import streamlit as st
import os
from src.models.section import BeamSection
from src.ui.tabs import flexure_tab, shear_tab, torsion_tab, report_tab

# Page Config
st.set_page_config(page_title="RC Beam Designer Modular", page_icon="🏗️", layout="wide")

# CSS handled by .streamlit/config.toml
# def local_css(file_name): ...

# Sidebar (Global Inputs)
st.sidebar.title("Configuración Global")
st.sidebar.subheader("Materiales")
fc = st.sidebar.number_input("f'c [MPa]", 15.0, 100.0, 28.0)
fy = st.sidebar.number_input("fy [MPa]", 200.0, 600.0, 420.0)

st.sidebar.divider()
st.sidebar.subheader("Geometría Seccional")
b = st.sidebar.number_input("Ancho b [cm]", 10.0, 200.0, 30.0)
h = st.sidebar.number_input("Altura h [cm]", 15.0, 300.0, 50.0)
cover = st.sidebar.number_input("Recubrimiento [cm]", 2.0, 10.0, 4.0)

# Create Section Object
section = BeamSection(b, h, fc, fy, cover)

# Main App
st.title("🏗️ Diseñador de Vigas RC - Modular")

tab_flexure, tab_shear, tab_torsion, tab_report = st.tabs(["🔄 Flexión", "✂️ Cortante", "🌀 Torsión", "📄 Reporte"])

with tab_flexure:
    flexure_tab.render(section)

with tab_shear:
    shear_tab.render(section)
    
with tab_torsion:
    torsion_tab.render(section)
    
with tab_report:
    report_tab.render(section)
