import streamlit as st
import datetime

def local_css(file_name):
    """Carga CSS local."""
    with open(file_name) as f:

        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        
def recomendaciones_itv(edad, km, combustible):
    recomendaciones = []

    # Por kilometraje
    if km >= 5000:
        recomendaciones.append("Revisar nivel de aceite, fugas y estado de neumáticos")
    if km >= 10000:
        recomendaciones.append("Alineación y balanceo, rotación de neumáticos, chequeo eléctrico")
    if km >= 15000:
        recomendaciones.append("Cambio de aceite y filtro, revisión frenos y batería")
    if km >= 30000:
        recomendaciones.append("Cambio de pastillas de freno y revisión de discos")
    if km >= 40000 and combustible.lower() == "gasolina":
        recomendaciones.append("Sustituir bujías y revisar encendido")
    if km >= 60000:
        recomendaciones.append("Cambio de filtro de aire y combustible, revisar correa distribución")
    if km >= 100000:
        recomendaciones.append("Sustituir correa distribución y revisar refrigeración")

    # Por edad
    if edad >= 4:
        recomendaciones.append("Comprobar luces, señalización y holguras de suspensión")
    if edad >= 8:
        recomendaciones.append("Inspección completa de frenos, dirección y chasis")

    # Por combustible
    if combustible.lower() == "diésel":
        recomendaciones.append("Comprobar filtro de partículas (DPF) y sistema de inyección")
    elif combustible.lower() == "híbrido":
        recomendaciones.append("Revisar batería híbrida y sistema eléctrico")
    elif combustible.lower() == "eléctrico":
        recomendaciones.append("Comprobar batería de tracción y sistema de carga")

    return recomendaciones
