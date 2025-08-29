import datetime
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
    "ruta_datos": None,
    "limpiar_rutas": False
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
        if st.button("Entrar", key="login_button"):
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
        if st.button("Crear cuenta", key="signup_button"):
            res = sign_up(email_s, password_s)
            if getattr(res, "user", None):
                st.success("Cuenta creada. Revisa tu email para verificar.")
            else:
                st.error("No se pudo crear la cuenta")
    st.stop()

# Mostrar info de usuario y logout
col_user1, col_user2 = st.columns([3, 1])
with col_user1:
    st.write(f"👋 Hola, {st.session_state.user.email}")
with col_user2:
    if st.button("Cerrar sesión", key="logout"):
        sign_out()
        st.session_state.user = None
        st.experimental_rerun()

# -----------------------------
# Función geocodificación
# -----------------------------
def geocode_city(city_name: str):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city_name, "format": "json", "limit": 1, "countrycodes": "es"}
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
# 🚗 Buscador de Vehículos
# -----------------------------
st.subheader("🚗 Buscador de Vehículos")
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox("Marca", options=makes, index=makes.index(st.session_state.ultima_marca) if st.session_state.ultima_marca in makes else 0)
modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos, index=modelos.index(st.session_state.ultima_modelo) if st.session_state.ultima_modelo in modelos else 0)
anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year, value=st.session_state.ultimo_anio or 2000)
km = st.number_input("Kilometraje", min_value=0, step=1000, value=st.session_state.ultimo_km or 0)
combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"], index=["Gasolina","Diésel","Híbrido","Eléctrico"].index(st.session_state.ultimo_combustible or "Gasolina"))

if st.button("🔍 Buscar información", key="buscar_info"):
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

        registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
        if registro not in st.session_state.historial:
            st.session_state.historial.append(registro)
    else:
        st.warning("Selecciona marca y modelo.")

# Mostrar histórico de coches
if st.session_state.historial:
    st.subheader("📜 Coches consultados")
    for item in st.session_state.historial:
        st.markdown(f"**{item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")

# Mostrar checklist
if st.session_state.checklist:
    st.subheader("✅ Recomendaciones antes de la ITV")
    for tarea, cat in st.session_state.checklist:
        st.markdown(f"- **{cat}:** {tarea}")

# -----------------------------
# 🔧 Talleres por ciudad
# -----------------------------
st.markdown("---")
st.subheader("🔧 Talleres en tu ciudad")
ciudad_busqueda = st.text_input("Ciudad para buscar talleres", key="ciudad_input")
if st.button("Buscar talleres", key="buscar_talleres"):
    resultados = search_workshops(ciudad_busqueda, limit=5)
    st.session_state.talleres = resultados
    if resultados:
        save_search(user_id=str(st.session_state.user.id), city=ciudad_busqueda, results=resultados)

if st.session_state.talleres:
    for i, t in enumerate(st.session_state.talleres, start=1):
        st.markdown(f"**{i}. {t.get('name','Taller')}** — {t.get('address','')}")

# -----------------------------
# 🗺️ Planificador de ruta y coste
# -----------------------------
st.markdown("---")
st.subheader("🗺️ Planificador de ruta y coste")
origen_nombre = st.text_input("Ciudad de origen", "Almería", key="origen")
destino_nombre = st.text_input("Ciudad de destino", "Sevilla", key="destino")
consumo = st.number_input("Consumo medio (L/100km)", value=6.5, key="consumo")
precio = st.number_input("Precio combustible (€/L)", value=1.6, key="precio")

if st.button("Calcular ruta", key="calc_ruta"):
    coords_origen = geocode_city(origen_nombre.strip())
    coords_destino = geocode_city(destino_nombre.strip())
    if coords_origen and coords_destino:
        lat_o, lon_o = coords_origen
        lat_d, lon_d = coords_destino
        ruta = get_route((lon_o, lat_o), (lon_d, lat_d))
        if ruta:
            distancia_km, duracion_min, coords_linea = ruta
            horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
            duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
            litros, coste = calcular_coste(distancia_km, consumo, precio)
            # Guardar en session_state
            st.session_state.ruta_datos = {
                "origen": origen_nombre,
                "destino": destino_nombre,
                "coords_origen": (lat_o, lon_o),
                "coords_destino": (lat_d, lon_d),
                "coords_linea": coords_linea,
                "distancia_km": distancia_km,
                "duracion": duracion_str,
                "litros": litros,
                "coste": coste
            }
            registro_ruta = {
                "origen": origen_nombre, "destino": destino_nombre,
                "distancia_km": round(distancia_km, 1),
                "duracion": duracion_str,
                "consumo_l": litros, "coste": coste
            }
            if registro_ruta not in st.session_state.historial_rutas:
                st.session_state.historial_rutas.append(registro_ruta)
            save_route(user_id=str(st.session_state.user.id),
                       origin=origen_nombre, destination=destino_nombre,
                       distance_km=distancia_km, duration=duracion_str,
                       consumption_l=litros, cost=coste)
    else:
        st.error("No se pudo obtener la ubicación de una o ambas ciudades.")

# Botón siempre visible para limpiar rutas
if st.button("🗑 Limpiar rutas", key="limpiar_rutas_btn"):
    st.session_state.historial_rutas = []
    st.session_state.ruta_datos = None
    st.success("Histórico de rutas borrado.")

# Mostrar ruta si existe
if st.session_state.ruta_datos:
    datos = st.session_state.ruta_datos
    st.success(f"Distancia: {datos['distancia_km']:.1f} km — Duración: {datos['duracion']}")
    st.info(f"Consumo estimado: {datos['litros']} L — Coste estimado: {datos['coste']} €")

    try:
        m = folium.Map(location=datos["coords_origen"], zoom_start=6)
        folium.Marker(datos["coords_origen"], tooltip=f"Origen: {datos['origen']}").add_to(m)
        folium.Marker(datos["coords_destino"], tooltip=f"Destino: {datos['destino']}").add_to(m)
        folium.PolyLine([(lat, lon) for lon, lat in datos["coords_linea"]], color="blue", weight=4).add_to(m)
        st_folium(m, width=700, height=500, key="mapa_ruta")
    except Exception as e:
        st.warning(f"No se pudo renderizar el mapa: {e}")

# Histórico de rutas
st.markdown("---")
st.subheader("📜 Histórico de rutas")
if st.session_state.historial_rutas:
    for r in st.session_state.historial_rutas:
        st.markdown(
            f"**{r['origen']} → {r['destino']}** — {r['distancia_km']} km — "
            f"{r['duracion']} — {r['consumo_l']} L — {r['coste']} €"
        )
else:
    st.info("Aún no has guardado rutas en esta sesión.")
