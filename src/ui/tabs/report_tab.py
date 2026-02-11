import json

import pandas as pd
import streamlit as st

from src.models.reporting import build_design_report
from src.ui.design_state import get_design_snapshot, init_design_state


def render(section):
    st.header("Reporte Resumen de Diseño")
    init_design_state(st.session_state)

    # Sync widget-only keys into central state (supports old navigation order)
    if "mu_pos" in st.session_state:
        st.session_state["design_inputs"]["mu_pos"] = st.session_state["mu_pos"]
    if "mu_neg" in st.session_state:
        st.session_state["design_inputs"]["mu_neg"] = st.session_state["mu_neg"]
    if "Vu" in st.session_state:
        st.session_state["design_inputs"]["vu"] = st.session_state["Vu"]
    if "Tu" in st.session_state:
        st.session_state["design_inputs"]["tu"] = st.session_state["Tu"]
    if "Vu_torsion" in st.session_state:
        st.session_state["design_inputs"]["vu_torsion"] = st.session_state["Vu_torsion"]
    if "n_legs" in st.session_state:
        st.session_state["design_inputs"]["n_legs"] = st.session_state["n_legs"]
    if "stirrup_bar" in st.session_state:
        st.session_state["design_inputs"]["stirrup_bar"] = st.session_state["stirrup_bar"]
    if "n_bars_torsion" in st.session_state:
        st.session_state["design_inputs"]["n_bars_torsion"] = st.session_state["n_bars_torsion"]

    snapshot = get_design_snapshot(st.session_state)
    bundle = build_design_report(section, snapshot)

    st.subheader("Cargas de Diseno")
    st.caption("Valores tomados del estado central de diseño para mantener consistencia entre pestañas.")

    lc1, lc2, lc3, lc4 = st.columns(4)
    lc1.metric("Mu+ [kNm]", f"{snapshot.mu_pos:.1f}")
    lc2.metric("Mu- [kNm]", f"{snapshot.mu_neg:.1f}")
    lc3.metric("Vu [kN]", f"{snapshot.vu:.1f}")
    lc4.metric("Tu [kNm]", f"{snapshot.tu:.1f}")

    st.divider()
    res_flex_pos = bundle.flexure_pos
    res_flex_neg = bundle.flexure_neg
    res_shear = bundle.shear_res
    res_tors = bundle.torsion_res
    dist = bundle.torsion_dist
    torsion_significant = "Required" in res_tors.status or dist.al_total > 0
    al_bottom = dist.al_bottom
    al_top = dist.al_top
    al_side = dist.al_side_each

    # ──────────────────────────────────────────────────────────────
    # 1. REFUERZO LONGITUDINAL
    # ──────────────────────────────────────────────────────────────
    st.subheader("1. Refuerzo Longitudinal")

    as_flex_bot = res_flex_pos.As_design
    as_flex_top = res_flex_neg.As_design

    if torsion_significant:
        st.markdown("**Combinacion Flexion + Torsion Longitudinal (ACI 318-19)**")

        # Combined table
        combined_data = {
            "Cara": ["Inferior", "Superior", "Lateral (c/u)"],
            "As Flexion (cm2)": [
                f"{as_flex_bot:.2f}",
                f"{as_flex_top:.2f}",
                "---"
            ],
            "Al Torsion (cm2)": [
                f"{al_bottom:.2f}",
                f"{al_top:.2f}",
                f"{al_side:.2f}"
            ],
            "TOTAL (cm2)": [
                f"{(as_flex_bot + al_bottom):.2f}",
                f"{(as_flex_top + al_top):.2f}",
                f"{al_side:.2f}"
            ],
        }
        st.table(pd.DataFrame(combined_data))

        # Summary metrics
        total_bot = as_flex_bot + al_bottom
        total_top = as_flex_top + al_top

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("As Total Inferior", f"{total_bot:.2f} cm2",
                   delta=f"+{al_bottom:.2f} por torsion" if al_bottom > 0 else None)
        mc2.metric("As Total Superior", f"{total_top:.2f} cm2",
                   delta=f"+{al_top:.2f} por torsion" if al_top > 0 else None)
        mc3.metric("As Lateral (c/lado)", f"{al_side:.2f} cm2")

        st.caption("Nota: El acero por torsion longitudinal se suma al acero por flexion en cada cara. "
                   "El acero lateral es adicional y se coloca en las caras del alma.")

    else:
        # No significant torsion - simple table
        long_data = {
            "Ubicacion": ["Inferior (Flexion +)", "Superior (Flexion -)"],
            "As Requerido (cm2)": [
                f"{as_flex_bot:.2f}",
                f"{as_flex_top:.2f}"
            ],
            "Comentarios": [
                res_flex_pos.status,
                res_flex_neg.status if snapshot.mu_neg > 0 else "Sin momento negativo"
            ]
        }
        st.table(pd.DataFrame(long_data))
        st.info("Torsión despreciable: no se requiere acero longitudinal adicional por torsión.")

    st.subheader("Checklist Flexión (resumen)")
    st.caption("Resumen por cara: estado, criterio gobernante y alerta de ductilidad.")
    flex_summary_df = pd.DataFrame(
        bundle.flexure_summary,
        columns=[
            "cara",
            "estado",
            "criterio_gobernante",
            "ductilidad_alerta",
            "As_min_cm2",
            "As_design_cm2",
            "phi",
            "epsilon_t",
        ],
    )
    st.table(flex_summary_df)

    # ──────────────────────────────────────────────────────────────
    # 2. REFUERZO TRANSVERSAL
    # ──────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("2. Refuerzo Transversal (Estribos)")

    st.write(f"**Cortante Vs:** {res_shear.Vs_req:.2f} kN")

    if "Neglectable" in res_tors.status:
        st.success("Torsión despreciable. Diseñar solo por cortante.")
        s_req = res_shear.s_req
        if s_req is not None:
            st.metric("Separacion Estribos (Cortante)", f"{s_req:.1f} cm")
        else:
            st.info(res_shear.status)
    elif "Error" in res_tors.status:
        st.error("Error en Torsión: " + res_tors.status)
    else:
        st.warning("Torsión significativa. Se requieren estribos cerrados.")

        col_res1, col_res2 = st.columns(2)
        s_req = res_shear.s_req
        if s_req is not None:
            col_res1.metric("Estribos por Cortante", f"s = {s_req:.1f} cm")
        else:
            col_res1.info(res_shear.status)
        col_res2.metric("Refuerzo Torsion (At/s)", f"{res_tors.At_s_req_cm2_m:.2f} cm2/m")

    st.divider()
    st.subheader("3. Criterios ACI Gobernantes")
    st.table(pd.DataFrame(bundle.governing_criteria))

    st.subheader("4. Advertencias Activas")
    if bundle.warnings:
        for warning in bundle.warnings:
            st.warning(warning)
    else:
        st.success("Sin advertencias activas para el conjunto actual de diseño.")

    st.divider()
    st.subheader("5. Exportación")
    payload = bundle.export_payload()
    criteria_df = pd.DataFrame(bundle.governing_criteria)
    csv_data = criteria_df.to_csv(index=False).encode("utf-8")

    cexp1, cexp2 = st.columns(2)
    cexp1.download_button(
        label="Descargar criterios (CSV)",
        data=csv_data,
        file_name="rc_beam_governing_criteria.csv",
        mime="text/csv",
    )
    cexp2.download_button(
        label="Descargar reporte técnico (JSON)",
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name="rc_beam_report_payload.json",
        mime="application/json",
    )
