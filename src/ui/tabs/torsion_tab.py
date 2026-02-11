import streamlit as st

from src.models import torsion
from src.models.torsion_distribution import distribute_torsion_longitudinal_reinf
from src.ui import plotting
from src.ui.design_state import get_design_snapshot, init_design_state, update_design_inputs


def render(section):
    st.header("Diseño por Torsión (T)")
    st.markdown("Verificación según ACI 318-19 Cap. 22.7")
    init_design_state(st.session_state)
    snapshot = get_design_snapshot(st.session_state)

    col1, col2 = st.columns(2)
    with col1:
        Tu = st.number_input("Torsión Última (Tu) [kNm]", 0.0, None, snapshot.tu, 1.0, key="Tu")
    with col2:
        Vu = st.number_input("Cortante Concomitante (Vu) [kN]", 0.0, None, snapshot.vu_torsion, 5.0, key="Vu_torsion")

    update_design_inputs(st.session_state, tu=Tu, vu_torsion=Vu)

    res = torsion.calculate_torsion(section, Tu, Vu)

    st.divider()

    # Threshold check
    c1, c2, c3 = st.columns(3)
    c1.metric("Tu (Aplicado)", f"{Tu:.2f} kNm")
    c2.metric("T_th (Umbral)", f"{res['T_th']:.2f} kNm", help="Torsión umbral para despreciar efectos")
    c3.metric("T_cr (Agrietamiento)", f"{res['T_cr']:.2f} kNm", help="Torsión de agrietamiento")

    # Status Logic
    if "Neglectable" in res['status']:
        st.success(res['status'])
        st.info("No se requiere refuerzo específico por torsión.")
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
            st.caption("Distribuir en el perímetro de la sección (ACI 9.5.4.3)")

        # --- Distribution of Al along perimeter ---
        al_total = res.get('Al_req', 0)
        if al_total > 0:
            st.divider()
            st.subheader("Distribución de Al en el Perímetro")
            st.caption("ACI 318-19 Sec. 9.5.4.3: Al se distribuye alrededor del perímetro de los estribos cerrados, "
                       "con separación máx. 300 mm y al menos una barra en cada esquina.")

            n_bars = st.number_input(
                "Número total de barras longitudinales por torsión",
                min_value=4, max_value=20, value=max(4, snapshot.n_bars_torsion), step=2,
                key="n_bars_torsion",
                help="Mínimo 4 (una por esquina). Distribuir simétricamente."
            )
            dist = distribute_torsion_longitudinal_reinf(
                al_total=al_total,
                b_cm=section.b,
                h_cm=section.h,
                cover_cm=section.cover,
                n_bars=n_bars,
            )
            update_design_inputs(st.session_state, n_bars_torsion=n_bars)

            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("Cara Inferior", f"{dist.al_bottom:.2f} cm2",
                       help=f"{dist.n_bottom} barras x {dist.al_per_bar:.2f} cm2")
            dc2.metric("Cara Superior", f"{dist.al_top:.2f} cm2",
                       help=f"{dist.n_top} barras x {dist.al_per_bar:.2f} cm2")
            dc3.metric("Cada Cara Lateral", f"{dist.al_side_each:.2f} cm2",
                       help=f"{dist.n_side_each} barras x {dist.al_per_bar:.2f} cm2" if dist.n_side_each > 0 else "Incluido en caras sup/inf")

            st.info(f"Área por barra: **{dist.al_per_bar:.2f} cm2** ({dist.n_bars} barras total)")

            # Store distribution in session state for report tab
            st.session_state["al_torsion_bottom"] = dist.al_bottom
            st.session_state["al_torsion_top"] = dist.al_top
            st.session_state["al_torsion_side"] = dist.al_side_each
            st.session_state["al_torsion_total"] = al_total
            st.session_state["al_torsion_n_bars"] = dist.n_bars
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
        st.pyplot(fig, use_container_width=False)
