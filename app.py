import datetime
import streamlit as st
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, search_workshops
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos

# Configuración de página y CSS responsive
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")
st.markdown("""
<style>
@media (max-width: 768px) {
    .block-container {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    h1, h2, h3, h4 {
        font-size: 1.1rem;
    }
}
</style>
""", unsafe_allow_html=True)

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
        st.session_state[k = v]  # noqa

# Título
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo de Europa para ver recomendaciones y próximos mantenimientos.")

# Marcas y modelos
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox(
    "Marca", options=makes,
    index=makes.index(st.session_state.ultima_marca) if st.session_state.ultima_marca in makes else None,
    placeholder="Elige una marca"
)
modelos = get_models(marca) if marca else []
modelo = st.selectbox(
    "Modelo", options=modelos,
    index=modelos.index(st.session_state.ultima_modelo) if st.session_state.ultima_modelo in modelos else None,
    placeholder="Elige un modelo"
)

# Datos del vehículo
anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year, value=st.session_state.ultimo_anio or 2000)
km = st.number_input("Kilometraje", min_value=0, step=1000, value=st.session_state.ultimo_km or 0)
combustible = st.selectbox(
    "Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"],
    index=["Gasolina", "Diésel", "Híbrido", "Eléctrico"].index(st.session_state.ultimo_combustible or "Gasolina")
)

# Acciones principales
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("🔍 Buscar información"):
        if marca and modelo:
            # Guardar última búsqueda
            st.session_state.ultima_marca = marca
            st.session_state.ultima_modelo = modelo
            st.session_state.ultimo_anio = anio
            st.session_state.ultimo_km = km
            st.session_state.ultimo_combustible = combustible

            st.success(f"Has seleccionado **{marca} {modelo}**")

            # Resumen de próximos mantenimientos
            resumen = resumen_proximos_mantenimientos(km)
            st.info(f"📅 {resumen}")

            # Generar checklist
            edad = datetime.date.today().year - anio
            st.session_state.checklist = recomendaciones_itv_detalladas(edad, km, combustible)

            # Guardar en histórico
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

# Checklist agrupado con orden fijo e indicadores de urgencia
if st.session_state.checklist:
    st.subheader("✅ Recomendaciones antes de la ITV")

    iconos = {
        "Kilometraje": "⚙",
        "Edad del vehículo": "📅",
        "Combustible específico": "🔋",
        "Otros": "🔧"
    }

    # Agrupar por categoría
    grupos = {}
    for tarea, categoria in st.session_state.checklist:
        grupos.setdefault(categoria, []).append(tarea)

    # Orden fijo por categoría
    orden_categorias = ["Kilometraje", "Edad del vehículo", "Combustible específico", "Otros"]
    for cat in orden_categorias:
        if cat in grupos:
            st.markdown(f"**{iconos[cat]} {cat}**")
            for tarea in grupos[cat]:
                color = "green"
                # Reglas de urgencia simples
                if any(word in tarea.lower() for word in ["correa", "pastillas", "aceite"]) and km >= 60000:
                    color = "red"
                elif any(word in tarea.lower() for word in ["correa", "pastillas", "aceite"]) and km >= 50000:
                    color = "orange"

                st.markdown(f"<span style='color:{color}'>• {tarea}</span>", unsafe_allow_html=True)

# ------------------------------------------------------------
# Talleres por ciudad (OSM/Overpass)
# ------------------------------------------------------------
st.markdown("---")
st.subheader("🔧 Talleres en tu ciudad")

# Sugerencias rápidas + campo libre
ciudades_sugeridas = [
    "— Escribe tu ciudad —", "Almería", "Madrid", "Barcelona", "Valencia", "Sevilla",
    "Zaragoza", "Málaga", "Murcia", "Palma", "Bilbao", "Valladolid", "Córdoba", "A Coruña",
    "Granada", "Oviedo", "Santander", "Donostia / San Sebastián", "Pamplona", "Vigo"
]
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
    limite = st.slider("Resultados a mostrar", min_value=3, max_value=10, value=5, step=1)

if buscar_talleres:
    if not ciudad_busqueda:
        st.warning("Escribe o selecciona una ciudad de España.")
    else:
        with st.spinner(f"Buscando talleres en {ciudad_busqueda}..."):
            st.session_state.talleres = search_workshops(ciudad_busqueda, limit=limite)
        if not st.session_state.talleres:
            st.info("No se han encontrado talleres con datos suficientes en esta ciudad. Prueba con otra población cercana.")

# Mostrar resultados de talleres
if st.session_state.talleres:
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
        if addr:
            st.markdown(f"- **Dirección:** {addr}")
        if tel:
            st.markdown(f"- **Teléfono:** [Llamar](tel:{tel})")
        if oh:
            st.markdown(f"- **Horario:** {oh}")
        if lat and lon:
            osm = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=17/{lat}/{lon}"
            st.markdown(f"- **Mapa:** [Ver en OpenStreetMap]({osm})")
        st.markdown("---")


