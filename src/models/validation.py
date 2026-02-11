from __future__ import annotations

from typing import TYPE_CHECKING

from src.models.result_types import TraceCheck

if TYPE_CHECKING:
    from src.models.section import BeamSection


def validate_section_geometry(section: BeamSection) -> list[str]:
    """Return geometry validation errors. Empty list means valid."""
    errors: list[str] = []
    if section.b <= 0 or section.h <= 0:
        errors.append("Invalid section dimensions: width/height must be positive.")
    if section.cover <= 0:
        errors.append("Invalid cover: cover must be positive.")
    if section.d <= 0:
        errors.append("Invalid effective depth: d must be positive.")
    if section.cover >= min(section.b, section.h) / 2:
        errors.append("Cover is too large relative to section dimensions.")
    return errors


def normalize_load_with_policy(
    value: float,
    load_name: str,
    policy: str = "abs_with_warning",
) -> tuple[float, TraceCheck | None]:
    """
    Normalize load values and provide an optional trace warning.

    Policies:
    - abs_with_warning: take absolute value and emit warning if input was negative
    - reject_negative: raise ValueError for negative inputs
    """
    if value >= 0:
        return value, None

    if policy == "reject_negative":
        raise ValueError(f"{load_name} must be non-negative, got {value}.")

    normalized = abs(value)
    trace = TraceCheck(
        code_ref="Input Policy",
        formula_id=f"{load_name}_SIGN_NORMALIZATION",
        inputs={"raw_input": value},
        value=normalized,
        units="same_as_input",
        status="warning",
        note=f"{load_name} was negative and converted to magnitude by policy.",
    )
    return normalized, trace
