import streamlit as st
from services.api import get_makes, get_models
from config import APP_TITLE, APP_ICON
from utils.helpers import local_css

# --- CONFIG ---
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# --- UI ---
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo disponible en Europa.")

# Selección Marca
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox("Marca", options=makes, index=None)

# Selección Modelo (dinámico)
modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos, index=None)

# Botón de búsqueda
if st.button("🔍 Buscar información"):
    if marca and modelo:
        st.success(f"Has seleccionado **{marca} {modelo}**")
    else:
        st.warning("Selecciona una marca y modelo válido.")
