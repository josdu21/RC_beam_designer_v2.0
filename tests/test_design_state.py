from src.ui.design_state import get_design_snapshot, init_design_state, update_design_inputs


def test_design_state_snapshot_updates_consistently():
    session_state: dict[str, object] = {}
    init_design_state(session_state)
    update_design_inputs(session_state, mu_pos=150.0, vu=95.0, n_legs=4)
    snap = get_design_snapshot(session_state)

    assert snap.mu_pos == 150.0
    assert snap.vu == 95.0
    assert snap.n_legs == 4
