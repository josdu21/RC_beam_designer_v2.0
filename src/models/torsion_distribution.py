from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TorsionLongitudinalDistribution:
    al_total: float
    n_bars: int
    al_per_bar: float
    n_bottom: int
    n_top: int
    n_side_each: int
    al_bottom: float
    al_top: float
    al_side_each: float

    def to_dict(self) -> dict[str, float | int]:
        return {
            "al_total": self.al_total,
            "n_bars": self.n_bars,
            "al_per_bar": self.al_per_bar,
            "n_bottom": self.n_bottom,
            "n_top": self.n_top,
            "n_side_each": self.n_side_each,
            "al_bottom": self.al_bottom,
            "al_top": self.al_top,
            "al_side_each": self.al_side_each,
        }


def distribute_torsion_longitudinal_reinf(
    al_total: float,
    b_cm: float,
    h_cm: float,
    cover_cm: float,
    n_bars: int = 6,
) -> TorsionLongitudinalDistribution:
    """Distribute total torsion longitudinal area around stirrup perimeter."""
    if al_total <= 0:
        return TorsionLongitudinalDistribution(0.0, n_bars, 0.0, 0, 0, 0, 0.0, 0.0, 0.0)

    n_bars = max(4, int(n_bars))
    b_inner = max(b_cm - 2 * cover_cm, 0.0)
    h_inner = max(h_cm - 2 * cover_cm, 0.0)
    ph = max(2 * (b_inner + h_inner), 1e-9)

    n_bottom = max(2, round(n_bars * b_inner / ph))
    n_top = max(2, round(n_bars * b_inner / ph))
    n_sides = n_bars - n_bottom - n_top
    if n_sides < 0:
        n_sides = 0
        n_bottom = n_bars // 2
        n_top = n_bars - n_bottom

    if n_sides % 2 != 0:
        n_bottom += 1
        n_sides -= 1
    n_side_each = max(0, n_sides // 2)

    al_per_bar = al_total / n_bars
    al_bottom = n_bottom * al_per_bar
    al_top = n_top * al_per_bar
    al_side_each = n_side_each * al_per_bar

    return TorsionLongitudinalDistribution(
        al_total=al_total,
        n_bars=n_bars,
        al_per_bar=al_per_bar,
        n_bottom=n_bottom,
        n_top=n_top,
        n_side_each=n_side_each,
        al_bottom=al_bottom,
        al_top=al_top,
        al_side_each=al_side_each,
    )
