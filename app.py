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
from utils.cities import ciudades_coords

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
    """Devuelve coordenadas de la ciudad desde el diccionario local."""
    coords = ciudades_coords.get(city_name)
    if coords:
        return coords  # tuple (lat, lon)
    else:
        st.error(f"No se encontró la ciudad: {city_name}")
        return None

# -----------------------------
# Header y footer
# -----------------------------
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0;">
    <img src="https://raw.githubusercontent.com/keyzen2/preitv/styles/logo.png" width="150">
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
    # Header
    st.markdown(
        """
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <img src="logo.png" width="150"/>
            <h1 style="margin:0;">PreITV</h1>
        </div>
        <hr>
        """,
        unsafe_allow_html=True
    )

    # Inicializar Supabase
    if "supabase" not in st.session_state:
        from services.supabase_client import supabase
        st.session_state.supabase = supabase

    # Cargar historial de usuario si hay login
    if st.session_state.user and not st.session_state.get("data_loaded"):
        historial, historial_rutas = load_user_data(str(st.session_state.user.id))
        st.session_state.historial = historial
        st.session_state.historial_rutas = historial_rutas
        st.session_state.data_loaded = True

    # Tabs principales
    tabs = ["🚗 Vehículos", "🗺️ Rutas"]
    if st.session_state.user:
        tabs.append("📜 Historial de búsquedas")
        tabs.append("👤 Panel de usuario")

    tab_selected = st.tabs(tabs)

    # ----------------- TAB VEHÍCULOS -----------------
    with tab_selected[0]:
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
            checklist = recomendaciones_itv_detalladas(datetime.date.today().year - anio, km, combustible)
            for tarea, cat in checklist:
                st.markdown(f"- **{cat}:** {tarea}")

            # Guardar solo si hay usuario logueado
            if st.session_state.user:
                registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
                if registro not in st.session_state.historial:
                    st.session_state.historial.append(registro)
                    save_search(str(st.session_state.user.id), f"{marca} {modelo}", registro)
            else:
                st.warning("🔒 Regístrate o inicia sesión para guardar tus búsquedas.")

    # ----------------- TAB RUTAS -----------------
    with tab_selected[1]:
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
                    horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
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
                                user_id=str(st.session_state.user.id),
                                origin=origen_nombre,
                                destination=destino_nombre,
                                distance_km=distancia_km,
                                duration=duracion_str,
                                consumption_l=litros,
                                cost=coste
                            )
                    else:
                        st.warning("🔒 Regístrate o inicia sesión para guardar tus rutas.")
            else:
                st.error("No se pudo obtener la ubicación de una o ambas ciudades.")

        # Mostrar datos de la ruta
        if st.session_state.ruta_datos:
            d = st.session_state.ruta_datos
            st.success(f"Distancia: {d['distancia_km']:.1f} km — Duración: {d['duracion']}")
            st.info(f"Consumo estimado: {d['litros']} L — Coste estimado: {d['coste']} €")
            try:
                m = folium.Map(location=d["coords_origen"], zoom_start=6)
                folium.Marker(d["coords_origen"], tooltip=f"Origen: {d['origen']}", icon=folium.Icon(color="green")).add_to(m)
                folium.Marker(d["coords_destino"], tooltip=f"Destino: {d['destino']}", icon=folium.Icon(color="red")).add_to(m)
                folium.PolyLine([(lat, lon) for lon, lat in d["coords_linea"]], color="blue", weight=5).add_to(m)
                st_folium(m, width=700, height=500)
            except Exception as e:
                st.warning(f"No se pudo renderizar el mapa: {e}")

    # ----------------- TAB HISTORIAL -----------------
    if st.session_state.user and len(tabs) > 2:
        with tab_selected[2]:
            st.subheader("📜 Historial de búsquedas")
            if st.session_state.historial:
                with st.expander("Ver coches consultados", expanded=True):
                    for item in st.session_state.historial:
                        st.markdown(f"**{item.get('marca','N/A')} {item.get('modelo','N/A')}** — {item.get('anio','N/A')} — {item.get('km','N/A')} km — {item.get('combustible','N/A')}")
            else:
                st.info("Aún no has guardado búsquedas.")

            st.subheader("📜 Historial de rutas")
            if st.session_state.historial_rutas:
                with st.expander("Ver rutas guardadas en esta sesión", expanded=True):
                    for i, r in enumerate(st.session_state.historial_rutas, start=1):
                        origen = r.get("origen", "Desconocido")
                        destino = r.get("destino", "Desconocido")
                        distancia = r.get("distancia_km", 0)
                        duracion = r.get("duracion", "N/A")
                        consumo = r.get("consumo_l", 0)
                        coste = r.get("coste", 0)
                        st.markdown(
                            f"**{i}. {origen} → {destino}** — {distancia} km — {duracion} — {consumo} L — {coste} €"
                        )
                if st.button("🗑 Limpiar historial de la sesión actual"):
                    st.session_state.historial_rutas = []
                    st.session_state.ruta_datos = None
                    st.success("Historial de rutas de la sesión actual borrado.")
                    st.caption("Esto no afecta al historial guardado permanentemente en tu cuenta.")

    # ----------------- TAB PANEL DE USUARIO -----------------
    if st.session_state.user and len(tabs) > 3:
        with tab_selected[3]:
            render_user_panel()

    # Footer
    st.markdown(
        """
        <hr>
        <p style="text-align:center; color:gray;">&copy; 2025 PreITV. Todos los derechos reservados.</p>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# Flujo principal
# -----------------------------
if not st.session_state.user:
    render_login_form()
render_main_app()
