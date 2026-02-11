from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from src.models.aci_constants import (
    AL_MIN_COEFF,
    AO_FACTOR,
    CROSS_SECTION_COEFF,
    LAMBDA_NWC,
    PHI_TORSION,
    T_CR_COEFF,
    T_TH_COEFF,
    TORSION_STRESS_COEFF,
    VC_COEFF,
)
from src.models.result_types import TorsionResult, TraceCheck
from src.models.units import Nmm_to_kNm, cm_to_mm, kN_to_N, kNm_to_Nmm, mm2_to_cm2
from src.models.validation import normalize_load_with_policy, validate_section_geometry

if TYPE_CHECKING:
    from src.models.section import BeamSection

logger = logging.getLogger(__name__)


def _compute_section_properties(section: BeamSection) -> dict:
    """Compute torsion section properties (Acp, Pcp, Aoh, Ph)."""
    b_mm = cm_to_mm(section.b)
    h_mm = cm_to_mm(section.h)
    cover_mm = cm_to_mm(section.cover)

    Acp = b_mm * h_mm
    Pcp = 2 * (b_mm + h_mm)

    x1 = b_mm - 2 * cover_mm
    y1 = h_mm - 2 * cover_mm

    return {
        "b_mm": b_mm, "h_mm": h_mm, "Acp": Acp, "Pcp": Pcp,
        "x1": x1, "y1": y1,
        "Aoh": x1 * y1 if (x1 > 0 and y1 > 0) else 0,
        "Ph": 2 * (x1 + y1) if (x1 > 0 and y1 > 0) else 0
    }


def _check_cross_section(Vu_N: float, Tu_Nmm: float, b_mm: float, d_mm: float,
                         fc: float, Ph: float, Aoh: float, Vc: float) -> tuple[bool, str]:
    """Check cross-sectional adequacy per ACI 318-19 22.7.7.1."""
    bw_d = b_mm * d_mm
    lhs_v = Vu_N / bw_d
    lhs_t = (Tu_Nmm * Ph) / (TORSION_STRESS_COEFF * Aoh ** 2)
    lhs = math.sqrt(lhs_v ** 2 + lhs_t ** 2)

    rhs_max = PHI_TORSION * ((Vc / bw_d) + CROSS_SECTION_COEFF * math.sqrt(fc))

    if lhs > rhs_max:
        return False, f"Combined Shear Stress {lhs:.2f} > Limit {rhs_max:.2f} MPa"
    return True, f"OK ({lhs:.2f} <= {rhs_max:.2f} MPa)"


def _compute_transverse_reinf(Tu_Nmm: float, Aoh: float, fy: float) -> float:
    """Compute At/s (transverse torsion reinforcement per unit length)."""
    Tn = Tu_Nmm / PHI_TORSION
    Ao = AO_FACTOR * Aoh
    cot_theta = 1.0  # cot(45 degrees)
    return Tn / (2 * Ao * fy * cot_theta)  # mm2/mm per leg


def _compute_longitudinal_reinf(At_s_req: float, Ph: float, fy: float,
                                fc: float, Acp: float) -> float:
    """Compute Al (longitudinal torsion reinforcement)."""
    fyt = fy  # Same yield for transverse and longitudinal
    cot_theta = 1.0

    Al_req = At_s_req * Ph * (fyt / fy) * (cot_theta ** 2)

    # ACI 318-19 Eq 9.6.4.3(a): Al,min = (5*sqrt(f'c)*Acp/fy) - (At/s)*Ph*(fyt/fy)
    # Coefficient 5 is for psi units; for MPa: 5/12 = 0.42
    term1 = (AL_MIN_COEFF * math.sqrt(fc) * Acp) / fy
    Al_min = term1 - (At_s_req * Ph * (fyt / fy))

    return max(Al_req, Al_min)


def _make_default_results(Tu: float, trace: list[TraceCheck] | None = None) -> TorsionResult:
    """Create a default result object with all expected keys."""
    return TorsionResult(
        Tu=Tu,
        T_th=0.0,
        phi_T_th=0.0,
        T_cr=0.0,
        phi_T_cr=0.0,
        status="OK",
        status_code="ok",
        At_s_req=0.0,
        At_s_req_cm2_m=0.0,
        Al_req=0.0,
        check_cross_section="OK",
        action="",
        trace=trace or [],
    )


def calculate_torsion(section: BeamSection, Tu: float, Vu: float) -> TorsionResult:
    """
    Check torsion threshold and calculate reinforcement if required (ACI 318-19).

    Args:
        section: The beam section object.
        Tu: Ultimate Torsion (kNm).
        Vu: Ultimate Shear Force (kN).

    Returns:
        dict with keys: Tu, T_th, phi_T_th, T_cr, phi_T_cr, status,
                        At_s_req, At_s_req_cm2_m, Al_req, check_cross_section, action
    """
    logger.info("Torsion calc: Tu=%.2f kNm, Vu=%.2f kN", Tu, Vu)

    errors = validate_section_geometry(section)
    if errors:
        return TorsionResult(
            Tu=Tu,
            status=f"Error: {' | '.join(errors)}",
            status_code="error",
            check_cross_section="N/A",
        )

    Tu_norm, tu_trace = normalize_load_with_policy(Tu, "Tu")
    Vu_norm, vu_trace = normalize_load_with_policy(Vu, "Vu")
    trace: list[TraceCheck] = []
    if tu_trace:
        trace.append(tu_trace)
    if vu_trace:
        trace.append(vu_trace)

    Tu_Nmm = kNm_to_Nmm(Tu_norm)
    Vu_N = kN_to_N(Vu_norm)
    fc = section.fc
    fy = section.fy

    # Section properties
    sp = _compute_section_properties(section)

    if sp["x1"] <= 0 or sp["y1"] <= 0:
        logger.error("Section too small for torsion cover: x1=%.1f, y1=%.1f", sp["x1"], sp["y1"])
        results = _make_default_results(Tu_norm, trace)
        results.status = "Error: Section too small for defined cover to calculate Aoh."
        results.status_code = "error"
        results.check_cross_section = "N/A"
        results.action = "Increase section or reduce cover"
        trace.append(
            TraceCheck(
                code_ref="ACI 318-19 Section 22.7",
                formula_id="Aoh_validity",
                inputs={"x1_mm": sp["x1"], "y1_mm": sp["y1"]},
                value=0.0,
                units="mm2",
                status="error",
            )
        )
        return results

    # Threshold and cracking torsion
    torsion_factor = LAMBDA_NWC * math.sqrt(fc) * (sp["Acp"] ** 2 / sp["Pcp"])
    T_th = T_TH_COEFF * torsion_factor
    T_cr = T_CR_COEFF * torsion_factor

    results = _make_default_results(Tu_norm, trace)
    results.T_th = Nmm_to_kNm(T_th)
    results.phi_T_th = Nmm_to_kNm(PHI_TORSION * T_th)
    results.T_cr = Nmm_to_kNm(T_cr)
    results.phi_T_cr = Nmm_to_kNm(PHI_TORSION * T_cr)
    trace.append(
        TraceCheck(
            code_ref="ACI 318-19 Section 22.7",
            formula_id="T_th",
            inputs={"fc_MPa": fc, "Acp_mm2": sp["Acp"], "Pcp_mm": sp["Pcp"]},
            value=T_th,
            units="Nmm",
            status="ok",
        )
    )

    # 1. Neglect torsion check
    if Tu_Nmm < PHI_TORSION * T_th:
        results.status = "Torsion Neglectable (Tu < phi * T_th)"
        results.status_code = "ok"
        results.action = "No Torsion Design Needed"
        return results

    # 2. Cross-section adequacy check
    d_mm = cm_to_mm(section.d)
    Vc = VC_COEFF * LAMBDA_NWC * math.sqrt(fc) * sp["b_mm"] * d_mm

    adequate, check_msg = _check_cross_section(
        Vu_N, Tu_Nmm, sp["b_mm"], d_mm, fc, sp["Ph"], sp["Aoh"], Vc
    )
    results.check_cross_section = check_msg
    trace.append(
        TraceCheck(
            code_ref="ACI 318-19 22.7.7.1",
            formula_id="combined_shear_torsion_stress",
            inputs={"Vu_N": Vu_N, "Tu_Nmm": Tu_Nmm},
            value=1.0 if adequate else 0.0,
            units="pass_fail",
            status="ok" if adequate else "error",
            note=check_msg,
        )
    )

    if not adequate:
        logger.warning("Cross-section inadequate: %s", check_msg)
        results.status = "Error: Cross-Section Too Small for Torsion+Shear!"
        results.status_code = "error"
        return results

    # 3. Transverse reinforcement At/s
    At_s_req = _compute_transverse_reinf(Tu_Nmm, sp["Aoh"], fy)
    results.At_s_req = At_s_req  # mm2/mm
    results.At_s_req_cm2_m = At_s_req * 10  # cm2/m
    trace.append(
        TraceCheck(
            code_ref="ACI 318-19 Section 22.7",
            formula_id="At_over_s",
            inputs={"Tu_Nmm": Tu_Nmm, "Aoh_mm2": sp["Aoh"], "fy_MPa": fy},
            value=At_s_req,
            units="mm2/mm",
            status="ok",
        )
    )

    # 4. Longitudinal reinforcement Al
    Al_final = _compute_longitudinal_reinf(At_s_req, sp["Ph"], fy, fc, sp["Acp"])
    results.Al_req = mm2_to_cm2(Al_final)  # cm2
    trace.append(
        TraceCheck(
            code_ref="ACI 318-19 Eq 9.6.4.3(a)",
            formula_id="Al_min_and_required",
            inputs={"At_s_mm2_per_mm": At_s_req, "Ph_mm": sp["Ph"], "Acp_mm2": sp["Acp"]},
            value=Al_final,
            units="mm2",
            status="ok",
        )
    )

    results.status = "Torsion Reinforcement Required"
    results.status_code = "warning"
    results.action = "Provide Closed Stirrups + Longitudinal Bars"

    return results
