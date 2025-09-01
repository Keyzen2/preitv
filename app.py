import streamlit as st
from supabase import create_client
from utils.helpers import (
    local_css,
    recomendaciones_itv_detalladas,
    resumen_proximos_mantenimientos,
    geocode_city,
)
from utils.ciudades_coords import ciudades_coords
from datetime import datetime

# -----------------------------
# Configuración Supabase
# -----------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# -----------------------------
# Inicializar sesión
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "historial" not in st.session_state:
    st.session_state.historial = []

# -----------------------------
# Login lateral
# -----------------------------
def login():
    st.sidebar.title("🔐 Iniciar sesión")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.sidebar.success("¡Login exitoso!")
        else:
            st.sidebar.error("Error al iniciar sesión")

# -----------------------------
# Logout
# -----------------------------
def logout():
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.historial = []
    st.success("Has cerrado sesión correctamente.")

# -----------------------------
# Panel de administrador
# -----------------------------
def render_admin_panel():
    st.header("⚙️ Panel de administrador")
    st.subheader("📊 Estadísticas de la app")
    users_count = len(supabase.table("users").select("*").execute().data)
    vehiculos_count = len(supabase.table("vehiculos").select("*").execute().data)
    rutas_count = len(supabase.table("routes").select("*").execute().data)
    st.metric("Usuarios", users_count)
    st.metric("Vehículos", vehiculos_count)
    st.metric("Rutas calculadas", rutas_count)

    st.subheader("👥 Listado de usuarios")
    users = supabase.table("users").select("*").execute().data
    for u in users:
        st.markdown(f"**{u['email']}** — Rol: {u.get('role','usuario')}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Eliminar {u['email']}", key=f"del_{u['id']}"):
                supabase.table("users").delete().eq("id", u["id"]).execute()
                st.experimental_rerun()
        with col2:
            if st.button(f"Promover {u['email']} a admin", key=f"admin_{u['id']}"):
                supabase.table("users").update({"role": "admin"}).eq("id", u["id"]).execute()
                st.success(f"{u['email']} ahora es admin")

# -----------------------------
# Tabs de la app
# -----------------------------
def render_main_app():
    st.image("assets/logo.png", width=200)
    st.title("🚗 PreITV")

    tabs = ["Vehículos", "Rutas"]
    if st.session_state.logged_in:
        tabs.append("Historial de búsquedas")
        tabs.append("Panel de usuario")
    if st.session_state.user_email == "admin@example.com":  # Ajusta según tu lógica
        tabs.append("Panel de administrador")

    selected_tab = st.tabs(tabs)

    # -----------------------------
    # Tab Vehículos
    # -----------------------------
    with selected_tab[0]:
        st.subheader("🚗 Vehículos")
        # Contenido de vehículos
        st.info("Aquí se mostrarán vehículos disponibles y opciones de búsqueda.")

    # -----------------------------
    # Tab Rutas
    # -----------------------------
    with selected_tab[1]:
        st.subheader("🗺️ Planificador de rutas y costes")
        origen = st.selectbox("Ciudad de origen", list(ciudades_coords.keys()))
        destino = st.selectbox("Ciudad de destino", list(ciudades_coords.keys()))
        consumo = st.number_input("Consumo medio (L/100km)", min_value=1.0, max_value=30.0, value=6.5)
        precio_combustible = st.number_input("Precio combustible (€/L)", min_value=1.0, max_value=3.0, value=1.75)

        if st.button("Calcular ruta"):
            coords_origen = geocode_city(origen, ciudades_coords)
            coords_destino = geocode_city(destino, ciudades_coords)
            if coords_origen and coords_destino:
                distancia_km = 500  # Simulación, puedes reemplazar con cálculo real
                duracion_h = round(distancia_km / 90, 2)
                coste = round(distancia_km * consumo / 100 * precio_combustible, 2)
                st.markdown(f"**{origen} → {destino}** — {distancia_km} km — {duracion_h} h — {consumo} L — {coste} €")

                # Guardado solo para usuarios logueados
                if st.session_state.logged_in:
                    registro = {
                        "origen": origen,
                        "destino": destino,
                        "distancia_km": distancia_km,
                        "duracion_h": duracion_h,
                        "consumo_l": consumo,
                        "coste": coste,
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.historial.append(registro)

    # -----------------------------
    # Tab Historial de búsquedas
    # -----------------------------
    if st.session_state.logged_in:
        with selected_tab[2]:
            st.subheader("📜 Historial de búsquedas")
            for i, r in enumerate(st.session_state.historial, 1):
                st.markdown(f"**{i}. {r['origen']} → {r['destino']}** — {r['distancia_km']} km — {r['duracion_h']} h — {r['consumo_l']} L — {r['coste']} €")

        # Panel de usuario
        with selected_tab[3]:
            st.subheader(f"👋 Hola, {st.session_state.user_email}")
            if st.button("Cerrar sesión"):
                logout()

    # -----------------------------
    # Panel de admin
    # -----------------------------
    if st.session_state.logged_in and st.session_state.user_email == "admin@example.com":
        with selected_tab[-1]:
            render_admin_panel()

    # -----------------------------
    # Footer
    # -----------------------------
    st.markdown("---")
    st.markdown("© 2025 PreITV")

# -----------------------------
# Ejecución
# -----------------------------
login()
render_main_app()
