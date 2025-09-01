import datetime
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, search_workshops
from services.routes import get_route, calcular_coste
from services.supabase_client import sign_in, sign_up, sign_out, save_search, save_route, load_user_data, supabase
from admin_panel import render_admin_panel
from supabase import create_client, Client
from utils.helpers import (
    local_css,
    resumen_proximos_mantenimientos,
    recomendaciones_itv_detalladas,
    ciudades_coords
)

# -----------------------------
# Configuración de Supabase
# -----------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# -----------------------------
# Estilos y Header/Footer
# -----------------------------
local_css("style.css")  # archivo CSS en la raíz

def render_header():
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:20px;">
            <img src="https://raw.githubusercontent.com/usuario/repositorio/main/logo.png" width="150"/>
            <h1>PreITV</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_footer():
    st.markdown(
        """
        <div style="text-align:center; margin-top:20px;">
            <hr/>
            <p>© 2025 PreITV</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# Funciones auxiliares
# -----------------------------
def geocode_city(city_name: str):
    """Devuelve las coordenadas desde ciudades_coords en lugar de llamar a la API externa"""
    coords = ciudades_coords.get(city_name)
    if coords:
        return coords
    else:
        st.error(f"No se encontraron coordenadas para {city_name}")
        return None

def get_users():
    """Obtiene listado de usuarios desde Supabase"""
    response = supabase.table("users").select("*").execute()
    if response.error:
        st.error("Error al obtener usuarios")
        return []
    return response.data

def get_statistics():
    """Obtiene estadísticas básicas de la app"""
    users_count = supabase.table("users").select("id", count="exact").execute().count
    vehiculos_count = supabase.table("vehiculos").select("id", count="exact").execute().count
    rutas_count = supabase.table("routes").select("id", count="exact").execute().count
    return {"usuarios": users_count, "vehiculos": vehiculos_count, "rutas": rutas_count}

# -----------------------------
# Autenticación
# -----------------------------
def login():
    if "user" not in st.session_state:
        st.session_state.user = None
    if st.session_state.user is None:
        st.sidebar.header("🔐 Iniciar sesión")
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Contraseña", type="password")
        if st.sidebar.button("Iniciar sesión"):
            resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if resp.user:
                st.session_state.user = resp.user
                st.experimental_rerun()
            else:
                st.sidebar.error("Error al iniciar sesión")
        st.stop()

def logout():
    st.session_state.user = None
    st.experimental_rerun()

# -----------------------------
# Panel de usuario
# -----------------------------
def render_user_panel():
    st.header(f"👋 Hola, {st.session_state.user.email}")
    if st.button("Cerrar sesión"):
        logout()
    tabs = st.tabs(["Vehículos", "Rutas", "Historial de búsquedas"])
    with tabs[0]:
        st.subheader("⚙️ Configuración de vehículo")
        # Aquí va el formulario de vehículo
    with tabs[1]:
        render_routes_tab()
    with tabs[2]:
        st.subheader("📜 Historial de búsquedas")
        if "historial" not in st.session_state:
            st.session_state.historial = []
        for r in st.session_state.historial:
            st.markdown(f"**{r['origen']} → {r['destino']}** — {r['distancia_km']} km — {r['duracion']} — {r['consumo_l']} L — {r['coste']} €")

# -----------------------------
# Tab Rutas
# -----------------------------
def render_routes_tab():
    st.subheader("🗺️ Planificador de ruta y coste")
    origen = st.selectbox("Ciudad de origen", list(ciudades_coords.keys()))
    destino = st.selectbox("Ciudad de destino", list(ciudades_coords.keys()))
    consumo = st.number_input("Consumo medio (L/100km)", value=6.5)
    precio = st.number_input("Precio combustible (€/L)", value=1.8)

    if st.button("Calcular ruta"):
        coor_origen = geocode_city(origen)
        coor_destino = geocode_city(destino)
        if coor_origen and coor_destino:
            # Simulación de cálculo de distancia y tiempo
            distancia_km = 250
            duracion = "3h 15min"
            coste = round(distancia_km * consumo / 100 * precio, 2)
            consumo_l = round(distancia_km * consumo / 100, 2)
            st.success(f"Ruta {origen} → {destino} calculada")
            st.markdown(f"**Distancia:** {distancia_km} km | **Duración:** {duracion} | **Consumo:** {consumo_l} L | **Coste:** {coste} €")
            if "historial" not in st.session_state:
                st.session_state.historial = []
            st.session_state.historial.append({
                "origen": origen,
                "destino": destino,
                "distancia_km": distancia_km,
                "duracion": duracion,
                "consumo_l": consumo_l,
                "coste": coste
            })

# -----------------------------
# Panel de administrador
# -----------------------------
def render_admin_panel():
    st.header("⚙️ Panel de administrador")
    stats = get_statistics()
    st.metric("Usuarios registrados", stats["usuarios"])
    st.metric("Vehículos registrados", stats["vehiculos"])
    st.metric("Rutas calculadas", stats["rutas"])
    st.markdown("---")
    st.subheader("👥 Listado de usuarios")
    users = get_users()
    if users:
        for u in users:
            st.markdown(f"**{u['email']}** — Rol: {u.get('role', 'usuario')}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Eliminar {u['email']}", key=f"del_{u['id']}"):
                    supabase.table("users").delete().eq("id", u["id"]).execute()
                    st.experimental_rerun()
            with col2:
                if st.button(f"Promover {u['email']} a admin", key=f"admin_{u['id']}"):
                    supabase.table("users").update({"role": "admin"}).eq("id", u["id"]).execute()
                    st.success(f"{u['email']} ahora es admin")
                    st.experimental_rerun()
    else:
        st.info("No hay usuarios registrados")

# -----------------------------
# Main App
# -----------------------------
def render_main_app():
    render_header()
    login()
    if st.session_state.user:
        if st.session_state.user.role == "admin":
            render_admin_panel()
        else:
            render_user_panel()
    render_footer()

if __name__ == "__main__":
    render_main_app()
