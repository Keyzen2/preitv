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
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
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
    "talleres": [],
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
        st.warning(f"Error geocodificando {city_name}: {e}")
    return None

# -----------------------------
# Header y footer
# -----------------------------
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0;">
    <img src="https://raw.githubusercontent.com/tu_usuario/tu_repositorio/main/logo.png" width="150">
    <span style="font-size:14px; color:gray;">© 2025 PreITV</span>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Login / Registro
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
                        st.session_state.data_loaded = False  # Cargar historial al iniciar sesión
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
    st.subheader(f"👋 Hola, {st.session_state.user.user_metadata.get('full_name','Usuario')}")
    with st.expander("⚙️ Configuración de cuenta", expanded=True):
        nuevo_nombre = st.text_input("Cambiar nombre", value=st.session_state.user.user_metadata.get("full_name",""))
        nueva_pass = st.text_input("Nueva contraseña", type="password")
        if st.button("Guardar cambios"):
            updates = {}
            if nuevo_nombre != st.session_state.user.user_metadata.get("full_name",""):
                updates["full_name"] = nuevo_nombre
            if nueva_pass:
                updates["password"] = nueva_pass
            if updates:
                try:
                    from services.supabase_client import supabase
                    supabase.auth.update_user(updates)
                    st.success("Cambios guardados correctamente")
                    st.session_state.user.user_metadata["full_name"] = nuevo_nombre
                except Exception as e:
                    st.error(f"No se pudieron guardar los cambios: {e}")
    if st.button("Cerrar sesión"):
        sign_out()
        for k in st.session_state.keys():
            st.session_state[k] = None
        st.experimental_rerun()

# -----------------------------
# Render App Principal
# -----------------------------
def render_main_app():
    # Carga historial desde Supabase solo si hay usuario y no cargado
    if st.session_state.user and not st.session_state.data_loaded:
        historial, historial_rutas = load_user_data(str(st.session_state.user.id))
        st.session_state.historial = historial
        st.session_state.historial_rutas = historial_rutas
        st.session_state.data_loaded = True

    # Tabs dinámicas
    if st.session_state.user:
        tab_busqueda, tab_rutas, tab_historial, tab_panel = st.tabs(
            ["Búsqueda de vehículos", "Planificador de rutas", "Historial de búsquedas y rutas", "Panel de usuario"]
        )
    else:
        tab_busqueda, tab_rutas = st.tabs(
            ["Búsqueda de vehículos", "Planificador de rutas"]
        )

    # -----------------------------
    # TAB: Búsqueda de vehículos
    # -----------------------------
    with tab_busqueda:
        if not st.session_state.user:
            st.warning("⚠️ Para guardar tus búsquedas, regístrate o inicia sesión.")
        st.subheader("🚗 Buscador de Vehículos")
        makes = get_makes()
        marca = st.selectbox("Marca", options=makes)
        modelos = get_models(marca) if marca else []
        modelo = st.selectbox("Modelo", options=modelos)
        anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year)
        km = st.number_input("Kilometraje", min_value=0, step=1000)
        combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])
        if st.button("🔍 Buscar información"):
            resumen = resumen_proximos_mantenimientos(km)
            st.info(f"📅 {resumen}")
            checklist = recomendaciones_itv_detalladas(datetime.date.today().year - anio, km, combustible)
            st.session_state.checklist = checklist
            registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
            if st.session_state.user:
                if registro not in st.session_state.historial:
                    st.session_state.historial.append(registro)
                    save_search(str(st.session_state.user.id), f"{marca} {modelo}", registro)

        if st.session_state.user and st.session_state.historial:
            with st.expander("📜 Coches consultados", expanded=True):
                for item in st.session_state.historial:
                    st.markdown(f"**{item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")

        if st.session_state.checklist:
            st.subheader("✅ Recomendaciones antes de la ITV")
            for tarea, cat in st.session_state.checklist:
                st.markdown(f"- **{cat}:** {tarea}")

    # -----------------------------
    # TAB: Planificador de rutas
    # -----------------------------
    with tab_rutas:
        if not st.session_state.user:
            st.warning("⚠️ Para guardar rutas, regístrate o inicia sesión.")
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
                    horas, minutos = int(distancia_min // 60), int(distancia_min % 60)
                    duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
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

                    if st.session_state.user:
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
                            save_route(
                                str(st.session_state.user.id),
                                origen_nombre,
                                destino_nombre,
                                distancia_km,
                                duracion_str,
                                litros,
                                coste
                            )
                else:
                    st.warning("No se pudo calcular la ruta")
            else:
                st.warning("No se pudo obtener la ubicación de una o ambas ciudades")

        # Mostrar mapa
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

    # -----------------------------
    # TAB: Historial (solo usuarios)
    # -----------------------------
    if st.session_state.user:
        with tab_historial:
            st.subheader("📜 Historial de búsquedas")
            if st.session_state.historial:
                for i, item in enumerate(st.session_state.historial, start=1):
                    st.markdown(f"**{i}. {item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")
            else:
                st.info("No hay búsquedas guardadas")
            st.subheader("📜 Historial de rutas")
            if st.session_state.historial_rutas:
                for i, r in enumerate(st.session_state.historial_rutas, start=1):
                    st.markdown(f"**{i}. {r['origen']} → {r['destino']}** — {r['distancia_km']} km — {r['duracion']} — {r['consumo_l']} L — {r['coste']} €")
            else:
                st.info("No hay rutas guardadas")

        # Panel de usuario
        with tab_panel:
            render_user_panel()

# -----------------------------
# Flujo principal
# -----------------------------
if not st.session_state.user:
    render_login_form()
render_main_app()
