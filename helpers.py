import streamlit as st

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"No se pudo cargar CSS: {e}")

def resumen_proximos_mantenimientos(km):
    checklist = []
    if km > 100000:
        checklist.append("Revisar motor y transmisión")
    checklist.append("Revisar aceite y filtros")
    checklist.append("Revisar frenos y neumáticos")
    return f"Tu vehículo tiene {km} km. {', '.join(checklist)}."

def recomendaciones_itv_detalladas(anio, km, combustible):
    checklist = []
    if km > 150000:
        checklist.append(("Revisar motor y transmisión", "Seguridad"))
    if anio <= 5:
        checklist.append(("Revisión general anual", "Carrocería"))
    if combustible in ["Híbrido", "Eléctrico"]:
        checklist.append(("Revisar batería y sistemas eléctricos", "Electricidad"))
    else:
        checklist.append(("Revisar sistema de escape", "Emisiones"))
    return checklist

def geocode_city(city_name: str):
    from utils.ciudades_coords import ciudades_coords
    coords = ciudades_coords.get(city_name)
    if coords:
        return coords
    else:
        st.error(f"No se encontraron coordenadas para {city_name}")
        return None
