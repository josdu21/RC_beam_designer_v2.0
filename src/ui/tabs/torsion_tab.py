import streamlit as st
from src.models import torsion

def render(section):
    st.header("Diseño por Torsión (T)")
    st.markdown("Verificación según ACI 318-19 Cap. 22.7")
    
    col1, col2 = st.columns(2)
    with col1:
        Tu = st.number_input("Torsión Última (Tu) [kNm]", 0.0, None, 15.0, 1.0)
    with col2:
        Vu = st.number_input("Cortante Concomitante (Vu) [kN]", 0.0, None, 50.0, 5.0)
        
    res = torsion.calculate_torsion(section, Tu, Vu)
    
    st.divider()
    
    # Threshold check
    c1, c2, c3 = st.columns(3)
    c1.metric("Tu (Aplicado)", f"{Tu:.2f} kNm")
    c2.metric("T_th (Umbral)", f"{res['T_th']:.2f} kNm", help="Torsión umbral para despreciar efectos")
    c3.metric("T_cr (Agrietamiento)", f"{res['T_cr']:.2f} kNm", help="Torsión de agrietamiento")
    
    # Status Logic
    if "Neglectable" in res['status']:
        st.success("✅ " + res['status'])
        st.info("No se requiere refuerzo específico por torsión.")
    elif "Error" in res['status']:
        st.error("❌ " + res['status'])
        if "check_cross_section" in res:
            st.write(f"Verificación Sección: {res['check_cross_section']}")
    else:
        st.warning("⚠️ " + res['status'])
        
        st.subheader("Refuerzo Requerido")
        
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown("#### Estribos Cerrados")
            st.metric("At/s (una rama)", f"{res.get('At_s_req', 0):.4f} mm²/mm")
            # Convert to sensible units for display
            ats_cm2_m = res.get('At_s_req', 0) * 1000 / 100 # mm2/mm * 1000mm/m / 100mm2/cm2 = cm2/m
            st.caption(f"Equivale a {ats_cm2_m:.2f} cm²/m por rama")
            
        with rc2:
            st.markdown("#### Refuerzo Longitudinal Adicional")
            st.metric("Al Total", f"{res.get('Al_req', 0):.2f} cm²")
            st.caption("Distribuir en el perímetro de la sección")
            
        with st.expander("Verificación de Sección Transversal"):
            st.write(res.get('check_cross_section', 'N/A'))
