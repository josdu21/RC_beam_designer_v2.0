from __future__ import annotations

from typing import Any

from src.models.design_inputs import DesignInputs


def init_design_state(session_state: dict[str, Any]) -> None:
    if "design_inputs" not in session_state:
        session_state["design_inputs"] = DesignInputs().to_dict()


def update_design_inputs(session_state: dict[str, Any], **kwargs: Any) -> None:
    init_design_state(session_state)
    session_state["design_inputs"].update(kwargs)


def get_design_snapshot(session_state: dict[str, Any]) -> DesignInputs:
    init_design_state(session_state)
    data = session_state["design_inputs"]
    return DesignInputs(
        mu_pos=float(data.get("mu_pos", 100.0)),
        mu_neg=float(data.get("mu_neg", 0.0)),
        vu=float(data.get("vu", 50.0)),
        tu=float(data.get("tu", 15.0)),
        vu_torsion=float(data.get("vu_torsion", float(data.get("vu", 50.0)))),
        n_legs=int(data.get("n_legs", 2)),
        stirrup_bar=str(data.get("stirrup_bar", '#3 (3/8")')),
        n_bars_torsion=int(data.get("n_bars_torsion", 6)),
    )
