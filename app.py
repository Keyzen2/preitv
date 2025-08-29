import datetime
import streamlit as st
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, search_workshops
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# Inicializar session_state
defaults = {
    "historial": [],
    "checklist": [],
    "ultima_marca": None,
    "ultima_modelo": None,
    "ultimo_anio": None,
    "ultimo_km": None,
    "ultimo_combustible": None,
    "talleres": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v  # CORREGIDO: = en lugar de st.session_state[k = v]

st.title("🚗 Buscador de Vehículos (Versión PRO)")

# Marcas y modelos
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox(
    "Marca", options=makes,
    index=makes.index(st.session_state.ultima_marca) if st.session_state.ultima_marca in makes else 0
)
modelos = get_models(marca) if marca else []
modelo = st.selectbox(
    "Modelo", options=modelos,
    index=modelos.index(st.session_state.ultima_modelo) if st.session_state.ultima_modelo in modelos else 0
)

anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year, value=st.session_state.ultimo_anio or 2000)
km = st.number_input("Kilometraje", min_value=0, step=1000, value=st.session_state.ultimo_km or 0)
combustible = st.selectbox(
    "Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"],
    index=["Gasolina", "Diésel", "Híbrido", "Eléctrico"].index(st.session_state.ultimo_combustible or "Gasolina")
)

# Buscar talleres
st.markdown("---")
st.subheader("🔧 Talleres en tu ciudad")

ciudades_sugeridas = ["— Escribe tu ciudad —", "Almería", "Madrid", "Barcelona", "Valencia", "Sevilla"]
colc1, colc2 = st.columns([1, 1])
with colc1:
    ciudad_sel = st.selectbox("Ciudad (rápido)", ciudades_sugeridas, index=0)
with colc2:
    ciudad_txt = st.text_input("O escribe tu ciudad", value="" if ciudad_sel == ciudades_sugeridas[0] else "")

ciudad_busqueda = ciudad_txt.strip() if ciudad_txt.strip() else (None if ciudad_sel == ciudades_sugeridas[0] else ciudad_sel)

colb1, colb2 = st.columns([1, 3])
with colb1:
    buscar_talleres = st.button("🔧 Buscar talleres")
with colb2:
    limite = st.slider("Resultados a mostrar", min_value=1, max_value=10, value=5)

if buscar_talleres:
    if not ciudad_busqueda:
        st.warning("Escribe o selecciona una ciudad de España.")
    else:
        with st.spinner(f"Buscando talleres en {ciudad_busqueda}..."):
            st.session_state.talleres = search_workshops(ciudad_busqueda, limit=limite)
        if not st.session_state.talleres:
            st.info("No se han encontrado talleres con datos suficientes en esta ciudad.")

# Mostrar resultados limitados
for i, t in enumerate(st.session_state.talleres, start=1):
    nombre = t.get("name") or "Taller sin nombre"
    addr = t.get("address") or ""
    tel = t.get("phone")
    web = t.get("website")
    lat = t.get("lat")
    lon = t.get("lon")
    oh = t.get("opening_hours")

    linea_titulo = f"**{i}. {nombre}**"
    if web:
        linea_titulo = f"[{linea_titulo}]({web})"

    st.markdown(linea_titulo)
    if addr: st.markdown(f"- **Dirección:** {addr}")
    if tel: st.markdown(f"- **Teléfono:** [Llamar](tel:{tel})")
    if oh: st.markdown(f"- **Horario:** {oh}")
    if lat and lon:
        osm = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=17/{lat}/{lon}"
        st.markdown(f"- **Mapa:** [Ver en OpenStreetMap]({osm})")
    st.markdown("---")



