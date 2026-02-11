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

    # Torsion longitudinal distribution from session state
    al_total = st.session_state.get("al_torsion_total", res_tors.get('Al_req', 0))
    al_bottom = st.session_state.get("al_torsion_bottom", al_total / 3)
    al_top = st.session_state.get("al_torsion_top", al_total / 3)
    al_side = st.session_state.get("al_torsion_side", al_total / 6)
    torsion_significant = "Required" in res_tors.get('status', '') or al_total > 0

    # ──────────────────────────────────────────────────────────────
    # 1. REFUERZO LONGITUDINAL
    # ──────────────────────────────────────────────────────────────
    st.subheader("1. Refuerzo Longitudinal")

    as_flex_bot = res_flex_pos['As_design']
    as_flex_top = res_flex_neg['As_design']

    if torsion_significant:
        st.markdown("**Combinacion Flexion + Torsion Longitudinal (ACI 318-19)**")

        # Combined table
        combined_data = {
            "Cara": ["Inferior", "Superior", "Lateral (c/u)"],
            "As Flexion (cm2)": [
                f"{as_flex_bot:.2f}",
                f"{as_flex_top:.2f}",
                "---"
            ],
            "Al Torsion (cm2)": [
                f"{al_bottom:.2f}",
                f"{al_top:.2f}",
                f"{al_side:.2f}"
            ],
            "TOTAL (cm2)": [
                f"{(as_flex_bot + al_bottom):.2f}",
                f"{(as_flex_top + al_top):.2f}",
                f"{al_side:.2f}"
            ],
        }
        st.table(pd.DataFrame(combined_data))

        # Summary metrics
        total_bot = as_flex_bot + al_bottom
        total_top = as_flex_top + al_top

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("As Total Inferior", f"{total_bot:.2f} cm2",
                   delta=f"+{al_bottom:.2f} por torsion" if al_bottom > 0 else None)
        mc2.metric("As Total Superior", f"{total_top:.2f} cm2",
                   delta=f"+{al_top:.2f} por torsion" if al_top > 0 else None)
        mc3.metric("As Lateral (c/lado)", f"{al_side:.2f} cm2")

        st.caption("Nota: El acero por torsion longitudinal se suma al acero por flexion en cada cara. "
                   "El acero lateral es adicional y se coloca en las caras del alma.")

    else:
        # No significant torsion - simple table
        long_data = {
            "Ubicacion": ["Inferior (Flexion +)", "Superior (Flexion -)"],
            "As Requerido (cm2)": [
                f"{as_flex_bot:.2f}",
                f"{as_flex_top:.2f}"
            ],
            "Comentarios": [
                res_flex_pos['status'],
                res_flex_neg['status'] if mu_neg > 0 else "Sin momento negativo"
            ]
        }
        st.table(pd.DataFrame(long_data))
        st.info("Torsion despreciable - no se requiere acero longitudinal adicional por torsion.")

    # ──────────────────────────────────────────────────────────────
    # 2. REFUERZO TRANSVERSAL
    # ──────────────────────────────────────────────────────────────
    st.divider()
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
