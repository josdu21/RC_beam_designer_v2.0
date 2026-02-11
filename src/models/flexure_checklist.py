from __future__ import annotations

from typing import Any


def _state_from_status_code(status_code: str) -> str:
    if status_code == "ok":
        return "cumple"
    if status_code == "warning":
        return "advertencia"
    if status_code == "error":
        return "no cumple"
    return "pendiente"


def _criterion_from_result(res: Any) -> str:
    if res.status_code == "error":
        return "Sección sobrecargada"
    if res.As_design <= res.As_min + 1e-9:
        return "Gobierna acero mínimo"
    return "Gobierna demanda por momento"


def build_flexure_summary(face_label: str, res: Any) -> dict[str, Any]:
    return {
        "cara": face_label,
        "estado": _state_from_status_code(res.status_code),
        "criterio_gobernante": _criterion_from_result(res),
        "ductilidad_alerta": "sí" if res.epsilon_t < 0.005 else "no",
        "As_calc_cm2": round(float(res.As_calc), 3),
        "As_min_cm2": round(float(res.As_min), 3),
        "As_design_cm2": round(float(res.As_design), 3),
        "rho": round(float(res.rho), 5),
        "phi": round(float(res.phi), 4),
        "epsilon_t": round(float(res.epsilon_t), 5),
    }


def build_flexure_checklist(face_label: str, res: Any) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    min_steel_state = "cumple" if res.As_design + 1e-9 >= res.As_min else "no cumple"
    rows.append(
        {
            "Cara": face_label,
            "Check": "Acero mínimo",
            "Code Ref": "ACI 318-19 Table 9.6.1.2",
            "Formula": "As_min",
            "Estado": min_steel_state,
            "Valor": f"As_design={res.As_design:.2f} cm2 | As_min={res.As_min:.2f} cm2",
            "Comentario": _criterion_from_result(res),
        }
    )

    if res.status_code == "error":
        ductility_state = "no cumple"
    elif res.epsilon_t < 0.004:
        ductility_state = "advertencia"
    elif res.epsilon_t < 0.005:
        ductility_state = "advertencia"
    else:
        ductility_state = "cumple"

    rows.append(
        {
            "Cara": face_label,
            "Check": "Ductilidad y factor phi",
            "Code Ref": "ACI 318-19 Section 21.2.2",
            "Formula": "phi_strain_classification",
            "Estado": ductility_state,
            "Valor": f"epsilon_t={res.epsilon_t:.5f} | phi={res.phi:.3f}",
            "Comentario": res.status,
        }
    )

    if res.status_code == "error":
        rows.append(
            {
                "Cara": face_label,
                "Check": "Capacidad de sección",
                "Code Ref": "ACI 318-19 Section 22.2",
                "Formula": "phiMn_quadratic_discriminant",
                "Estado": "no cumple",
                "Valor": "Falla de capacidad en flexión",
                "Comentario": "Sección sobrecargada para el momento aplicado.",
            }
        )

    return rows
