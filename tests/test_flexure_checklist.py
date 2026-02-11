from src.models.flexure import calculate_flexure
from src.models.flexure_checklist import build_flexure_checklist, build_flexure_summary
from src.models.section import BeamSection


def test_low_moment_governs_min_steel():
    section = BeamSection(30, 50, 28, 420, 4)
    res = calculate_flexure(section, 0.0)
    summary = build_flexure_summary("Inferior (+)", res)
    checklist = build_flexure_checklist("Inferior (+)", res)

    assert abs(res.As_design - res.As_min) < 1e-9
    assert summary["criterio_gobernante"] == "Gobierna acero mínimo"
    assert checklist[0]["Estado"] == "cumple"


def test_moderate_moment_governs_by_demand():
    section = BeamSection(30, 50, 28, 420, 4)
    res = calculate_flexure(section, 150.0)
    summary = build_flexure_summary("Inferior (+)", res)

    assert res.As_design > res.As_min
    assert summary["criterio_gobernante"] == "Gobierna demanda por momento"
    assert summary["estado"] in {"cumple", "advertencia"}


def test_low_ductility_case_marks_warning():
    section = BeamSection(30, 50, 28, 420, 4)
    warning_case = None
    for mu in range(200, 1000, 10):
        candidate = calculate_flexure(section, float(mu))
        if candidate.status_code == "warning":
            warning_case = candidate
            break

    assert warning_case is not None
    checklist = build_flexure_checklist("Inferior (+)", warning_case)
    assert checklist[1]["Estado"] == "advertencia"


def test_overloaded_section_has_capacity_failure_item():
    section = BeamSection(30, 50, 28, 420, 4)
    res = calculate_flexure(section, 1000.0)
    checklist = build_flexure_checklist("Inferior (+)", res)

    assert res.status_code == "error"
    assert any(row["Formula"] == "phiMn_quadratic_discriminant" for row in checklist)
    assert any(row["Estado"] == "no cumple" for row in checklist)
