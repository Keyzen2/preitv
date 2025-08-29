import datetime
import streamlit as st
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models
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
for key in ["historial", "checklist", "ultima_marca", "ultima_modelo", "ultimo_anio", "ultimo_km", "ultimo_combustible"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["historial", "checklist"] else None

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

anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year, value=st.session_state.ultimo_anio or 2000)
km = st.number_input("Kilometraje", min_value=0, step=1000, value=st.session_state.ultimo_km or 0)
combustible = st.selectbox(
    "Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"],
    index=["Gasolina", "Diésel", "Híbrido", "Eléctrico"].index(st.session_state.ultimo_combustible or "Gasolina")
)

# Botones principales
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

# Mostrar checklist agrupado con colores
if st.session_state.checklist:
    st.subheader("✅ Recomendaciones antes de la ITV")

    iconos = {
        "Kilometraje": "⚙",
        "Edad del vehículo": "📅",
        "Combustible específico": "🔋",
        "Otros": "🔧"
    }

    for tarea, categoria in st.session_state.checklist:
        icono = iconos.get(categoria, "")
        color = "green"
        if any(word in tarea.lower() for word in ["correa", "pastillas", "aceite"]) and km >= 60000:
            color = "red"
        elif any(word in tarea.lower() for word in ["correa", "pastillas", "aceite"]) and km >= 50000:
            color = "orange"

        st.markdown(f"<span style='color:{color}'>{icono} {tarea}</span>", unsafe_allow_html=True)


