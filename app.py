import datetime
import streamlit as st
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, get_brand_image
from utils.helpers import local_css, recomendaciones_itv

# Configuración
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# UI
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo disponible en Europa.")

# Selección Marca
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox("Marca", options=makes, index=None)
modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos, index=None)

# Datos para checklist ITV
anio = st.number_input("Año de matriculación", min_value=1980, max_value=datetime.date.today().year)
km = st.number_input("Kilometraje", min_value=0, step=1000)
combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

# Botón
if st.button("🔍 Buscar información"):
    if marca and modelo:
        st.success(f"Has seleccionado **{marca} {modelo}**")

        # Imagen genérica de la marca desde Wikipedia
        img_url = get_brand_image(marca)
        if img_url:
            st.image(img_url, caption=f"{marca}", use_column_width=True)
        else:
            st.info("No se encontró imagen para esta marca.")

        # Guardar checklist en sesión
        edad = datetime.date.today().year - anio
        st.session_state.checklist = recomendaciones_itv(edad, km, combustible)
    else:
        st.warning("Selecciona una marca y modelo válido.")

# Mostrar checklist persistente
if "checklist" in st.session_state and st.session_state.checklist:
    st.subheader("✅ Recomendaciones antes de la ITV")
    for i, tarea in enumerate(st.session_state.checklist):
        st.checkbox(tarea, key=f"chk_{i}")
