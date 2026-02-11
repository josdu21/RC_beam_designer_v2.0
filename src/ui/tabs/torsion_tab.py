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
            st.caption("Distribuir en el perimetro de la seccion")

        with st.expander("Verificacion de Seccion Transversal"):
            st.write(res.get('check_cross_section', 'N/A'))

        # Visualization
        st.subheader("Esquema")
        fig = plotting.draw_beam_section_torsion(
            section.b, section.h, section.cover,
            al_total=res.get('Al_req', 0)
        )
        st.pyplot(fig)
