from __future__ import annotations
import logging
import math
from typing import TYPE_CHECKING

from src.models.aci_constants import (
    LAMBDA_NWC, VC_COEFF, T_TH_COEFF, T_CR_COEFF, CROSS_SECTION_COEFF,
    TORSION_STRESS_COEFF, AO_FACTOR, AL_MIN_COEFF, PHI_TORSION
)
from src.models.units import kNm_to_Nmm, kN_to_N, cm_to_mm, mm2_to_cm2, Nmm_to_kNm

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


def _make_default_results(Tu: float) -> dict:
    """Create a default results dict with all expected keys."""
    return {
        "Tu": Tu, "T_th": 0.0, "phi_T_th": 0.0, "T_cr": 0.0, "phi_T_cr": 0.0,
        "status": "OK",
        "At_s_req": 0.0, "At_s_req_cm2_m": 0.0, "Al_req": 0.0,
        "check_cross_section": "OK", "action": ""
    }


def calculate_torsion(section: BeamSection, Tu: float, Vu: float) -> dict:
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

    Tu_Nmm = kNm_to_Nmm(Tu)
    Vu_N = kN_to_N(Vu)
    fc = section.fc
    fy = section.fy

    # Section properties
    sp = _compute_section_properties(section)

    if sp["x1"] <= 0 or sp["y1"] <= 0:
        logger.error("Section too small for torsion cover: x1=%.1f, y1=%.1f", sp["x1"], sp["y1"])
        results = _make_default_results(Tu)
        results["status"] = "Error: Section too small for defined cover to calculate Aoh."
        results["check_cross_section"] = "N/A"
        results["action"] = "Increase section or reduce cover"
        return results

    # Threshold and cracking torsion
    torsion_factor = LAMBDA_NWC * math.sqrt(fc) * (sp["Acp"] ** 2 / sp["Pcp"])
    T_th = T_TH_COEFF * torsion_factor
    T_cr = T_CR_COEFF * torsion_factor

    results = _make_default_results(Tu)
    results["T_th"] = Nmm_to_kNm(T_th)
    results["phi_T_th"] = Nmm_to_kNm(PHI_TORSION * T_th)
    results["T_cr"] = Nmm_to_kNm(T_cr)
    results["phi_T_cr"] = Nmm_to_kNm(PHI_TORSION * T_cr)

    # 1. Neglect torsion check
    if Tu_Nmm < PHI_TORSION * T_th:
        results["status"] = "Torsion Neglectable (Tu < phi * T_th)"
        results["action"] = "No Torsion Design Needed"
        return results

    # 2. Cross-section adequacy check
    d_mm = cm_to_mm(section.d)
    Vc = VC_COEFF * LAMBDA_NWC * math.sqrt(fc) * sp["b_mm"] * d_mm

    adequate, check_msg = _check_cross_section(
        Vu_N, Tu_Nmm, sp["b_mm"], d_mm, fc, sp["Ph"], sp["Aoh"], Vc
    )
    results["check_cross_section"] = check_msg

    if not adequate:
        logger.warning("Cross-section inadequate: %s", check_msg)
        results["status"] = "Error: Cross-Section Too Small for Torsion+Shear!"
        return results

    # 3. Transverse reinforcement At/s
    At_s_req = _compute_transverse_reinf(Tu_Nmm, sp["Aoh"], fy)
    results["At_s_req"] = At_s_req  # mm2/mm
    results["At_s_req_cm2_m"] = At_s_req * 10  # cm2/m

    # 4. Longitudinal reinforcement Al
    Al_final = _compute_longitudinal_reinf(At_s_req, sp["Ph"], fy, fc, sp["Acp"])
    results["Al_req"] = mm2_to_cm2(Al_final)  # cm2

    results["status"] = "Torsion Reinforcement Required"
    results["action"] = "Provide Closed Stirrups + Longitudinal Bars"

    return results
