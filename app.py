import datetime
import streamlit as st
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, get_car_image
from utils.helpers import local_css, recomendaciones_itv_coste

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

        # Imagen del coche
        img_url = get_car_image(marca, modelo)
        if img_url:
            st.image(img_url, caption=f"{marca} {modelo}", use_column_width=True)
        else:
            st.info("No se encontró imagen para este modelo.")

        # Checklist con coste
        edad = datetime.date.today().year - anio
        recomendaciones = recomendaciones_itv_coste(edad, km, combustible)

        if recomendaciones:
            st.subheader("✅ Recomendaciones antes de la ITV")
            total = 0
            for tarea, motivo, coste in recomendaciones:
                st.checkbox(f"{tarea} — {motivo} (≈ {coste} €)", value=False)
                total += coste
            st.markdown(f"**💰 Coste estimado total:** ≈ {total} €")
        else:
            st.info("No hay recomendaciones específicas para este vehículo.")
    else:
        st.warning("Selecciona una marca y modelo válido.")
