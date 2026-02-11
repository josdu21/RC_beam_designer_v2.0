import streamlit as st
import pandas as pd
from src.models import flexure, shear, torsion

def render(section):
    st.header("📄 Reporte Resumen de Diseño")
    
    # Re-calculate everything based on current session state inputs? 
    # Ideally, we should pull from session state, but for simplicity we rely on inputs
    # generated in other tabs being stored in session_state if we used keys.
    # Since we didn't use keys in previous steps, we can't pull exact values easily without global state.
    # TO FIX: We will instruct user that this report generates a sample based on default or 
    # we need to refactor inputs to use st.session_state.
    
    st.info("Nota: Para un reporte preciso, asegúrese de haber ingresado las cargas en las pestañas respectivas.")
    
    # Let's create a summary table that allows re-inputting key loads for the report
    # or assumes a "Case Study" mode.
    # Better approach: Add inputs here for the "Design Case" to summarize.
    
    md_col1, md_col2, md_col3 = st.columns(3)
    with md_col1:
        mu_pos = st.number_input("Mu+ [kNm]", 0.0, None, 100.0, key="rep_mu_pos")
    with md_col2:
        vu = st.number_input("Vu [kN]", 0.0, None, 50.0, key="rep_vu")
    with md_col3:
        tu = st.number_input("Tu [kNm]", 0.0, None, 15.0, key="rep_tu")
        
    # Run Calculations
    res_flex = flexure.calculate_flexure(section, mu_pos)
    res_shear = shear.calculate_shear(section, vu)
    res_tors = torsion.calculate_torsion(section, tu, vu)
    
    st.subheader("1. Refuerzo Longitudinal")
    
    long_data = {
        "Ubicación": ["Inferior (Flexión)", "Superior (Flexión)", "Longitudinal Torsión (Total)", "TOTAL Inferior Estimado"],
        "As Requerdio (cm²)": [
            f"{res_flex['As_design']:.2f}",
            "0.00", # Placeholder as we asked only mu_pos
            f"{res_tors.get('Al_req', 0):.2f}",
            f"{(res_flex['As_design'] + res_tors.get('Al_req', 0)/3):.2f} *" # Rough estimate 1/3 Al bottom
        ],
        "Comentarios": [res_flex['status'], "-", "Distribuir en perímetro", "* Asumiendo 1/3 Al abajo"]
    }
    st.table(pd.DataFrame(long_data))
    
    st.subheader("2. Refuerzo Transversal (Estribos)")
    
    # Calculate combined Av/s
    # Av/s_total = (Av/s)_shear + 2 * (At/s)_torsion
    # Shear result gives s_req for a specific bar.
    # Let's compute (Av/s) ratio provided vs required.
    
    # Shear Av/s req = Vs / (fy * d)  (Simplified)
    # Torsion 2*At/s 
    
    st.write(f"**Cortante Vs:** {res_shear.get('Vs_req', 0):.2f} kN")
    
    if "Neglectable" in res_tors['status']:
        st.success("Torsión despreciable. Diseñar solo por Cortante.")
        st.metric("Separación Estribos (Cortante)", f"{res_shear.get('s_req', 0):.1f} cm")
    elif "Error" in res_tors['status']:
        st.error("Error en Torsión: " + res_tors['status'])
    else:
        st.warning("Torsión Significativa. Se requieren estribos cerrados.")
        # Calculate combined spacing for a chosen bar
        bar_diam = 0.95 # #3
        Av_bar = 0.71 # cm2
        
        # Area per leg for shear = Av_shear / 2 legs
        # Area per leg for torsion = At
        
        # Better: Calculate required (Area/spacing) TOTAL per leg
        # (Av+t / s) = (Av/s)/2 + (At/s)
        
        # From shear module we have s_req for 2 legs.
        # Av_shear_total / s_shear = Vs / (fyd)
        
        # Let's show data
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Estribos por Cortante", f"s = {res_shear.get('s_req', 0):.1f} cm")
        col_res2.metric("Refuerzo Torsión (At/s)", f"{res_tors.get('At_s_req', 0):.4f} mm²/mm")
