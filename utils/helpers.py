import streamlit as st

def local_css(file_name):
    """Carga CSS local."""
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def recomendaciones_itv_coste(edad, km, combustible):
    """
    Devuelve lista de tuplas (tarea, motivo, coste_estimado)
    """
    recomendaciones = []

    def add(tarea, motivo, coste):
        recomendaciones.append((tarea, motivo, coste))

    if km >= 5000:
        add("Revisar nivel de aceite, fugas y neumáticos", "Evita desgaste prematuro", 20)
    if km >= 10000:
        add("Alineación, balanceo y rotación de neumáticos", "Mantiene estabilidad", 40)
    if km >= 15000:
        add("Cambio de aceite y filtro, revisión frenos y batería", "Lubricación y frenado óptimos", 120)
    if km >= 30000:
        add("Cambio de pastillas de freno, revisión discos", "Mejora frenado", 150)
    if km >= 40000 and combustible.lower() == "gasolina":
        add("Sustituir bujías y revisar encendido", "Optimiza combustión", 80)
    if km >= 60000:
        add("Cambio de filtro de aire y combustible, revisar correa distribución", "Previene averías graves", 250)
    if km >= 100000:
        add("Sustituir correa distribución y revisar refrigeración", "Evita rotura de motor", 500)

    if edad >= 4:
        add("Comprobar luces, señalización y suspensión", "Requisitos ITV", 30)
    if edad >= 8:
        add("Inspección completa de frenos, dirección y chasis", "Previene fallos estructurales", 200)

    if combustible.lower() == "diésel":
        add("Comprobar filtro de partículas (DPF) e inyección", "Evita pérdida de potencia", 180)
    elif combustible.lower() == "híbrido":
        add("Revisar batería híbrida y sistema eléctrico", "Mantiene autonomía", 300)
    elif combustible.lower() == "eléctrico":
        add("Comprobar batería de tracción y sistema de carga", "Asegura rendimiento", 150)

    return recomendaciones
