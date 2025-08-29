import datetime
import time
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, search_workshops
from services.routes import get_route, calcular_coste
from services.supabase_client import sign_in, sign_up, sign_out, save_search, save_route
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos, ciudades_es

# -----------------------------
# Configuración
# -----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# -----------------------------
# Utilidades
# -----------------------------
def geocode_city(city_name: str):
    """Devuelve (lat, lon) de una ciudad usando Nominatim (OSM)."""
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
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        st.error(f"Error geocodificando {city_name}: {e}")
    return None

# -----------------------------
# Estado inicial
# -----------------------------
defaults = {
    "historial": [],
    "historial_rutas": [],
    "checklist": [],
    "user": None,
    "talleres": [],
    "ultima_marca": None,
    "ultima_modelo": None,
    "ultimo_anio": None,
    "ultimo_km": None,
    "ultimo_combustible": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# Login / Registro
# -----------------------------
if not st.session_state.user:
    st.subheader("🔐 Iniciar sesión o registrarse")
    tab_login, tab_signup = st.tabs(["Iniciar sesión", "Registrarse"])

    with tab_login:
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            res = sign_in(email, password)
            if getattr(res, "user", None):
                st.session_state.user = res.user
                st.success("Sesión iniciada")
                st.experimental_rerun()
            else:
                st.error("Credenciales incorrectas")

    with tab_signup:
        email_s = st.text_input("Email nuevo")
        password_s = st.text_input("Contraseña nueva", type="password")
        if st.button("Crear cuenta"):
            res = sign_up(email_s, password_s)
            if getattr(res, "user", None):
                st.success("Cuenta creada. Revisa tu email para verificar.")
            else:
                st.error("No se pudo crear la cuenta")
    st.stop()
else:
    col_user1, col_user2 = st.columns([3, 1])
    with col_user1:
        st.write(f"👋 Hola, {st.session_state.user.email}")
    with col_user2:
        if st.button("Cerrar sesión"):
            sign_out()
            st.session_state.user = None
            st.experimental_rerun()

# -----------------------------
# Título general
# -----------------------------
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo para ver recomendaciones y próximos mantenimientos, busca talleres y planifica rutas con coste estimado.")

# -----------------------------
# 🚗 Buscador de Vehículos
# -----------------------------
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox(
    "Marca",
    options=makes,
    index=(makes.index(st.session_state.ultima_marca) if st.session_state.ultima_marca in makes else 0) if makes else 0,
)

modelos = get_models(marca) if marca else []
modelo = st.selectbox(
    "Modelo",
    options=modelos,
    index=(modelos.index(st.session_state.ultima_modelo) if st.session_state.ultima_modelo in modelos else 0) if modelos else 0,
)

anio = st.number_input(
    "Año de matriculación",
    min_value=1900,
    max_value=datetime.date.today().year,
    value=st.session_state.ultimo_anio or 2008
)
km = st.number_input(
    "Kilometraje",
    min_value=0,
    step=1000,
    value=st.session_state.ultimo_km or 0
)
combustible = st.selectbox(
    "Combustible",
    ["Gasolina", "Diésel", "Híbrido", "Eléctrico"],
    index=(["Gasolina", "Diésel", "Híbrido", "Eléctrico"].index(st.session_state.ultimo_combustible)
           if st.session_state.ultimo_combustible in ["Gasolina", "Diésel", "Híbrido", "Eléctrico"] else 0)
)

col_veh1, col_veh2 = st.columns([1, 1])
with col_veh1:
    if st.button("🔍 Buscar información"):
        if marca and modelo:
            st.session_state.ultima_marca = marca
            st.session_state.ultima_modelo = modelo
            st.session_state.ultimo_anio = anio
            st.session_state.ultimo_km = km
            st.session_state.ultimo_combustible = combustible

            st.success(f"Has seleccionado **{marca} {modelo}**")
            resumen = resumen_proximos_mantenimientos(km)
            st.info(f"📅 {resumen}")

            edad = datetime.date.today().year - anio
            st.session_state.checklist = recomendaciones_itv_detalladas(edad, km, combustible)

            registro = {
                "marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible
            }
            if registro not in st.session_state.historial:
                st.session_state.historial.append(registro)
        else:
            st.warning("Selecciona una marca y modelo válidos.")
with col_veh2:
    if st.button("🗑 Limpiar coches"):
        st.session_state.historial = []
        st.session_state.checklist = []
        st.success("Histórico de coches y checklist borrados.")

if st.session_state.historial:
    if st.button("📜 Coches consultados"):
        st.subheader("Histórico de coches consultados en esta sesión")
        for item in st.session_state.historial:
            st.markdown(
                f"**{item['marca']} {item['modelo']}** — {item['anio']} — "
                f"{item['km']} km — {item['combustible']}"
            )

if st.session_state.checklist:
    st.subheader("✅ Recomendaciones antes de la ITV")
    # Agrupar por categoría si viene en formato [(tarea, categoría)]
    grupos = {}
    for tarea_cat in st.session_state.checklist:
        if isinstance(tarea_cat, (tuple, list)) and len(tarea_cat) == 2:
            tarea, categoria = tarea_cat
        else:
            tarea, categoria = tarea_cat, "Otros"
        grupos.setdefault(categoria, []).append(tarea)

    orden_categorias = ["Kilometraje", "Edad del vehículo", "Combustible específico", "Otros"]
    iconos = {"Kilometraje": "⚙", "Edad del vehículo": "📅", "Combustible específico": "🔋", "Otros": "🔧"}

    for cat in orden_categorias:
        if cat in grupos:
            st.markdown(f"**{iconos.get(cat, '🔧')} {cat}**")
            for tarea in grupos[cat]:
                color = "green"
                texto = tarea.lower()
                if any(w in texto for w in ["correa", "pastillas", "aceite"]) and km >= 60000:
                    color = "red"
                elif any(w in texto for w in ["correa", "pastillas", "aceite"]) and km >= 50000:
                    color = "orange"
                st.markdown(f"<span style='color:{color}'>• {tarea}</span>", unsafe_allow_html=True)

# -----------------------------
# 🔧 Talleres por ciudad
# -----------------------------
st.markdown("---")
st.subheader("🔧 Talleres en tu ciudad")

col_tw1, col_tw2 = st.columns([2, 1])
with col_tw1:
    ciudad_busqueda = st.text_input("Ciudad", value="")
with col_tw2:
    limite = st.slider("Resultados", min_value=3, max_value=10, value=5, step=1)

col_t_btn1, col_t_btn2 = st.columns([1, 1])
with col_t_btn1:
    buscar_talleres = st.button("Buscar talleres")
with col_t_btn2:
    limpiar_talleres = st.button("Limpiar talleres")

if limpiar_talleres:
    st.session_state.talleres = []
    st.success("Listado de talleres limpiado.")

if buscar_talleres:
    if not ciudad_busqueda.strip():
        st.warning("Escribe una ciudad de España.")
    else:
        with st.spinner(f"Buscando talleres en {ciudad_busqueda}..."):
            resultados = search_workshops(ciudad_busqueda.strip(), limit=limite)
            st.session_state.talleres = resultados
            time.sleep(0.2)
        if resultados:
            # Guardar en Supabase
            try:
                save_search(user_id=str(st.session_state.user.id), city=ciudad_busqueda.strip(), results=resultados)
            except Exception as e:
                st.warning(f"No se pudo guardar la búsqueda en Supabase: {e}")
        else:
            st.info("No se han encontrado talleres con datos suficientes en esta ciudad.")

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
# 🗺️ Planificador de ruta y coste
# -----------------------------
st.markdown("---")
st.subheader("🗺️ Planificador de ruta y coste")

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
    calcular_ruta = st.button("Calcular ruta")

if calcular_ruta:
    coords_origen = geocode_city(origen_nombre.strip())
    coords_destino = geocode_city(destino_nombre.strip())

    if not coords_origen or not coords_destino:
        st.error("No se pudo obtener la ubicación de una o ambas ciudades.")
    else:
        lat_o, lon_o = coords_origen
        lat_d, lon_d = coords_destino

        with st.spinner(f"Calculando ruta de {origen_nombre} a {destino_nombre}..."):
            ruta = get_route((lon_o, lat_o), (lon_d, lat_d))

        if ruta:
            distancia_km, duracion_min, coords_linea = ruta

            # Duración en horas y minutos
            horas = int(duracion_min // 60)
            minutos = int(duracion_min % 60)
            duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"

            litros, coste = calcular_coste(distancia_km, consumo, precio)

            st.success(f"Distancia: {distancia_km:.1f} km — Duración: {duracion_str}")
            st.info(f"Consumo estimado: {litros} L — Coste estimado: {coste} €")

            # Mapa de la ruta
            try:
                m = folium.Map(location=[lat_o, lon_o], zoom_start=6)
                folium.Marker([lat_o, lon_o], tooltip=f"Origen: {origen_nombre}").add_to(m)
                folium.Marker([lat_d, lon_d], tooltip=f"Destino: {destino_nombre}").add_to(m)
                folium.PolyLine([(lat, lon) for lon, lat in coords_linea], color="blue", weight=4).add_to(m)
                st_folium(m, width=700, height=500)
            except Exception as e:
                st.warning(f"No se pudo renderizar el mapa: {e}")

            # Guardar en histórico local
            registro_ruta = {
                "origen": origen_nombre,
                "destino": destino_nombre,
                "distancia_km": round(distancia_km, 1),
                "duracion": duracion_str,
                "consumo_l": litros,
                "coste": coste
            }
            if registro_ruta not in st.session_state.historial_rutas:
                st.session_state.historial_rutas.append(registro_ruta)

            # Guardar en Supabase
            try:
                save_route(
                    user_id=str(st.session_state.user.id),
                    origin=origen_nombre,
                    destination=destino_nombre,
                    distance_km=distancia_km,
                    duration=duracion_str,
                    consumption_l=litros,
                    cost=coste
                )
            except Exception as e:
                st.warning(f"No se pudo guardar la ruta en Supabase: {e}")

        else:
            st.error("No se pudo calcular la ruta.")

# Histórico de rutas: mostrar y limpiar
col_hist1, col_hist2 = st.columns([1, 1])
with col_hist1:
    if st.button("📜 Rutas consultadas"):
        if st.session_state.historial_rutas:
            st.subheader("Histórico de rutas")
            for r in st.session_state.historial_rutas:
                st.markdown(
                    f"**{r['origen']} → {r['destino']}** — {r['distancia_km']} km — "
                    f"{r['duracion']} — {r['consumo_l']} L — {r['coste']} €"
                )
        else:
            st.info("Sin rutas guardadas.")
with col_hist2:
    if st.button("🗑 Limpiar rutas"):
        st.session_state.historial_rutas = []
        st.success("Histórico de rutas borrado.")
