import streamlit as st
import pandas as pd

from src.models import flexure
from src.models.flexure_checklist import build_flexure_checklist, build_flexure_summary
from src.ui import plotting
from src.ui.design_state import get_design_snapshot, init_design_state, update_design_inputs


def _render_status_box(status_code: str, message: str) -> None:
    if status_code == "ok":
        st.success(message)
    elif status_code == "warning":
        st.warning(message)
    else:
        st.error(message)


def render(section):
    st.header("Diseño por Flexión (Momentos)")
    init_design_state(st.session_state)
    snapshot = get_design_snapshot(st.session_state)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⬇️ Refuerzo Inferior (+)")
        mu_pos = st.number_input("Momento Positivo (+Mu) [kNm]", 0.0, None, snapshot.mu_pos, 10.0, key="mu_pos")
    with col2:
        st.subheader("⬆️ Refuerzo Superior (-)")
        mu_neg = st.number_input("Momento Negativo (-Mu) [kNm]", 0.0, None, snapshot.mu_neg, 10.0, key="mu_neg")

    update_design_inputs(st.session_state, mu_pos=mu_pos, mu_neg=mu_neg)

    res_bot = flexure.calculate_flexure(section, mu_pos)
    res_top = flexure.calculate_flexure(section, mu_neg)

    # 2) Resultados rápidos por cara
    st.subheader("Resultados rápidos por cara")
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        st.write("Inferior (+)")
        _render_status_box(res_bot["status_code"], f"As diseño: {res_bot['As_design']:.2f} cm²")
        st.metric("As calculado", f"{res_bot['As_calc']:.2f} cm²")

    with c2:
        st.write("Superior (-)")
        if mu_neg > 0:
            _render_status_box(res_top["status_code"], f"As diseño: {res_top['As_design']:.2f} cm²")
            st.metric("As calculado", f"{res_top['As_calc']:.2f} cm²")
        else:
            st.info("Sin momento negativo, gobierna acero mínimo.")
            st.metric("As mínimo", f"{res_top['As_min']:.2f} cm²")

    with c3:
        st.write("Esquema")
        as_b = res_bot["As_design"] if mu_pos > 0 else 0
        as_t = res_top["As_design"] if mu_neg > 0 else 0
        fig = plotting.draw_beam_section_flexure(section.b, section.h, section.cover, as_b, as_t)
        st.pyplot(fig)

    # 3) Acero mínimo y control gobernante
    st.divider()
    st.subheader("Acero mínimo y control gobernante")
    summary_bot = build_flexure_summary("Inferior (+)", res_bot)
    summary_top = build_flexure_summary("Superior (-)", res_top)

    s1, s2 = st.columns(2)
    with s1:
        st.markdown("#### Cara inferior (+)")
        st.metric("As mínimo", f"{res_bot['As_min']:.2f} cm²")
        st.metric("As calculado", f"{res_bot['As_calc']:.2f} cm²")
        st.metric("As diseño", f"{res_bot['As_design']:.2f} cm²")
        st.caption(f"Controla: {summary_bot['criterio_gobernante']}")
        st.caption(
            f"rho={res_bot['rho']:.5f} | phi={res_bot['phi']:.3f} | epsilon_t={res_bot['epsilon_t']:.5f}"
        )

    with s2:
        st.markdown("#### Cara superior (-)")
        st.metric("As mínimo", f"{res_top['As_min']:.2f} cm²")
        st.metric("As calculado", f"{res_top['As_calc']:.2f} cm²")
        st.metric("As diseño", f"{res_top['As_design']:.2f} cm²")
        st.caption(f"Controla: {summary_top['criterio_gobernante']}")
        st.caption(
            f"rho={res_top['rho']:.5f} | phi={res_top['phi']:.3f} | epsilon_t={res_top['epsilon_t']:.5f}"
        )

    if summary_bot["criterio_gobernante"] == "Gobierna acero mínimo":
        st.info("Cara inferior: gobierna acero mínimo.")
    else:
        st.info("Cara inferior: gobierna demanda por Mu.")

    if summary_top["criterio_gobernante"] == "Gobierna acero mínimo":
        st.info("Cara superior: gobierna acero mínimo.")
    else:
        st.info("Cara superior: gobierna demanda por Mu.")

    # 4) Checklist de comprobaciones ACI
    st.divider()
    st.subheader("Checklist de comprobaciones ACI")
    checklist_rows = build_flexure_checklist("Inferior (+)", res_bot) + build_flexure_checklist(
        "Superior (-)", res_top
    )
    checklist_df = pd.DataFrame(
        checklist_rows,
        columns=["Cara", "Check", "Code Ref", "Formula", "Estado", "Valor", "Comentario"],
    )
    st.table(checklist_df)
