import datetime
import streamlit as st
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, get_brand_image
from utils.helpers import local_css, recomendaciones_itv_detalladas

# Configuración
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# Inicializar histórico
if "historial" not in st.session_state:
    st.session_state.historial = []

# UI principal
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo disponible en Europa.")

# Cargar todas las marcas europeas de config.py vía API
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox("Marca", options=makes, index=None, placeholder="Elige una marca")
modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos, index=None, placeholder="Elige un modelo")

# Datos para checklist ITV
anio = st.number_input("Año de matriculación", min_value=1980, max_value=datetime.date.today().year)
km = st.number_input("Kilometraje", min_value=0, step=1000)
combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Buscar información"):
        if marca and modelo:
            st.success(f"Has seleccionado **{marca} {modelo}**")

            # Imagen genérica de la marca
            img_url = get_brand_image(marca)
            if img_url:
                st.image(img_url, caption=f"{marca}", use_column_width=True)
            else:
                st.info("No se encontró imagen para esta marca.")

            # Generar recomendaciones
            edad = datetime.date.today().year - anio
            st.session_state.checklist = recomendaciones_itv_detalladas(edad, km, combustible)

            # Guardar en histórico
