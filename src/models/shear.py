from __future__ import annotations
import logging
import math
from typing import TYPE_CHECKING

from src.models.aci_constants import (
    LAMBDA_NWC, VC_COEFF, VS_MAX_COEFF, VS_HALF_COEFF,
    AV_MIN_COEFF_1, AV_MIN_COEFF_2, PHI_SHEAR, S_MAX_NORMAL, S_MAX_HEAVY
)
from src.models.units import kN_to_N, cm_to_mm, N_to_kN, mm_to_cm, mm2_to_cm2

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
                    stirrup_diameter: float = 0.95) -> dict:
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

    Vu_N = kN_to_N(Vu)
    b_mm = cm_to_mm(section.b)
    d_mm = cm_to_mm(section.d)
    fc = section.fc
    fy = section.fy

    Vc = _compute_Vc(fc, b_mm, d_mm)
    phi_Vc = PHI_SHEAR * Vc

    Av_bar, Av = _compute_stirrup_area(stirrup_diameter, n_legs)

    # No stirrups needed
    if Vu_N <= 0.5 * phi_Vc:
        return {
            "Vc": N_to_kN(Vc), "phi_Vc": N_to_kN(phi_Vc),
            "Vs_req": 0, "s_req": None,
            "s_max": mm_to_cm(d_mm / 2),
            "status": "No Shear Reinforcement Required (Vu < 0.5 * phi * Vc)",
            "Av": Av, "Av_bar_cm2": mm2_to_cm2(Av_bar)
        }

    # Required Vs
    Vs_req = (Vu_N / PHI_SHEAR) - Vc

    # Check max Vs
    Vs_max = VS_MAX_COEFF * math.sqrt(fc) * b_mm * d_mm
    if Vs_req > Vs_max:
        logger.warning("Section too small for shear: Vs_req=%.0f > Vs_max=%.0f", Vs_req, Vs_max)
        return {
            "Vc": N_to_kN(Vc), "phi_Vc": N_to_kN(phi_Vc),
            "Vs_req": N_to_kN(Vs_req),
            "s_req": None, "s_max": None,
            "status": "Error: Section Dimensions too small for Shear (Vs > Vs_max). Increase Dimensions.",
            "Av": Av, "Av_bar_cm2": mm2_to_cm2(Av_bar)
        }

    s_final, s_max_limit = _compute_spacing(Av, fy, d_mm, Vs_req, fc, b_mm)

    return {
        "Vc": N_to_kN(Vc), "phi_Vc": N_to_kN(phi_Vc),
        "Vs_req": N_to_kN(max(0, Vs_req)),
        "s_req": mm_to_cm(s_final),
        "s_max": mm_to_cm(s_max_limit),
        "status": "Add Stirrups" if Vs_req > 0 else "Minimum Stirrups Required",
        "Av": Av, "Av_bar_cm2": mm2_to_cm2(Av_bar)
    }
