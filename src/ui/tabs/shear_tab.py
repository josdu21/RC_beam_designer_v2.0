import streamlit as st

from src.models import shear
from src.ui import plotting
from src.ui.design_state import get_design_snapshot, init_design_state, update_design_inputs


def render(section):
    st.header("Diseño por Cortante (V)")
    init_design_state(st.session_state)
    snapshot = get_design_snapshot(st.session_state)

    col1, col2 = st.columns(2)
    with col1:
        Vu = st.number_input("Cortante Último (Vu) [kN]", 0.0, None, snapshot.vu, 5.0, key="Vu")
    with col2:
        bars = ['#3 (3/8")', '#4 (1/2")']
        selected_index = bars.index(snapshot.stirrup_bar) if snapshot.stirrup_bar in bars else 0
        stirrup_bar = st.selectbox("Diámetro Estribo", bars, index=selected_index, key="stirrup_bar")
        n_legs = st.number_input("Ramas", 2, 4, snapshot.n_legs, key="n_legs")

    bar_diam = 0.95 if stirrup_bar.startswith("#3") else 1.27
    update_design_inputs(st.session_state, vu=Vu, n_legs=n_legs, stirrup_bar=stirrup_bar)

    res = shear.calculate_shear(section, Vu, n_legs, bar_diam)

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Vc (Concreto)", f"{res['Vc']:.2f} kN")
        st.metric("Vs Requerido", f"{res['Vs_req']:.2f} kN")

    with c2:
        if res['s_req']:
            st.success(f"Separacion Requerida: {res['s_req']:.1f} cm")
            st.info(f"Separacion Maxima (Norma): {res['s_max']:.1f} cm")
        else:
            st.info(res['status'])

    # Visualization
    st.subheader("Esquema")
    fig = plotting.draw_beam_section_shear(section.b, section.h, section.cover, res.get('s_req'), n_legs)
    st.pyplot(fig)
