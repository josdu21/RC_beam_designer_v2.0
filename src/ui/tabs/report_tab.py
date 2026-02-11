import streamlit as st
import pandas as pd
from src.models import flexure, shear, torsion

def render(section):
    st.header("Reporte Resumen de Diseno")

    # Read values from session state (set by other tabs via key= parameter)
    mu_pos = st.session_state.get("mu_pos", 100.0)
    mu_neg = st.session_state.get("mu_neg", 0.0)
    vu = st.session_state.get("Vu", 50.0)
    tu = st.session_state.get("Tu", 15.0)
    vu_torsion = st.session_state.get("Vu_torsion", vu)

    # Show current design loads as read-only summary
    st.subheader("Cargas de Diseno")
    st.caption("Valores tomados de las pestanas de diseno. Modifiquelos en sus pestanas respectivas.")

    lc1, lc2, lc3, lc4 = st.columns(4)
    lc1.metric("Mu+ [kNm]", f"{mu_pos:.1f}")
    lc2.metric("Mu- [kNm]", f"{mu_neg:.1f}")
    lc3.metric("Vu [kN]", f"{vu:.1f}")
    lc4.metric("Tu [kNm]", f"{tu:.1f}")

    st.divider()

    # Run Calculations
    res_flex_pos = flexure.calculate_flexure(section, mu_pos)
    res_flex_neg = flexure.calculate_flexure(section, mu_neg)
    res_shear = shear.calculate_shear(section, vu)
    res_tors = torsion.calculate_torsion(section, tu, vu_torsion)

    st.subheader("1. Refuerzo Longitudinal")

    al_torsion = res_tors.get('Al_req', 0)

    long_data = {
        "Ubicacion": [
            "Inferior (Flexion +)",
            "Superior (Flexion -)",
            "Longitudinal Torsion (Total)",
            "TOTAL Inferior Estimado"
        ],
        "As Requerido (cm2)": [
            f"{res_flex_pos['As_design']:.2f}",
            f"{res_flex_neg['As_design']:.2f}",
            f"{al_torsion:.2f}",
            f"{(res_flex_pos['As_design'] + al_torsion / 3):.2f} *"
        ],
        "Comentarios": [
            res_flex_pos['status'],
            res_flex_neg['status'] if mu_neg > 0 else "Sin momento negativo",
            "Distribuir en perimetro",
            "* Asumiendo 1/3 Al abajo"
        ]
    }
    st.table(pd.DataFrame(long_data))

    st.subheader("2. Refuerzo Transversal (Estribos)")

    st.write(f"**Cortante Vs:** {res_shear.get('Vs_req', 0):.2f} kN")

    if "Neglectable" in res_tors['status']:
        st.success("Torsion despreciable. Disenar solo por Cortante.")
        s_req = res_shear.get('s_req')
        if s_req is not None:
            st.metric("Separacion Estribos (Cortante)", f"{s_req:.1f} cm")
        else:
            st.info(res_shear['status'])
    elif "Error" in res_tors['status']:
        st.error("Error en Torsion: " + res_tors['status'])
    else:
        st.warning("Torsion Significativa. Se requieren estribos cerrados.")

        col_res1, col_res2 = st.columns(2)
        s_req = res_shear.get('s_req')
        if s_req is not None:
            col_res1.metric("Estribos por Cortante", f"s = {s_req:.1f} cm")
        else:
            col_res1.info(res_shear['status'])
        col_res2.metric("Refuerzo Torsion (At/s)", f"{res_tors.get('At_s_req_cm2_m', 0):.2f} cm2/m")
