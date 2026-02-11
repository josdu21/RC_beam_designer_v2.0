from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from src.models.aci_constants import (
    AV_MIN_COEFF_1,
    AV_MIN_COEFF_2,
    LAMBDA_NWC,
    PHI_SHEAR,
    S_MAX_HEAVY,
    S_MAX_NORMAL,
    VC_COEFF,
    VS_HALF_COEFF,
    VS_MAX_COEFF,
)
from src.models.result_types import ShearResult, TraceCheck
from src.models.units import N_to_kN, cm_to_mm, kN_to_N, mm2_to_cm2, mm_to_cm
from src.models.validation import normalize_load_with_policy, validate_section_geometry

if TYPE_CHECKING:
    from src.models.section import BeamSection

logger = logging.getLogger(__name__)


def _compute_Vc(fc: float, b_mm: float, d_mm: float) -> float:
    """Concrete shear capacity Vc (simplified method)."""
    return VC_COEFF * LAMBDA_NWC * math.sqrt(fc) * b_mm * d_mm


def _compute_stirrup_area(stirrup_diameter_cm: float, n_legs: int) -> tuple[float, float]:
    """Compute stirrup bar area and total area for given legs."""
    d_mm = cm_to_mm(stirrup_diameter_cm)
    Av_bar = math.pi * (d_mm / 2) ** 2
    Av = n_legs * Av_bar
    return Av_bar, Av


def _compute_spacing(Av: float, fy: float, d_mm: float, Vs_req: float,
                     fc: float, b_mm: float) -> tuple[float, float]:
    """Compute required spacing and max spacing limit."""
    # Calculate spacing from Vs
    if Vs_req <= 0:
        s_calc = 9999.0  # Min reinforcement governs
    else:
        s_calc = (Av * fy * d_mm) / Vs_req

    # Max spacing limits (ACI 318 Table 9.7.6.2.2)
    if Vs_req <= VS_HALF_COEFF * math.sqrt(fc) * b_mm * d_mm:
        s_max_limit = min(d_mm / 2, S_MAX_NORMAL)
    else:
        s_max_limit = min(d_mm / 4, S_MAX_HEAVY)

    # Min shear reinforcement spacing limits
    s_min_1 = (Av * fy) / (AV_MIN_COEFF_1 * math.sqrt(fc) * b_mm)
    s_min_2 = (Av * fy) / (AV_MIN_COEFF_2 * b_mm)
    s_max_min_reinf = min(s_min_1, s_min_2)

    s_final = min(s_calc, s_max_limit, s_max_min_reinf)
    return s_final, s_max_limit


def calculate_shear(section: BeamSection, Vu: float, n_legs: int = 2,
                    stirrup_diameter: float = 0.95) -> ShearResult:
    """
    Calculate shear reinforcement (stirrups) per ACI 318-19 Simplified Method.

    Args:
        section: The beam section object.
        Vu: Ultimate Shear Force (kN).
        n_legs: Number of legs for stirrups (usually 2).
        stirrup_diameter: Diameter of stirrup bar (cm).

    Returns:
        dict with keys: Vc, phi_Vc, Vs_req, s_req, s_max, status, Av, Av_bar_cm2
    """
    logger.info("Shear calc: Vu=%.2f kN, b=%.1f d=%.1f", Vu, section.b, section.d)

    errors = validate_section_geometry(section)
    if errors:
        return ShearResult(
            status=f"Error: {' | '.join(errors)}",
            status_code="error",
        )

    Vu_norm, input_trace = normalize_load_with_policy(Vu, "Vu")
    trace: list[TraceCheck] = []
    if input_trace:
        trace.append(input_trace)

    Vu_N = kN_to_N(Vu_norm)
    b_mm = cm_to_mm(section.b)
    d_mm = cm_to_mm(section.d)
    fc = section.fc
    fy = section.fy

    Vc = _compute_Vc(fc, b_mm, d_mm)
    phi_Vc = PHI_SHEAR * Vc
    trace.append(
        TraceCheck(
            code_ref="ACI 318-19 Section 22.5",
            formula_id="Vc_simplified",
            inputs={"fc_MPa": fc, "bw_mm": b_mm, "d_mm": d_mm},
            value=Vc,
            units="N",
            status="ok",
        )
    )

    Av_bar, Av = _compute_stirrup_area(stirrup_diameter, n_legs)

    # No stirrups needed
    if Vu_N <= 0.5 * phi_Vc:
        trace.append(
            TraceCheck(
                code_ref="ACI 318-19 Section 9.6",
                formula_id="Vu_threshold_no_stirrups",
                inputs={"Vu_N": Vu_N, "phiVc_N": phi_Vc},
                value=Vu_N / max(phi_Vc, 1e-9),
                units="ratio",
                status="ok",
            )
        )
        return ShearResult(
            Vc=N_to_kN(Vc),
            phi_Vc=N_to_kN(phi_Vc),
            Vs_req=0,
            s_req=None,
            s_max=mm_to_cm(d_mm / 2),
            status="No Shear Reinforcement Required (Vu < 0.5 * phi * Vc)",
            status_code="ok",
            Av=Av,
            Av_bar_cm2=mm2_to_cm2(Av_bar),
            trace=trace,
        )

    # Required Vs
    Vs_req = (Vu_N / PHI_SHEAR) - Vc

    # Check max Vs
    Vs_max = VS_MAX_COEFF * math.sqrt(fc) * b_mm * d_mm
    trace.append(
        TraceCheck(
            code_ref="ACI 318-19 Section 22.5",
            formula_id="Vs_max",
            inputs={"fc_MPa": fc, "bw_mm": b_mm, "d_mm": d_mm},
            value=Vs_max,
            units="N",
            status="ok",
        )
    )
    if Vs_req > Vs_max:
        logger.warning("Section too small for shear: Vs_req=%.0f > Vs_max=%.0f", Vs_req, Vs_max)
        trace.append(
            TraceCheck(
                code_ref="ACI 318-19 Section 22.5",
                formula_id="Vs_req_gt_Vs_max",
                inputs={"Vs_req_N": Vs_req, "Vs_max_N": Vs_max},
                value=Vs_req,
                units="N",
                status="error",
            )
        )
        return ShearResult(
            Vc=N_to_kN(Vc),
            phi_Vc=N_to_kN(phi_Vc),
            Vs_req=N_to_kN(Vs_req),
            s_req=None,
            s_max=None,
            status="Error: Section Dimensions too small for Shear (Vs > Vs_max). Increase Dimensions.",
            status_code="error",
            Av=Av,
            Av_bar_cm2=mm2_to_cm2(Av_bar),
            trace=trace,
        )

    s_final, s_max_limit = _compute_spacing(Av, fy, d_mm, Vs_req, fc, b_mm)

    trace.append(
        TraceCheck(
            code_ref="ACI 318-19 Table 9.7.6.2.2",
            formula_id="stirrup_spacing",
            inputs={"Av_mm2": Av, "fy_MPa": fy, "d_mm": d_mm, "Vs_req_N": Vs_req},
            value=s_final,
            units="mm",
            status="ok",
        )
    )
    return ShearResult(
        Vc=N_to_kN(Vc),
        phi_Vc=N_to_kN(phi_Vc),
        Vs_req=N_to_kN(max(0, Vs_req)),
        s_req=mm_to_cm(s_final),
        s_max=mm_to_cm(s_max_limit),
        status="Add Stirrups" if Vs_req > 0 else "Minimum Stirrups Required",
        status_code="ok",
        Av=Av,
        Av_bar_cm2=mm2_to_cm2(Av_bar),
        trace=trace,
    )
