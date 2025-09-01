import streamlit as st
from helpers import local_css, geocode_city, resumen_proximos_mantenimientos
from database import get_supabase_client
from admin_panel import render_admin_panel

# -----------------------------
# Inicializar session_state
# -----------------------------
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'historial' not in st.session_state:
    st.session_state['historial'] = []
if 'update' not in st.session_state:
    st.session_state['update'] = False

# -----------------------------
# Login lateral
# -----------------------------
def login():
    st.sidebar.title("🔐 Iniciar sesión")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        # Validación simplificada (reemplazar con Supabase)
        if email and password:
            st.session_state['user'] = email
        else:
            st.sidebar.error("Credenciales incorrectas")

# -----------------------------
# Main App
# -----------------------------
def render_main_app():
    supabase = get_supabase_client()
    
    # Login
    if st.session_state['user'] is None:
        login()
        st.stop()

    # Tabs principales
    tabs = ["Vehículos", "Rutas", "Historial", "Panel Admin"]
    selected_tab = st.tabs(tabs)

    with selected_tab[0]:
        st.subheader("🚗 Vehículos")
        # contenido de vehículos

    with selected_tab[1]:
        st.subheader("🗺️ Rutas")
        origen = st.text_input("Ciudad de origen")
        destino = st.text_input("Ciudad de destino")
        if st.button("Calcular ruta"):
            coord_origen = geocode_city(origen)
            coord_destino = geocode_city(destino)
            if coord_origen and coord_destino:
                st.success(f"Ruta: {coord_origen} → {coord_destino}")

    with selected_tab[2]:
        st.subheader("📜 Historial de búsquedas")
        for h in st.session_state['historial']:
            st.write(h)

    with selected_tab[3]:
        st.subheader("👤 Panel de Admin")
        render_admin_panel(supabase)

render_main_app()
