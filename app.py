import datetime
import streamlit as st
import folium
from streamlit_folium import st_folium
from services.api import get_makes, get_models
from services.routes import get_route, calcular_coste
from services.supabase_client import sign_in, sign_up, sign_out, save_search, save_route, load_user_data
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos
from utils.cities import ciudades_es, ciudades_coords  # Diccionario con coordenadas de todas las ciudades españolas

# -----------------------------
# Configuración de página y CSS
# -----------------------------
st.set_page_config(page_title="PreITV", page_icon="🚗", layout="wide")
local_css("styles/theme.css")

# -----------------------------
# Header y footer
# -----------------------------
st.markdown("""
<header style="display:flex; align-items:center; padding:10px 0;">
    <img src="https://raw.githubusercontent.com/tu_usuario/tu_repo/main/logo.png" alt="Logo" width="120">
    <h1 style="margin-left:20px;">PreITV App</h1>
</header>
""", unsafe_allow_html=True)

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
    # Usar coordenadas predefinidas
    if city_name in ciudades_coords:
        return ciudades_coords[city_name]
    st.warning(f"No se encontró la ciudad {city_name} en coordenadas locales.")
    return None

# -----------------------------
# Login y registro en lateral
# -----------------------------
with st.sidebar.expander("🔐 Iniciar sesión / Registrarse", expanded=True):
    if not st.session_state.user:
        st.subheader("Login")
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

        st.subheader("Registrarse")
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
# Cargar historial desde Supabase (solo usuarios)
# -----------------------------
if st.session_state.user and not st.session_state.data_loaded:
    historial, historial_rutas = load_user_data(str(st.session_state.user.id))
    st.session_state.historial = historial
    st.session_state.historial_rutas = historial_rutas
    st.session_state.data_loaded = True

# -----------------------------
# Mensaje para usuarios no logueados
# -----------------------------
if not st.session_state.user:
    st.info("🔒 Regístrate o inicia sesión para guardar tus búsquedas y rutas.")

# -----------------------------
# Tabs principales
# -----------------------------
tabs = st.tabs(["📜 Historial de búsquedas", "🚗 Buscador de vehículos", "🗺️ Planificador de rutas"])

# 1️⃣ Historial de búsquedas
with tabs[0]:
    st.subheader("Historial de búsquedas")
    if st.session_state.user:
        if st.session_state.historial:
            for item in st.session_state.historial:
                st.markdown(f"**{item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")
        else:
            st.info("Aún no has guardado búsquedas de vehículos.")
        st.markdown("---")
        st.subheader("Historial de rutas")
        if st.session_state.historial_rutas:
            for i, r in enumerate(st.session_state.historial_rutas, start=1):
                st.markdown(f"**{i}. {r['origen']} → {r['destino']}** — {r['distancia_km']} km — {r['duracion']} — {r['consumo_l']} L — {r['coste']} €")
        else:
            st.info("Aún no has guardado rutas.")
        if st.button("🗑 Limpiar historial de la sesión actual"):
            st.session_state.historial_rutas = []
            st.session_state.ruta_datos = None
            st.success("Historial de rutas borrado.")
    else:
        st.info("Inicia sesión para ver tus historiales.")

# 2️⃣ Buscador de vehículos
with tabs[1]:
    st.subheader("Buscador de vehículos")
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
        # Guardado solo si usuario logueado
        if st.session_state.user:
            registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
            if registro not in st.session_state.historial:
                st.session_state.historial.append(registro)
                save_search(str(st.session_state.user.id), f"{marca} {modelo}", registro)

# 3️⃣ Planificador de rutas
with tabs[2]:
    st.subheader("Planificador de rutas")
    origen = st.selectbox("Ciudad de origen", options=ciudades_es, index=0)
    destino = st.selectbox("Ciudad de destino", options=ciudades_es, index=1)
    consumo = st.number_input("Consumo medio (L/100km)", value=6.5)
    precio = st.number_input("Precio combustible (€/L)", value=1.6)

    if st.button("Calcular ruta"):
        coords_origen = geocode_city(origen)
        coords_destino = geocode_city(destino)
        if coords_origen and coords_destino:
            ruta = get_route((coords_origen[1], coords_origen[0]), (coords_destino[1], coords_destino[0]))
            if ruta:
                distancia_km, duracion_min, coords_linea = ruta
                horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
                duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
                litros, coste = calcular_coste(distancia_km, consumo, precio)
                st.session_state.ruta_datos = {
                    "origen": origen, "destino": destino,
                    "coords_origen": coords_origen,
                    "coords_destino": coords_destino,
                    "coords_linea": coords_linea,
                    "distancia_km": distancia_km,
                    "duracion": duracion_str,
                    "litros": litros,
                    "coste": coste
                }
                # Guardado solo si usuario logueado
                if st.session_state.user:
                    registro_ruta = {
                        "origen": origen, "destino": destino,
                        "distancia_km": round(distancia_km,1),
                        "duracion": duracion_str,
                        "consumo_l": litros,
                        "coste": coste
                    }
                    if registro_ruta not in st.session_state.historial_rutas:
                        st.session_state.historial_rutas.append(registro_ruta)
                        save_route(str(st.session_state.user.id), origen, destino, distancia_km, duracion_str, litros, coste)
        else:
            st.error("No se pudo obtener la ubicación de una o ambas ciudades.")

    # Mostrar mapa
    if st.session_state.ruta_datos:
        datos = st.session_state.ruta_datos
        st.success(f"Distancia: {datos['distancia_km']:.1f} km — Duración: {datos['duracion']}")
        st.info(f"Consumo estimado: {datos['litros']} L — Coste estimado: {datos['coste']} €")
        m = folium.Map(location=datos["coords_origen"], zoom_start=6)
        folium.Marker(datos["coords_origen"], tooltip=f"Origen: {datos['origen']}", icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker(datos["coords_destino"], tooltip=f"Destino: {datos['destino']}", icon=folium.Icon(color="red", icon="stop")).add_to(m)
        folium.PolyLine([(lat, lon) for lon, lat in datos["coords_linea"]], color="blue", weight=5).add_to(m)
        st_folium(m, width=700, height=500)

# -----------------------------
# Footer
# -----------------------------
st.markdown("""
<footer style="text-align:center; padding:10px 0; border-top:1px solid #ccc; margin-top:20px;">
    © 2025 PreITV App. Todos los derechos reservados.
</footer>
""", unsafe_allow_html=True)
