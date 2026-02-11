from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class DesignInputs:
    mu_pos: float = 100.0
    mu_neg: float = 0.0
    vu: float = 50.0
    tu: float = 15.0
    vu_torsion: float = 50.0
    n_legs: int = 2
    stirrup_bar: str = '#3 (3/8")'
    n_bars_torsion: int = 6

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
