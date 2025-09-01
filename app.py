import datetime
import streamlit as st
from streamlit_folium import st_folium
import folium
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, search_workshops
from services.routes import get_route, calcular_coste
from services.supabase_client import sign_in, sign_up, sign_out, save_search, save_route, load_user_data, supabase
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos
from utils.ciudades_coords import ciudades_coords

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
    "ruta_datos": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# Funciones auxiliares
# -----------------------------
def geocode_city(city_name: str):
    """Devuelve coordenadas desde ciudades_coords"""
    coords = ciudades_coords.get(city_name)
    if coords:
        return coords
    else:
        st.error(f"No se encontraron coordenadas para {city_name}")
    return None

# -----------------------------
# Login / Registro
# -----------------------------
def render_login():
    st.sidebar.header("🔐 Iniciar sesión")
    tab_login, tab_signup = st.tabs(["Login", "Registro"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        if st.button("Entrar"):
            if not email or not password:
                st.warning("Introduce email y contraseña")
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
                st.warning("Introduce email y contraseña")
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
    st.subheader(f"👋 Hola, {st.session_state.user.user_metadata.get('name', st.session_state.user.email)}")
    with st.expander("⚙️ Configuración de cuenta", expanded=True):
        nuevo_nombre = st.text_input("Cambiar nombre", value=st.session_state.user.user_metadata.get("name", ""))
        nueva_pass = st.text_input("Nueva contraseña", type="password")
        if st.button("Actualizar nombre"):
            if nuevo_nombre:
                try:
                    supabase.auth.update_user({"data": {"name": nuevo_nombre}})
                    st.session_state.user.user_metadata["name"] = nuevo_nombre
                    st.success("Nombre actualizado")
                except Exception as e:
                    st.error(f"No se pudo actualizar nombre: {e}")
        if st.button("Actualizar contraseña"):
            if nueva_pass:
                try:
                    supabase.auth.update_user({"password": nueva_pass})
                    st.success("Contraseña actualizada")
                except Exception as e:
                    st.error(f"No se pudo actualizar contraseña: {e}")
        if st.button("Cerrar sesión"):
            sign_out()
            for k in st.session_state.keys():
                st.session_state[k] = None
            st.experimental_rerun()

# -----------------------------
# Panel de admin
# -----------------------------
def render_admin_panel():
    st.subheader("🛠️ Panel de Administrador")
    # Listado de usuarios
    users = supabase.table("users").select("*").execute().data
    st.write("Usuarios registrados:")
    for u in users:
        st.markdown(f"- {u['email']} ({u.get('role','user')})")
    # Subir logo
    uploaded_logo = st.file_uploader("Subir logo de la web", type=["png","jpg"])
    if uploaded_logo:
        with open("assets/logo.png", "wb") as f:
            f.write(uploaded_logo.getbuffer())
        st.success("Logo actualizado")

# -----------------------------
# App principal
# -----------------------------
def render_main_app():
    # Header
    st.markdown(f"<h1 style='text-align:center'>{APP_TITLE}</h1>", unsafe_allow_html=True)
    st.image("assets/logo.png", width=150)

    # Tabs
    tabs = ["Vehículos", "Rutas"]
    if st.session_state.user:
        tabs += ["Historial de búsquedas", "Panel de usuario"]
        if st.session_state.user.user_metadata.get("role") == "admin":
            tabs += ["Panel de administrador"]

    selected_tab = st.tabs(tabs)

    # -----------------------------
    # Tab Vehículos
    # -----------------------------
    with selected_tab[0]:
        st.subheader("🚗 Buscador de Vehículos")
        makes = get_makes()
        marca = st.selectbox("Marca", options=makes)
        modelos = get_models(marca) if marca else []
        modelo = st.selectbox("Modelo", options=modelos)
        anio = st.number_input("Año", min_value=1900, max_value=datetime.date.today().year)
        km = st.number_input("Kilometraje", min_value=0, step=1000)
        combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

        if st.button("🔍 Buscar información"):
            st.session_state.checklist = recomendaciones_itv_detalladas(datetime.date.today().year - anio, km, combustible)
            st.success(f"Buscando información de {marca} {modelo}")
            if st.session_state.user:
                registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
                st.session_state.historial.append(registro)
                save_search(str(st.session_state.user.id), f"{marca} {modelo}", registro)
            else:
                st.info("Registrate para guardar tus búsquedas")

        # Mostrar checklist
        if st.session_state.checklist:
            st.subheader("✅ Recomendaciones ITV")
            for t, c in st.session_state.checklist:
                st.markdown(f"- **{c}:** {t}")

    # -----------------------------
    # Tab Rutas
    # -----------------------------
    with selected_tab[1]:
        st.subheader("🗺️ Planificador de rutas")
        origen_nombre = st.selectbox("Ciudad de origen", options=list(ciudades_coords.keys()), index=list(ciudades_coords.keys()).index("Almería"))
        destino_nombre = st.selectbox("Ciudad de destino", options=list(ciudades_coords.keys()), index=list(ciudades_coords.keys()).index("Sevilla"))
        consumo = st.number_input("Consumo medio (L/100km)", value=6.5)
        precio = st.number_input("Precio combustible (€/L)", value=1.6)

        if st.button("Calcular ruta"):
            coords_origen = geocode_city(origen_nombre)
            coords_destino = geocode_city(destino_nombre)
            if coords_origen and coords_destino:
                lat_o, lon_o = coords_origen
                lat_d, lon_d = coords_destino
                # Obtener ruta (función interna)
                ruta = get_route((lat_o, lon_o), (lat_d, lon_d))
                if ruta:
                    distancia_km, duracion_min, coords_linea = ruta
                    horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
                    duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
                    litros, coste = calcular_coste(distancia_km, consumo, precio)

                    st.markdown(f"**Ruta:** {origen_nombre} → {destino_nombre}")
                    st.markdown(f"- Distancia: {distancia_km:.2f} km")
                    st.markdown(f"- Duración: {duracion_str}")
                    st.markdown(f"- Consumo estimado: {litros:.2f} L")
                    st.markdown(f"- Coste estimado: {coste:.2f} €")

                    # Mostrar mapa
                    mapa = folium.Map(location=[lat_o, lon_o], zoom_start=6)
                    folium.Marker(location=[lat_o, lon_o], tooltip="Origen").add_to(mapa)
                    folium.Marker(location=[lat_d, lon_d], tooltip="Destino").add_to(mapa)
                    folium.PolyLine(coords_linea, color="blue", weight=5, opacity=0.7).add_to(mapa)
                    st_folium(mapa, width=700, height=400)

                    # Guardado solo para usuarios logueados
                    if st.session_state.user:
                        registro_ruta = {
                            "origen": origen_nombre,
                            "destino": destino_nombre,
                            "distancia_km": distancia_km,
                            "duracion": duracion_str,
                            "consumo_l": litros,
                            "coste": coste,
                            "fecha": datetime.datetime.now().isoformat()
                        }
                        st.session_state.historial_rutas.append(registro_ruta)
                        save_route(str(st.session_state.user.id), registro_ruta)
                    else:
                        st.info("Regístrate para guardar tus rutas.")
                else:
                    st.error("No se pudo calcular la ruta. Verifica las coordenadas.")
            else:
                st.error("No se pudo obtener las coordenadas de origen o destino.")

    # -----------------------------
    # Tab Historial de búsquedas
    # -----------------------------
    if st.session_state.user and "Historial de búsquedas" in tabs:
        with selected_tab[tabs.index("Historial de búsquedas")]:
            st.subheader("📜 Historial de búsquedas")
            if st.session_state.historial:
                for idx, r in enumerate(st.session_state.historial, 1):
                    st.markdown(f"**{idx}. {r['marca']} {r['modelo']}** — {r['anio']} — {r['km']} km — {r['combustible']}")
            else:
                st.info("No tienes búsquedas guardadas.")

            st.subheader("🗺️ Historial de rutas")
            if st.session_state.historial_rutas:
                for idx, r in enumerate(st.session_state.historial_rutas, 1):
                    st.markdown(f"**{idx}. {r['origen']} → {r['destino']}** — {r['distancia_km']:.2f} km — {r['duracion']} — {r['consumo_l']:.2f} L — {r['coste']:.2f} €")
            else:
                st.info("No tienes rutas guardadas.")

    # -----------------------------
    # Tab Panel de usuario
    # -----------------------------
    if st.session_state.user and "Panel de usuario" in tabs:
        with selected_tab[tabs.index("Panel de usuario")]:
            render_user_panel()

    # -----------------------------
    # Tab Panel de administrador
    # -----------------------------
    if st.session_state.user and st.session_state.user.user_metadata.get("role") == "admin" and "Panel de administrador" in tabs:
        with selected_tab[tabs.index("Panel de administrador")]:
            render_admin_panel()

    # Footer
    st.markdown("<hr><p style='text-align:center'>© 2025 PreITV</p>", unsafe_allow_html=True)

# -----------------------------
# Ejecución principal
# -----------------------------
if __name__ == "__main__":
    render_login()
    render_main_app()
