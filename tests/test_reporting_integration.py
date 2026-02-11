from src.models.design_inputs import DesignInputs
from src.models.reporting import build_design_report
from src.models.section import BeamSection


def test_report_bundle_contains_governing_criteria_and_payload():
    section = BeamSection(30, 50, 28, 420, 4)
    design_inputs = DesignInputs(mu_pos=100, mu_neg=20, vu=80, tu=20, vu_torsion=80, n_bars_torsion=6)
    bundle = build_design_report(section, design_inputs)

    assert len(bundle.governing_criteria) == 4
    payload = bundle.export_payload()
    assert "flexure_pos" in payload
    assert "shear" in payload
    assert "torsion" in payload
    assert "warnings" in payload
    assert "trace" in payload["flexure_pos"]


def test_report_deterministic_for_same_inputs():
    section = BeamSection(30, 50, 28, 420, 4)
    design_inputs = DesignInputs(mu_pos=120, mu_neg=0, vu=90, tu=10, vu_torsion=90, n_bars_torsion=6)

    p1 = build_design_report(section, design_inputs).export_payload()
    p2 = build_design_report(section, design_inputs).export_payload()
    assert p1 == p2
