import datetime
import streamlit as st
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, get_brand_image
from utils.helpers import local_css, recomendaciones_itv_detalladas

# Configuración de página
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# Inicializar session_state
if "historial" not in st.session_state:
    st.session_state.historial = []
if "checklist" not in st.session_state:
    st.session_state.checklist = []

# Título y explicación
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo disponible en Europa para ver recomendaciones agrupadas por tipo.")

# Marcas y modelos
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox("Marca", options=makes, index=None, placeholder="Elige una marca")
modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos, index=None, placeholder="Elige un modelo")

# Datos del vehículo
anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year)
km = st.number_input("Kilometraje", min_value=0, step=1000)
combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

# Botones principales
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Buscar información"):
        if marca and modelo:
            st.success(f"Has seleccionado **{marca} {modelo}**")

            # Imagen de marca
            img_url = get_brand_image(marca)
            if img_url:
                st.image(img_url, caption=f"{marca}", use_column_width=True)
            else:
                st.info("No se encontró imagen para esta marca.")

            # Guardar checklist y en histórico
            edad = datetime.date.today().year - anio
            st.session_state.checklist = recomendaciones_itv_detalladas(edad, km, combustible)
            registro = {
                "marca": marca,
                "modelo": modelo,
                "anio": anio,
                "km": km,
                "combustible": combustible
            }
            if registro not in st.session_state.historial:
                st.session_state.historial.append(registro)
        else:
            st.warning("Selecciona una marca y modelo válido.")

with col2:
    if st.button("📜 Coches consultados"):
        if st.session_state.historial:
            st.subheader("Histórico de coches consultados en esta sesión")
            for item in st.session_state.historial:
                st.markdown(f"**{item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")
        else:
            st.info("Aún no has consultado ningún coche.")

with col3:
    if st.button("🗑 Limpiar histórico"):
        st.session_state.historial = []
        st.session_state.checklist = []
        st.success("Histórico y checklist borrados.")

# Mostrar checklist agrupado por categorías
if st.session_state.checklist:
    st.subheader("✅ Recomendaciones antes de la ITV")

    iconos = {
        "Kilometraje": "⚙",
        "Edad del vehículo": "📅",
        "Combustible específico": "🔋",
        "Otros": "🔧"
    }

    grupos = {}
    for tarea, categoria in st.session_state.checklist:
        grupos.setdefault(categoria, []).append(f"{iconos.get(categoria, '')} {tarea}")

    # Mostrar en orden predefinido
    orden_categorias = ["Kilometraje", "Edad del vehículo", "Combustible específico", "Otros"]
    for cat in orden_categorias:
        if cat in grupos:
            st.markdown(f"**{cat}**")
            for item in grupos[cat]:
                st.write(f"• {item}")

