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
    assert "flexure_summary" in payload
    assert "flexure_checklist" in payload
    assert len(payload["flexure_summary"]) == 2


def test_report_flexure_summary_consistency():
    section = BeamSection(30, 50, 28, 420, 4)
    design_inputs = DesignInputs(mu_pos=0, mu_neg=120, vu=80, tu=20, vu_torsion=80, n_bars_torsion=6)
    bundle = build_design_report(section, design_inputs)

    assert len(bundle.flexure_summary) == 2
    assert bundle.flexure_summary[0]["cara"] == "Inferior (+)"
    assert bundle.flexure_summary[1]["cara"] == "Superior (-)"


def test_report_deterministic_for_same_inputs():
    section = BeamSection(30, 50, 28, 420, 4)
    design_inputs = DesignInputs(mu_pos=120, mu_neg=0, vu=90, tu=10, vu_torsion=90, n_bars_torsion=6)

    p1 = build_design_report(section, design_inputs).export_payload()
    p2 = build_design_report(section, design_inputs).export_payload()
    assert p1 == p2
