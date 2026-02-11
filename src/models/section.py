from __future__ import annotations
from src.models.aci_constants import (
    BETA1_HIGH, BETA1_LOW, FC_BETA1_UPPER, FC_BETA1_LOWER
)


class BeamSection:
    def __init__(self, b: float, h: float, fc: float, fy: float, cover: float) -> None:
        """
        Initialize the BeamSection with material and geometric properties.

        Args:
            b: Width of the beam (cm)
            h: Total height of the beam (cm)
            fc: Concrete compressive strength (MPa)
            fy: Steel yield strength (MPa)
            cover: Concrete cover to centroid of reinforcement (cm)
        """
        # Validation
        if b <= 0 or h <= 0:
            raise ValueError(f"Width and height must be positive (b={b}, h={h})")
        if cover >= h:
            raise ValueError(f"Cover ({cover} cm) must be less than beam height ({h} cm)")
        if fc <= 0 or fy <= 0:
            raise ValueError(f"Material strengths must be positive (fc={fc}, fy={fy})")

        self.b = b
        self.h = h
        self.fc = fc
        self.fy = fy
        self.cover = cover
        self.d = h - cover

        # Beta1 calculation (ACI 318-19 Table 22.2.2.4.3)
        if fc <= FC_BETA1_UPPER:
            self.beta1 = BETA1_HIGH
        elif fc < FC_BETA1_LOWER:
            self.beta1 = BETA1_HIGH - 0.05 * (fc - FC_BETA1_UPPER) / 7
        else:
            self.beta1 = BETA1_LOW
