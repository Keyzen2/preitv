import streamlit as st
import datetime

def local_css(file_name):
    """Carga CSS local."""
    with open(file_name) as f:

        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        
def recomendaciones_itv(edad, km, combustible):
    """
    Devuelve recomendaciones antes de la ITV basadas en edad, kilometraje y combustible.
    """
    recomendaciones = []

    # Reglas basadas en la edad
    if edad >= 4:
        recomendaciones.append("Revisar estado de neumáticos y presión")
        recomendaciones.append("Comprobar funcionamiento de luces y señalización")
    if edad >= 8:
        recomendaciones.append("Inspeccionar sistema de frenos (pastillas y discos)")
        recomendaciones.append("Verificar holguras en suspensión y dirección")

    # Reglas basadas en kilometraje
    if km >= 60000:
        recomendaciones.append("Cambiar aceite y filtro de aceite")
        recomendaciones.append("Revisar filtro de aire")
    if km >= 100000:
        recomendaciones.append("Sustituir correa de distribución si aplica")
        recomendaciones.append("Revisar sistema de refrigeración")

    # Reglas según combustible
    if combustible.lower() == "diésel":
        recomendaciones.append("Comprobar filtro de partículas (DPF)")
        recomendaciones.append("Verificar sistema de inyección")
    elif combustible.lower() == "gasolina":
        recomendaciones.append("Revisar bujías y sistema de encendido")
    elif combustible.lower() == "híbrido":
        recomendaciones.append("Comprobar batería híbrida y sistema eléctrico")
    elif combustible.lower() == "eléctrico":
        recomendaciones.append("Revisar estado de batería de tracción y carga")

    return recomendaciones
