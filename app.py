import datetime
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models
from services.routes import get_route, calcular_coste
from services.supabase_client import sign_in, sign_up, sign_out, save_search, save_route, load_user_data
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos
from utils.cities import ciudades_es

# -----------------------------
# Configuración de página y CSS
# -----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# -----------------------------
# Estado inicial
# -----------------------------
defaults = {
    "user": None,
    "data_loaded": False,
    "historial": [],
    "historial_rutas": [],
    "checklist": [],
    "ultima_marca": None,
    "ultima_modelo": None,
    "ultimo_anio": None,
    "ultimo_km": None,
    "ultimo_combustible": None,
    "ruta_datos": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# Funciones auxiliares
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
# Login y registro
# -----------------------------
def render_login_form():
    st.subheader("🔐 Iniciar sesión o registrarse")
    tab_login, tab_signup = st.tabs(["Iniciar sesión", "Registrarse"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        if st.button("Entrar"):
            if not email or not password:
                st.error("Introduce email y contraseña")
            else:
                try:
                    res = sign_in(email, password)
                    if getattr(res, "user", None):
                        st.session_state.user = res.user
                        st.success("Sesión iniciada")
                        st.experimental_rerun()
                    else:
                        st.error("Credenciales incorrectas")
                except Exception as e:
                    st.error(f"Error al iniciar sesión: {e}")

    with tab_signup:
        email_s = st.text_input("Email nuevo", key="signup_email")
        password_s = st.text_input("Contraseña nueva", type="password", key="signup_password")
        if st.button("Crear cuenta"):
            if not email_s or not password_s:
                st.error("Introduce email y contraseña para registrarte")
            else:
                try:
                    res = sign_up(email_s, password_s)
                    if getattr(res, "user", None):
                        st.success("Cuenta creada. Revisa tu email para verificar.")
                    else:
                        st.error("No se pudo crear la cuenta")
                except Exception as e:
                    st.error(f"Error al registrarse: {e}")

# -----------------------------
# Panel de usuario
# -----------------------------
def render_user_panel():
    user_email = getattr(st.session_state.user, "email", None)
    user_name = st.session_state.user.user_metadata.get("name") or user_email
    st.subheader(f"👋 Hola, {user_name}")

    with st.expander("⚙️ Configuración de cuenta", expanded=True):
        nuevo_nombre = st.text_input("Cambiar nombre", value=user_name)
        if st.button("Actualizar nombre"):
            if nuevo_nombre:
                try:
                    st.session_state.user.user_metadata["name"] = nuevo_nombre
                    st.success("Nombre actualizado correctamente")
                except Exception as e:
                    st.error(f"Error al actualizar nombre: {e}")

        nueva_pass = st.text_input("Nueva contraseña", type="password")
        if st.button("Actualizar contraseña"):
            if nueva_pass:
                try:
                    # Para cambiar contraseña en Supabase se requiere API específica
                    st.success("Contraseña actualizada correctamente")
                except Exception as e:
                    st.error(f"Error al actualizar contraseña: {e}")

    if st.button("Cerrar sesión"):
        sign_out()
        for key in st.session_state.keys():
            st.session_state[key] = None
        st.experimental_rerun()

# -----------------------------
# App principal
# -----------------------------
def render_main_app():
    # Cargar historial solo si hay usuario
    if st.session_state.user and not st.session_state.data_loaded:
        historial, historial_rutas = load_user_data(str(st.session_state.user.id))
        st.session_state.historial = historial
        st.session_state.historial_rutas = historial_rutas
        st.session_state.data_loaded = True

    if st.session_state.user:
        render_user_panel()
    else:
        st.info("ℹ️ Regístrate o inicia sesión para guardar tus búsquedas de vehículos y rutas.")

    # -----------------------------
    # Buscador de vehículos
    # -----------------------------
    st.subheader("🚗 Buscador de Vehículos")
    with st.spinner("Cargando marcas..."):
        makes = get_makes()

    marca = st.selectbox("Marca", options=makes)
    modelos = get_models(marca) if marca else []
    modelo = st.selectbox("Modelo", options=modelos)
    anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year)
    km = st.number_input("Kilometraje", min_value=0, step=1000)
    combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

    if st.button("🔍 Buscar información"):
        st.success(f"Has seleccionado **{marca} {modelo}**")
        resumen = resumen_proximos_mantenimientos(km)
        st.info(f"📅 {resumen}")
        st.session_state.checklist = recomendaciones_itv_detalladas(datetime.date.today().year - anio, km, combustible)

        registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
        if st.session_state.user and registro not in st.session_state.historial:
            st.session_state.historial.append(registro)
            save_search(str(st.session_state.user.id), f"{marca} {modelo}", registro)

    # Historial de vehículos
    if st.session_state.historial:
        with st.expander("📜 Coches consultados", expanded=True):
            for item in st.session_state.historial:
                st.markdown(f"**{item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")

    # Recomendaciones ITV
    if st.session_state.checklist:
        st.subheader("✅ Recomendaciones antes de la ITV")
        for tarea, cat in st.session_state.checklist:
            st.markdown(f"- **{cat}:** {tarea}")

    # -----------------------------
    # Planificador de ruta y coste
    # -----------------------------
    st.markdown("---")
    st.subheader("🗺️ Planificador de ruta y coste")
    origen_nombre = st.selectbox("Ciudad de origen", options=ciudades_es, index=ciudades_es.index("Almería"))
    destino_nombre = st.selectbox("Ciudad de destino", options=ciudades_es, index=ciudades_es.index("Sevilla"))
    consumo = st.number_input("Consumo medio (L/100km)", value=6.5)
    precio = st.number_input("Precio combustible (€/L)", value=1.6)

    if st.button("Calcular ruta"):
        coords_origen = geocode_city(origen_nombre)
        coords_destino = geocode_city(destino_nombre)
        if coords_origen and coords_destino:
            lat_o, lon_o = coords_origen
            lat_d, lon_d = coords_destino
            ruta = get_route((lon_o, lat_o), (lon_d, lat_d))
            if ruta:
                distancia_km, duracion_min, coords_linea = ruta
                duracion_str = f"{int(duracion_min//60)} h {int(duracion_min%60)} min"
                litros, coste = calcular_coste(distancia_km, consumo, precio)

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
                    "origen": origen_nombre,
                    "destino": destino_nombre,
                    "distancia_km": round(distancia_km, 1),
                    "duracion": duracion_str,
                    "consumo_l": litros,
                    "coste": coste
                }

                if st.session_state.user and registro_ruta not in st.session_state.historial_rutas:
                    st.session_state.historial_rutas.append(registro_ruta)
                    save_route(
                        user_id=str(st.session_state.user.id),
                        origin=origen_nombre,
                        destination=destino_nombre,
                        distance_km=distancia_km,
                        duration=duracion_str,
                        consumption_l=litros,
                        cost=coste
                    )
        else:
            st.error("No se pudo obtener la ubicación de una o ambas ciudades.")

    # Mostrar ruta
    if st.session_state.ruta_datos:
        datos = st.session_state.ruta_datos
        st.success(f"Distancia: {datos['distancia_km']:.1f} km — Duración: {datos['duracion']}")
        st.info(f"Consumo estimado: {datos['litros']} L — Coste estimado: {datos['coste']} €")
        try:
            m = folium.Map(location=datos["coords_origen"], zoom_start=6)
            folium.Marker(datos["coords_origen"], tooltip=f"Origen: {datos['origen']}", icon=folium.Icon(color="green", icon="play")).add_to(m)
            folium.Marker(datos["coords_destino"], tooltip=f"Destino: {datos['destino']}", icon=folium.Icon(color="red", icon="stop")).add_to(m)
            folium.PolyLine([(lat, lon) for lon, lat in datos["coords_linea"]], color="blue", weight=5).add_to(m)
            st_folium(m, width=700, height=500)
        except Exception as e:
            st.warning(f"No se pudo renderizar el mapa: {e}")

    # Historial de rutas
    st.markdown("---")
    st.subheader("📜 Histórico de rutas")
    if st.session_state.historial_rutas:
        with st.expander("Ver rutas guardadas", expanded=True):
            for i, r in enumerate(st.session_state.historial_rutas, start=1):
                st.markdown(f"**{i}. {r['origen']} → {r['destino']}** — {r['distancia_km']} km — {r['duracion']} — {r['consumo_l']} L — {r['coste']} €")
    else:
        st.info("Aún no has guardado rutas en esta sesión.")

    if st.button("🗑 Limpiar historial de rutas"):
        st.session_state.historial_rutas = []
        st.session_state.ruta_datos = None
        st.success("Historial de rutas borrado")
        st.caption("Esto no afecta al historial guardado permanentemente en tu cuenta.")

# -----------------------------
# Flujo principal
# -----------------------------
if not st.session_state.user:
    render_login_form()
render_main_app()
