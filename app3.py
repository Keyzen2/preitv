import streamlit as st
from supabase import create_client, Client
from utils.helpers import (
    local_css,
    recomendaciones_itv_detalladas,
    resumen_proximos_mantenimientos,
    geocode_city,
)
from utils.ciudades_coords import ciudades_coords
from utils.database import supabase_client
from admin_panel import render_admin_panel

# -----------------------------
# Configuración inicial
# -----------------------------
st.set_page_config(
    page_title="PreITV",
    layout="wide",
    initial_sidebar_state="expanded"
)
local_css("styles.css")

# -----------------------------
# Sidebar Login
# -----------------------------
def login_sidebar():
    st.sidebar.header("🔐 Iniciar sesión o registrarse")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Iniciar sesión"):
        user = supabase_client.auth.sign_in_with_password({"email": email, "password": password})
        if user:
            st.session_state['user'] = user
            st.success(f"Bienvenido {email}")
        else:
            st.error("Usuario o contraseña incorrecta")
    if st.sidebar.button("Registrarse"):
        st.session_state['register_mode'] = True

# -----------------------------
# Funciones auxiliares para sesión
# -----------------------------
def logout():
    for key in st.session_state.keys():
        st.session_state[key] = None
    st.session_state['user'] = None
    st.experimental_rerun()

# -----------------------------
# Tabs principales
# -----------------------------
def render_main_app():
    if 'user' not in st.session_state or not st.session_state['user']:
        login_sidebar()
        st.title("🚗 PreITV")
        st.info("Puedes explorar la app, pero para guardar búsquedas debes iniciar sesión.")
    else:
        user = st.session_state['user']
        tabs = ["Vehículos", "Rutas", "Historial de búsquedas", "Panel de usuario", "Panel administrador"]
        selected_tab = st.tabs(tabs)

        # -----------------------------
        # Tab Vehículos
        # -----------------------------
        with selected_tab[0]:
            st.header("🚗 Vehículos")
            marca = st.selectbox("Marca", ["Seat", "Volkswagen", "Renault"])
            modelo = st.text_input("Modelo")
            anio = st.number_input("Año", 1990, 2025, 2020)
            km = st.number_input("Km", 0, 1000000, 50000)
            combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])
            if st.button("Calcular recomendaciones"):
                recomendaciones = recomendaciones_itv_detalladas(anio, km, combustible)
                st.table(recomendaciones)
                st.success(resumen_proximos_mantenimientos(km))

        # -----------------------------
        # Tab Rutas
        # -----------------------------
        with selected_tab[1]:
            st.header("🗺️ Planificador de ruta y coste")
            origen = st.selectbox("Ciudad de origen", list(ciudades_coords.keys()))
            destino = st.selectbox("Ciudad de destino", list(ciudades_coords.keys()))
            consumo = st.number_input("Consumo medio (L/100km)", 0.0, 30.0, 6.5)
            precio_combustible = st.number_input("Precio combustible (€/L)", 0.0, 5.0, 1.75)
            if st.button("Calcular ruta"):
                coord_origen = geocode_city(origen)
                coord_destino = geocode_city(destino)
                if coord_origen and coord_destino:
                    distancia_km = 200  # placeholder, calcular real
                    duracion_h = distancia_km / 80  # placeholder velocidad media
                    consumo_total = distancia_km * consumo / 100
                    coste = consumo_total * precio_combustible
                    st.markdown(f"**Ruta:** {origen} → {destino}")
                    st.markdown(f"**Distancia:** {distancia_km} km")
                    st.markdown(f"**Duración aproximada:** {duracion_h:.2f} h")
                    st.markdown(f"**Consumo estimado:** {consumo_total:.2f} L")
                    st.markdown(f"**Coste estimado:** {coste:.2f} €")

        # -----------------------------
        # Tab Historial de búsquedas
        # -----------------------------
        with selected_tab[2]:
            st.header("📜 Historial de búsquedas")
            historial = supabase_client.table("routes").select("*").eq("user_id", user['id']).execute()
            st.table(historial.data if historial.data else [])

        # -----------------------------
        # Tab Panel de usuario
        # -----------------------------
        with selected_tab[3]:
            st.header(f"👋 Hola, {user['email']}")
            if st.button("Cerrar sesión"):
                logout()

        # -----------------------------
        # Tab Administrador
        # -----------------------------
        with selected_tab[4]:
            render_admin_panel(supabase_client)

# -----------------------------
# Ejecutar app
# -----------------------------
render_main_app()
