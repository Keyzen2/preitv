import datetime
import time
import requests
import streamlit as st
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, search_workshops
from services.routes import get_route, calcular_coste
from services.fuel import get_fuel_prices, filter_cheapest_on_route
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos, ciudades_es
import folium
from streamlit_folium import st_folium

# -----------------------------
# Función auxiliar para geocodificar con Nominatim
# -----------------------------
def geocode_city(city_name):
    """Devuelve (lat, lon) de una ciudad usando Nominatim."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": city_name,
            "format": "json",
            "limit": 1,
            "countrycodes": "es"
        }
        headers = {"User-Agent": "PreITV-App"}
        res = requests.get(url, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        st.error(f"Error geocodificando {city_name}: {e}")
    return None

# -----------------------------
# Configuración y CSS
# -----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# -----------------------------
# Inicializar session_state
# -----------------------------
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
        st.session_state[k] = v

# -----------------------------
# Título
# -----------------------------
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo para ver recomendaciones y próximos mantenimientos.")

# -----------------------------
# Marcas y modelos
# -----------------------------
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox("Marca", options=makes,
    index=makes.index(st.session_state.ultima_marca) if st.session_state.ultima_marca in makes else None)

modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos,
    index=modelos.index(st.session_state.ultima_modelo) if st.session_state.ultima_modelo in modelos else None)

anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year,
    value=st.session_state.ultimo_anio or 2000)
km = st.number_input("Kilometraje", min_value=0, step=1000,
    value=st.session_state.ultimo_km or 0)
combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"],
    index=["Gasolina", "Diésel", "Híbrido", "Eléctrico"].index(st.session_state.ultimo_combustible or "Gasolina"))

# -----------------------------
# Acciones principales
# -----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Buscar información"):
        if marca and modelo:
            st.session_state.update({
                "ultima_marca": marca,
                "ultima_modelo": modelo,
                "ultimo_anio": anio,
                "ultimo_km": km,
                "ultimo_combustible": combustible
            })
            st.success(f"Has seleccionado **{marca} {modelo}**")
            resumen = resumen_proximos_mantenimientos(km)
            st.info(f"📅 {resumen}")
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
            st.warning("Selecciona marca y modelo.")

with col2:
    if st.button("📜 Coches consultados"):
        if st.session_state.historial:
            st.subheader("Histórico consultado")
            for item in st.session_state.historial:
                st.markdown(f"**{item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")
        else:
            st.info("Histórico vacío.")

with col3:
    if st.button("🗑 Limpiar histórico"):
        st.session_state["historial"] = []
        st.session_state["checklist"] = []
        st.success("Histórico borrado.")

# -----------------------------
# Checklist ITV
# -----------------------------
if st.session_state.checklist:
    st.subheader("✅ Recomendaciones antes de la ITV")
    iconos = {"Kilometraje": "⚙", "Edad del vehículo": "📅", "Combustible específico": "🔋", "Otros": "🔧"}
    grupos = {}
    for tarea, categoria in st.session_state.checklist:
        grupos.setdefault(categoria, []).append(tarea)
    for cat in ["Kilometraje", "Edad del vehículo", "Combustible específico", "Otros"]:
        if cat in grupos:
            st.markdown(f"**{iconos[cat]} {cat}**")
            for tarea in grupos[cat]:
                color = "green"
                if any(w in tarea.lower() for w in ["correa", "pastillas", "aceite"]) and km >= 60000:
                    color = "red"
                elif any(w in tarea.lower() for w in ["correa", "pastillas", "aceite"]) and km >= 50000:
                    color = "orange"
                st.markdown(f"<span style='color:{color}'>• {tarea}</span>", unsafe_allow_html=True)

# -----------------------------
# Talleres por ciudad
# -----------------------------
st.markdown("---")
st.subheader("🔧 Talleres en tu ciudad")

colc1, colc2 = st.columns(2)
with colc1:
    ciudad_sel = st.selectbox("Ciudad (rápido)", ["— Escribe tu ciudad —"] + ciudades_es, index=0)
with colc2:
    ciudad_txt = st.text_input("O escribe tu ciudad", value="" if ciudad_sel == "— Escribe tu ciudad —" else "")

ciudad_busqueda = ciudad_txt.strip() if ciudad_txt.strip() else (None if ciudad_sel == "— Escribe tu ciudad —" else ciudad_sel)
colb1, colb2 = st.columns([1, 3])
with colb1:
    buscar_talleres = st.button("🔧 Buscar talleres")
with colb2:
    limite = st.slider("Resultados", min_value=3, max_value=10, value=5, step=1)

if buscar_talleres:
    if not ciudad_busqueda:
        st.warning("Escribe o selecciona ciudad.")
    else:
        with st.spinner(f"Buscando talleres en {ciudad_busqueda}..."):
            st.session_state.talleres = search_workshops(ciudad_busqueda, limit=limite)
            time.sleep(0.3)
        if not st.session_state.talleres:
            st.info("Sin datos de talleres en esta ciudad.")

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

# -----------------------------
# 🗺️ Planificador de ruta y coste de combustible
# -----------------------------
st.subheader("🗺️ Planificador de ruta y coste de combustible")

TIPO_COMBUSTIBLE_MAP = {
    "Gasolina": "Gasolina 95 E5",
    "Diésel": "Gasoleo A",
    "Híbrido": "Gasolina 95 E5",
    "Eléctrico": None
}
tipo_comb_api = TIPO_COMBUSTIBLE_MAP.get(combustible)

col_r1, col_r2 = st.columns(2)
with col_r1:
    origen_nombre = st.text_input("Ciudad de origen", "Almería")
with col_r2:
    destino_nombre = st.text_input("Ciudad de destino", "Sevilla")

col_r3, col_r4, col_r5 = st.columns(3)
with col_r3:
    consumo = st.number_input("Consumo medio (L/100km)", min_value=3.0, max_value=20.0, value=6.5)
with col_r4:
    precio = st.number_input("Precio combustible (€/L)", min_value=0.5, max_value=3.0, value=1.6)
with col_r5:
    calcular_ruta = st.button("Calcular ruta y coste")

if calcular_ruta:
    coords_origen = geocode_city(origen_nombre)
    coords_destino = geocode_city(destino_nombre)

    if not coords_origen or not coords_destino:
        st.error("No se pudo obtener la ubicación de una o ambas ciudades.")
    else:
        lat_o, lon_o = coords_origen
        lat_d, lon_d = coords_destino

        with st.spinner(f"Calculando ruta de {origen_nombre} a {destino_nombre}..."):
            ruta = get_route((lon_o, lat_o), (lon_d, lat_d))

        if ruta:
            distancia_km, duracion_min, coords_linea = ruta

            # Formatear duración
            horas = int(duracion_min // 60)
            minutos = int(duracion_min % 60)
            duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"

            litros, coste = calcular_coste(distancia_km, consumo, precio)
            st.success(f"Distancia: {distancia_km:.1f} km — Duración: {duracion_str}")
            st.info(f"Consumo estimado: {litros} L — Coste estimado: {coste} €")

            # Mapa base
            m = folium.Map(location=[lat_o, lon_o], zoom_start=6)
            folium.Marker([lat_o, lon_o], tooltip=f"Origen: {origen_nombre}").add_to(m)
            folium.Marker([lat_d, lon_d], tooltip=f"Destino: {destino_nombre}").add_to(m)
            folium.PolyLine([(lat, lon) for lon, lat in coords_linea],
                            color="blue", weight=4).add_to(m)

            # Gasolineras más baratas
            if tipo_comb_api:
                st.subheader(f"⛽ Gasolineras más baratas ({tipo_comb_api}) en la ruta")
                estaciones = get_fuel_prices()
                coords_filtradas = coords_linea[::10]  # 1 de cada 10 puntos
                baratas = filter_cheapest_on_route(
                    estaciones, coords_filtradas,
                    fuel_type=tipo_comb_api,
                    max_distance_km=3, limit=5
                )

                if baratas:
                    # Recalcular coste con el precio mínimo
                    mejor_precio = baratas[0]['precio']
                    litros, coste_mejor = calcular_coste(distancia_km, consumo, mejor_precio)
                    st.info(f"💡 Repostando en la más barata ({mejor_precio} €/L) → Coste viaje: {coste_mejor} €")

                    for g in baratas:
                        folium.Marker(
                            [g["lat"], g["lon"]],
                            tooltip=f"{g['rotulo']} - {g['precio']} €/L",
                            icon=folium.Icon(color="green", icon="tint", prefix="fa")
                        ).add_to(m)
                        st.markdown(f"**{g['rotulo']}** — {g['precio']} €/L — {g['direccion']} ({g['municipio']})")
                else:
                    st.info("No se encontraron gasolineras cercanas a la ruta.")
            else:
                st.info("No se buscan gasolineras para vehículos eléctricos en la API MITECO.")

            # Mostrar mapa
            st_folium(m, width=700, height=500)

        else:
            st.error("No se pudo calcular la ruta.")
