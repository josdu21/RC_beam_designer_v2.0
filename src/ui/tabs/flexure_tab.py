import streamlit as st

from src.models import flexure
from src.ui import plotting
from src.ui.design_state import get_design_snapshot, init_design_state, update_design_inputs


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
    
    c1, c2, c3 = st.columns([1,1,1])
    
    with c1:
        st.write("Resultados Inferior")
        if res_bot['status'].startswith("OK"):
            st.success(f"As Req: {res_bot['As_design']:.2f} cm²")
        else:
            st.error(res_bot['status'])
        st.metric("As Calc", f"{res_bot['As_calc']:.2f} cm²")
    
    with c2:
        st.write("Resultados Superior")
        if mu_neg > 0:
            if res_top['status'].startswith("OK"):
                st.success(f"As Req: {res_top['As_design']:.2f} cm²")
            else:
                st.error(res_top['status'])
            st.metric("As Calc", f"{res_top['As_calc']:.2f} cm²")
        else:
            st.info("Sin momento negativo")
            
    with c3:
        st.write("Esquema")
        as_b = res_bot['As_design'] if mu_pos > 0 else 0
        as_t = res_top['As_design'] if mu_neg > 0 else 0
        fig = plotting.draw_beam_section_flexure(section.b, section.h, section.cover, as_b, as_t)
        st.pyplot(fig)
