import streamlit as st
from src.models import torsion
from src.ui import plotting

def render(section):
    st.header("Diseno por Torsion (T)")
    st.markdown("Verificacion segun ACI 318-19 Cap. 22.7")

    col1, col2 = st.columns(2)
    with col1:
        Tu = st.number_input("Torsion Ultima (Tu) [kNm]", 0.0, None, 15.0, 1.0, key="Tu")
    with col2:
        Vu = st.number_input("Cortante Concomitante (Vu) [kN]", 0.0, None, 50.0, 5.0, key="Vu_torsion")

    res = torsion.calculate_torsion(section, Tu, Vu)

    st.divider()

    # Threshold check
    c1, c2, c3 = st.columns(3)
    c1.metric("Tu (Aplicado)", f"{Tu:.2f} kNm")
    c2.metric("T_th (Umbral)", f"{res['T_th']:.2f} kNm", help="Torsion umbral para despreciar efectos")
    c3.metric("T_cr (Agrietamiento)", f"{res['T_cr']:.2f} kNm", help="Torsion de agrietamiento")

    # Status Logic
    if "Neglectable" in res['status']:
        st.success(res['status'])
        st.info("No se requiere refuerzo especifico por torsion.")
    elif "Error" in res['status']:
        st.error(res['status'])
        st.write(f"Verificacion Seccion: {res['check_cross_section']}")
    else:
        st.warning(res['status'])

        st.subheader("Refuerzo Requerido")

        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("#### Estribos Cerrados")
            st.metric("At/s (una rama)", f"{res.get('At_s_req', 0):.4f} mm2/mm")
            st.caption(f"Equivale a {res.get('At_s_req_cm2_m', 0):.2f} cm2/m por rama")

        with rc2:
            st.markdown("#### Refuerzo Longitudinal Adicional")
            st.metric("Al Total", f"{res.get('Al_req', 0):.2f} cm2")
            st.caption("Distribuir en el perimetro de la seccion (ACI 9.5.4.3)")

        # --- Distribution of Al along perimeter ---
        al_total = res.get('Al_req', 0)
        if al_total > 0:
            st.divider()
            st.subheader("Distribucion de Al en el Perimetro")
            st.caption("ACI 318-19 Sec. 9.5.4.3: Al se distribuye alrededor del perimetro de los estribos cerrados, "
                       "con separacion max. 300 mm. Al menos una barra en cada esquina.")

            b_inner = section.b - 2 * section.cover
            h_inner = section.h - 2 * section.cover
            ph = 2 * (b_inner + h_inner)  # perimeter in cm

            # Proportional distribution by face length
            al_bottom = al_total * b_inner / ph
            al_top = al_total * b_inner / ph
            al_side_each = al_total * h_inner / ph  # per side

            n_bars = st.number_input(
                "Numero total de barras longitudinales por torsion",
                min_value=4, max_value=20, value=6, step=2,
                key="n_bars_torsion",
                help="Minimo 4 (una por esquina). Distribuir simetricamente."
            )

            al_per_bar = al_total / n_bars

            # Distribution: 2 corners bottom + extra, 2 corners top + extra, sides
            n_bottom = max(2, round(n_bars * b_inner / ph))
            n_top = max(2, round(n_bars * b_inner / ph))
            n_sides = n_bars - n_bottom - n_top
            if n_sides < 0:
                n_sides = 0
                n_bottom = n_bars // 2
                n_top = n_bars - n_bottom
            n_side_each = max(0, n_sides // 2)
            # Adjust if odd remainder
            if n_sides % 2 != 0:
                n_bottom += 1
                n_sides -= 1
                n_side_each = n_sides // 2

            al_bottom_actual = n_bottom * al_per_bar
            al_top_actual = n_top * al_per_bar
            al_side_actual = n_side_each * al_per_bar

            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("Cara Inferior", f"{al_bottom_actual:.2f} cm2",
                       help=f"{n_bottom} barras x {al_per_bar:.2f} cm2")
            dc2.metric("Cara Superior", f"{al_top_actual:.2f} cm2",
                       help=f"{n_top} barras x {al_per_bar:.2f} cm2")
            dc3.metric("Cada Cara Lateral", f"{al_side_actual:.2f} cm2",
                       help=f"{n_side_each} barras x {al_per_bar:.2f} cm2" if n_side_each > 0 else "Incluido en caras sup/inf")

            st.info(f"Area por barra: **{al_per_bar:.2f} cm2** ({n_bars} barras total)")

            # Store distribution in session state for report tab
            st.session_state["al_torsion_bottom"] = al_bottom_actual
            st.session_state["al_torsion_top"] = al_top_actual
            st.session_state["al_torsion_side"] = al_side_actual
            st.session_state["al_torsion_total"] = al_total
            st.session_state["al_torsion_n_bars"] = n_bars
        else:
            st.session_state["al_torsion_bottom"] = 0.0
            st.session_state["al_torsion_top"] = 0.0
            st.session_state["al_torsion_side"] = 0.0
            st.session_state["al_torsion_total"] = 0.0
            st.session_state["al_torsion_n_bars"] = 0

        with st.expander("Verificacion de Seccion Transversal"):
            st.write(res.get('check_cross_section', 'N/A'))

        # Visualization
        st.subheader("Esquema")
        fig = plotting.draw_beam_section_torsion(
            section.b, section.h, section.cover,
            al_total=al_total,
            n_long_bars=st.session_state.get("al_torsion_n_bars", 6)
        )
        st.pyplot(fig)
