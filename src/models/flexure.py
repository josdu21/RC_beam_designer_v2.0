from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from src.models.aci_constants import (
    EPSILON_CU,
    EPSILON_T_COMPRESSION,
    EPSILON_T_TENSION,
    MIN_RHO_COEFF_1,
    MIN_RHO_COEFF_2,
    PHI_COMPRESSION,
    PHI_TENSION,
    WHITNEY_COEFF,
)
from src.models.result_types import FlexureResult, TraceCheck
from src.models.units import cm_to_mm, kNm_to_Nmm, mm2_to_cm2, mm_to_cm
from src.models.validation import normalize_load_with_policy, validate_section_geometry

if TYPE_CHECKING:
    from src.models.section import BeamSection

logger = logging.getLogger(__name__)


def _compute_As_min(fc: float, fy: float, b_mm: float, d_mm: float) -> float:
    """Minimum reinforcement per ACI 318 Table 9.6.1.2."""
    min_rho_1 = MIN_RHO_COEFF_1 * math.sqrt(fc) / fy
    min_rho_2 = MIN_RHO_COEFF_2 / fy
    return max(min_rho_1, min_rho_2) * b_mm * d_mm


def _compute_phi(epsilon_t: float) -> float:
    """Compute strength reduction factor based on net tensile strain."""
    if epsilon_t >= EPSILON_T_TENSION:
        return PHI_TENSION
    elif epsilon_t <= EPSILON_T_COMPRESSION:
        return PHI_COMPRESSION
    else:
        return PHI_COMPRESSION + 0.25 * (epsilon_t - EPSILON_T_COMPRESSION) / (EPSILON_T_TENSION - EPSILON_T_COMPRESSION)


def _iterate_phi(section: BeamSection, Mu_Nmm: float, b_mm: float, d_mm: float,
                 fc: float, fy: float) -> dict:
    """Iterative phi-convergence loop for flexural design."""
    phi = PHI_TENSION

    # Quadratic coefficients: (fy^2 / (2*0.85*fc*b)) * As^2 - (fy*d) * As + Mu/phi = 0
    term_A = (fy ** 2) / (2 * WHITNEY_COEFF * fc * b_mm)
    term_B = -fy * d_mm

    As_req = 0.0
    a = 0.0
    c = 0.0
    epsilon_t = 1.0

    for i in range(10):
        term_C = Mu_Nmm / phi
        delta = term_B ** 2 - 4 * term_A * term_C

        if delta < 0:
            logger.warning("Section overloaded: discriminant < 0 at phi=%.4f", phi)
            return {"error": True, "phi": phi}

        As_req = (-term_B - math.sqrt(delta)) / (2 * term_A)
        a = As_req * fy / (WHITNEY_COEFF * fc * b_mm)
        c = a / section.beta1

        if c <= 0:
            epsilon_t = 1.0
            phi = PHI_TENSION
            break

        epsilon_t = EPSILON_CU * (d_mm - c) / c
        new_phi = _compute_phi(epsilon_t)

        if abs(new_phi - phi) < 0.001:
            phi = new_phi
            break
        phi = new_phi
        logger.debug("Iteration %d: phi=%.4f, epsilon_t=%.5f", i, phi, epsilon_t)

    return {
        "error": False, "As_req": As_req, "a": a, "c": c,
        "epsilon_t": epsilon_t, "phi": phi
    }


def calculate_flexure(section: BeamSection, Mu: float) -> FlexureResult:
    """
    Calculate required reinforcement for a given ultimate moment.

    Args:
        section: The beam section object.
        Mu: Ultimate Moment (kNm).

    Returns:
        dict with keys: As_calc, As_min, As_design, rho, phi, epsilon_t, status, c, a
    """
    logger.info("Flexure calc: Mu=%.2f kNm, b=%.1f h=%.1f", Mu, section.b, section.h)

    errors = validate_section_geometry(section)
    if errors:
        return FlexureResult(
            status=f"Error: {' | '.join(errors)}",
            status_code="error",
            phi=PHI_COMPRESSION,
        )

    Mu_norm, input_trace = normalize_load_with_policy(Mu, "Mu")
    trace: list[TraceCheck] = []
    if input_trace:
        trace.append(input_trace)

    Mu_Nmm = kNm_to_Nmm(Mu_norm)
    b_mm = cm_to_mm(section.b)
    d_mm = cm_to_mm(section.d)
    fc = section.fc
    fy = section.fy

    As_min = _compute_As_min(fc, fy, b_mm, d_mm)
    trace.append(
        TraceCheck(
            code_ref="ACI 318-19 Table 9.6.1.2",
            formula_id="As_min",
            inputs={"fc_MPa": fc, "fy_MPa": fy, "b_mm": b_mm, "d_mm": d_mm},
            value=As_min,
            units="mm2",
            status="ok",
        )
    )

    # Negligible moment
    if Mu_Nmm < 1e-6:
        return FlexureResult(
            As_calc=0.0,
            As_min=mm2_to_cm2(As_min),
            As_design=mm2_to_cm2(As_min),
            rho=0.0,
            phi=PHI_TENSION,
            epsilon_t=1.0,
            status="OK (Min Steel)",
            status_code="ok",
            c=0.0,
            a=0.0,
            trace=trace,
        )

    result = _iterate_phi(section, Mu_Nmm, b_mm, d_mm, fc, fy)

    if result["error"]:
        trace.append(
            TraceCheck(
                code_ref="ACI 318-19 Section 22.2",
                formula_id="phiMn_quadratic_discriminant",
                inputs={"Mu_Nmm": Mu_Nmm},
                value=result["phi"],
                units="phi",
                status="error",
                note="Negative discriminant in flexure quadratic.",
            )
        )
        return FlexureResult(
            As_calc=0.0,
            As_min=mm2_to_cm2(As_min),
            As_design=0.0,
            rho=0.0,
            phi=result["phi"],
            epsilon_t=0.0,
            status="Error: Section Overloaded (Compression Failure)",
            status_code="error",
            c=0.0,
            a=0.0,
            trace=trace,
        )

    As_req = result["As_req"]
    epsilon_t = result["epsilon_t"]
    phi = result["phi"]
    a = result["a"]
    c = result["c"]

    status = "OK"
    status_code = "ok"
    if epsilon_t < 0.004:
        status = "Warning: Low Ductility (epsilon_t < 0.004)"
        status_code = "warning"
        logger.warning("Low ductility: epsilon_t=%.5f", epsilon_t)
    elif epsilon_t < EPSILON_T_TENSION:
        status = "Transition Zone (epsilon_t < 0.005)"
        status_code = "warning"

    trace.append(
        TraceCheck(
            code_ref="ACI 318-19 Section 21.2.2",
            formula_id="phi_strain_classification",
            inputs={"epsilon_t": epsilon_t},
            value=phi,
            units="phi",
            status=status_code,
        )
    )

    return FlexureResult(
        As_calc=mm2_to_cm2(As_req),
        As_min=mm2_to_cm2(As_min),
        As_design=mm2_to_cm2(max(As_req, As_min)),
        rho=As_req / (b_mm * d_mm),
        phi=phi,
        epsilon_t=epsilon_t,
        status=status,
        status_code=status_code,
        c=mm_to_cm(c),
        a=mm_to_cm(a),
        trace=trace,
    )
