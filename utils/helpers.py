import streamlit as st

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"No se pudo cargar CSS: {e}")

def resumen_proximos_mantenimientos(km):
    return f"Tu vehículo tiene {km} km, revisa aceite, frenos y neumáticos."

def recomendaciones_itv_detalladas(edad, km, combustible):
    checklist = []
    if km > 100000:
        checklist.append(("Revisar motor y transmisión", "Seguridad"))
    if edad > 10:
        checklist.append(("Revisar corrosión y chasis", "Carrocería"))
    if combustible in ["Híbrido", "Eléctrico"]:
        checklist.append(("Revisar batería y sistemas eléctricos", "Electricidad"))
    else:
        checklist.append(("Revisar sistema de escape", "Emisiones"))
    return checklist







