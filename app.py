import streamlit as st
from supabase import create_client, Client
from io import BytesIO
from PIL import Image
import base64
import json

from utils.helpers import (
    local_css,
    recomendaciones_itv_detalladas,
    resumen_proximos_mantenimientos
)
from utils.cities import ciudades_coords

# -----------------------------
# Configuración Supabase
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Cargar CSS
# -----------------------------
local_css("styles.css")

# -----------------------------
# Funciones auxiliares
# -----------------------------
def geocode_city(city_name: str):
    """Devuelve coordenadas de ciudades_coords"""
    coords = ciudades_coords.get(city_name)
    if coords:
        return coords
    else:
        st.error(f"No se encontraron coordenadas para {city_name}")
    return None

def guardar_busqueda(usuario_id, busqueda):
    """Guardar búsqueda solo para usuarios logueados"""
    if usuario_id:
        supabase.table("routes").insert(busqueda).execute()

# -----------------------------
# Funciones de login
# -----------------------------
def login(email, password):
    try:
        user = supabase.auth.sign_in(email=email, password=password)
        if user:
            st.session_state["usuario"] = user
            st.success("Inicio de sesión correcto")
    except Exception as e:
        st.error(f"Error al iniciar sesión: {e}")

def logout():
    for k in list(st.session_state.keys()):
        st.session_state[k] = None
    st.session_state["usuario"] = None

# -----------------------------
# Panel de administrador
# -----------------------------
def render_admin_panel():
    if "usuario" not in st.session_state or st.session_state["usuario"] is None:
        st.warning("Acceso restringido a administradores")
        return
    st.header("⚙️ Panel de Administrador")
    # Aquí puedes integrar estadísticas, listado de usuarios, subida de logo
    st.info("Panel de admin funcionalidad aún pendiente de completarse según necesidades")

# -----------------------------
# Renderizado principal
# -----------------------------
def render_user_panel():
    usuario = st.session_state.get("usuario")
    if not usuario:
        st.info("🔐 Inicia sesión para guardar tus búsquedas y acceder al historial.")
    st.title("PreITV")
    st.image("logo.png", width=200)
    tabs = st.tabs(["Vehículos", "Rutas", "Panel Admin"])
    
    with tabs[0]:
        st.subheader("🚗 Vehículos")
        # Formulario de búsqueda de vehículos y recomendaciones ITV
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        edad = st.number_input("Edad del vehículo (años)", min_value=0, max_value=30, value=5)
        km = st.number_input("Kilometraje (km)", min_value=0, value=50000)
        combustible = st.selectbox("Combustible", ["Gasolina", "Diesel", "Híbrido", "Eléctrico"])
        if st.button("Obtener recomendaciones"):
            checklist = recomendaciones_itv_detalladas(edad, km, combustible)
            for item, categoria in checklist:
                st.markdown(f"- **{categoria}**: {item}")
            st.markdown(resumen_proximos_mantenimientos(km))

    with tabs[1]:
        st.subheader("🗺️ Rutas")
        origen = st.selectbox("Ciudad de origen", list(ciudades_coords.keys()))
        destino = st.selectbox("Ciudad de destino", list(ciudades_coords.keys()))
        if st.button("Calcular ruta"):
            coord_origen = geocode_city(origen)
            coord_destino = geocode_city(destino)
            if coord_origen and coord_destino:
                distancia_km = 100  # placeholder cálculo
                consumo_l = 7       # placeholder
                coste = consumo_l * 1.9  # placeholder
                st.markdown(f"**{origen} → {destino}** — {distancia_km} km — {consumo_l} L — {coste:.2f} €")
                if "usuario" in st.session_state and st.session_state["usuario"]:
                    guardar_busqueda(st.session_state["usuario"]["id"], {
                        "origen": origen,
                        "destino": destino,
                        "distancia_km": distancia_km,
                        "consumo_l": consumo_l,
                        "coste": coste
                    })

    with tabs[2]:
        render_admin_panel()

# -----------------------------
# Login lateral
# -----------------------------
if "usuario" not in st.session_state or st.session_state["usuario"] is None:
    with st.sidebar:
        st.header("🔐 Iniciar sesión o registrarse")
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        if st.button("Iniciar sesión"):
            login(email, password)
        if st.button("Registrarse"):
            st.info("Registro pendiente de implementación")
else:
    if st.sidebar.button("Cerrar sesión"):
        logout()

# -----------------------------
# Ejecutar app
# -----------------------------
render_user_panel()

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.markdown("© 2025 PreITV")
