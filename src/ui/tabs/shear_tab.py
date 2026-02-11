import streamlit as st
from src.models import shear

def render(section):
    st.header("Diseño por Cortante (V)")
    
    col1, col2 = st.columns(2)
    with col1:
        Vu = st.number_input("Cortante Último (Vu) [kN]", 0.0, None, 50.0, 5.0)
    with col2:
        stirrup_bar = st.selectbox("Diámetro Estribo", ["#3 (3/8\")", "#4 (1/2\")"])
        n_legs = st.number_input("Ramas", 2, 4, 2)
        
    bar_diam = 0.95 if stirrup_bar.startswith("#3") else 1.27
    
    res = shear.calculate_shear(section, Vu, n_legs, bar_diam)
    
    st.divider()
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Vc (Concreto)", f"{res['Vc']:.2f} kN")
        st.metric("Vs Requerido", f"{res['Vs_req']:.2f} kN")
        
    with c2:
        if res['s_req']:
            st.success(f"Separación Requerida: {res['s_req']:.1f} cm")
            st.info(f"Separación Máxima (Norma): {res['s_max']:.1f} cm")
        else:
            st.info(res['status'])
