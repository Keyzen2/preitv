import datetime
import streamlit as st
from streamlit_folium import st_folium
import folium

from services.api import get_makes, get_models
from services.routes import get_route, calcular_coste
from services.supabase_client import sign_in, sign_up, sign_out, save_search, save_route, load_user_data, supabase
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos
from utils.ciudades import ciudades_coords

# -----------------------------
# Configuración página y CSS
# -----------------------------
st.set_page_config(page_title="PreITV", page_icon="🚗", layout="wide")
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
    "ruta_datos": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# Header y Footer
# -----------------------------
def render_header():
    st.markdown(
        """
        <div style="text-align:center">
            <img src="https://raw.githubusercontent.com/usuario/repositorio/main/logo.png" width="120">
            <h1>PreITV</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_footer():
    st.markdown(
        """
        <hr>
        <p style='text-align:center;font-size:12px;color:gray;'>&copy; 2025 PreITV</p>
        """,
        unsafe_allow_html=True
    )

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
# Render panel de usuario
# -----------------------------
def render_user_panel():
    st.subheader(f"👋 Hola, {st.session_state.user.user_metadata.get('full_name', st.session_state.user.email)}")
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
# Función principal
# -----------------------------
def render_main_app():
    render_header()

    # Cargar historial de usuario si está logueado
    if st.session_state.user and not st.session_state.data_loaded:
        historial, historial_rutas = load_user_data(str(st.session_state.user.id))
        st.session_state.historial = historial
        st.session_state.historial_rutas = historial_rutas
        st.session_state.data_loaded = True

    # Tabs principales
    tabs = ["Vehículos", "Rutas"]
    if st.session_state.user:
        tabs += ["Historial de búsquedas", "Panel de usuario"]

    selected_tab = st.tabs(tabs)

    # -----------------------------
    # Vehículos
    # -----------------------------
    with selected_tab[0]:
        st.subheader("🚗 Buscador de vehículos")
        makes = get_makes()
        marca = st.selectbox("Marca", options=makes)
        modelos = get_models(marca) if marca else []
        modelo = st.selectbox("Modelo", options=modelos)
        anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year)
        km = st.number_input("Kilometraje", min_value=0, step=1000)
        combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

        if st.button("🔍 Buscar información"):
            st.session_state.checklist = recomendaciones_itv_detalladas(datetime.date.today().year-anio, km, combustible)
            registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
            st.success(f"Has seleccionado **{marca} {modelo}**")
            if st.session_state.user and registro not in st.session_state.historial:
                st.session_state.historial.append(registro)
                save_search(str(st.session_state.user.id), f"{marca} {modelo}", registro)
            elif not st.session_state.user:
                st.info("🔐 Regístrate para guardar tus búsquedas.")

        # Mostrar checklist
        if st.session_state.checklist:
            st.subheader("✅ Recomendaciones antes de la ITV")
            for tarea, cat in st.session_state.checklist:
                st.markdown(f"- **{cat}:** {tarea}")

    # -----------------------------
    # Rutas
    # -----------------------------
    with selected_tab[1]:
        st.subheader("🗺️ Planificador de ruta y coste")
        ciudad_origen = st.selectbox("Ciudad de origen", options=list(ciudades_coords.keys()))
        ciudad_destino = st.selectbox("Ciudad de destino", options=list(ciudades_coords.keys()))
        consumo = st.number_input("Consumo medio (L/100km)", value=6.5)
        precio = st.number_input("Precio combustible (€/L)", value=1.6)

        if st.button("Calcular ruta"):
            lat_o, lon_o = ciudades_coords[ciudad_origen]
            lat_d, lon_d = ciudades_coords[ciudad_destino]

            try:
                ruta = get_route((lon_o, lat_o), (lon_d, lat_d))
            except Exception as e:
                st.error(f"No se pudo calcular la ruta: {e}")
                ruta = None

            if ruta:
                distancia_km, duracion_min, coords_linea = ruta
                horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
                duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
                litros, coste = calcular_coste(distancia_km, consumo, precio)
                
                # Mostrar mapa con folium
                mapa = folium.Map(location=[lat_o, lon_o], zoom_start=6)
                folium.Marker([lat_o, lon_o], tooltip="Origen").add_to(mapa)
                folium.Marker([lat_d, lon_d], tooltip="Destino").add_to(mapa)
                folium.PolyLine(coords_linea, color="blue", weight=5, opacity=0.7).add_to(mapa)
                st_folium(mapa, width=700, height=450)

                # Mostrar resumen de ruta
                st.markdown(f"**{ciudad_origen} → {ciudad_destino}**")
                st.markdown(f"- Distancia: {distancia_km:.1f} km")
                st.markdown(f"- Duración: {duracion_str}")
                st.markdown(f"- Consumo estimado: {litros:.1f} L")
                st.markdown(f"- Coste aproximado: {coste:.2f} €")

                # Guardado solo para usuarios logueados
                if st.session_state.user:
                    registro_ruta = {
                        "origen": ciudad_origen,
                        "destino": ciudad_destino,
                        "distancia_km": round(distancia_km, 1),
                        "duracion": duracion_str,
                        "consumo_l": round(litros, 2),
                        "coste": round(coste, 2)
                    }
                    if registro_ruta not in st.session_state.historial_rutas:
                        st.session_state.historial_rutas.append(registro_ruta)
                        save_route(str(st.session_state.user.id), registro_ruta)
                else:
                    st.info("🔐 Regístrate para guardar tus rutas.")

    # -----------------------------
    # Historial de búsquedas (solo usuarios)
    # -----------------------------
    if st.session_state.user and len(tabs) > 2:
        with selected_tab[2]:
            st.subheader("📜 Historial de búsquedas")
            if st.session_state.historial:
                for i, r in enumerate(st.session_state.historial, 1):
                    st.markdown(f"**{i}. {r['marca']} {r['modelo']}** — {r['anio']} — {r['km']} km — {r['combustible']}")
            else:
                st.info("No hay búsquedas guardadas aún.")

            st.subheader("📍 Historial de rutas")
            if st.session_state.historial_rutas:
                for i, r in enumerate(st.session_state.historial_rutas, 1):
                    st.markdown(f"**{i}. {r['origen']} → {r['destino']}** — {r['distancia_km']} km — {r['duracion']} — {r['consumo_l']} L — {r['coste']} €")
            else:
                st.info("No hay rutas guardadas aún.")

    # -----------------------------
    # Panel de usuario
    # -----------------------------
    if st.session_state.user and len(tabs) > 3:
        with selected_tab[3]:
            render_user_panel()

    render_footer()

# -----------------------------
# Ejecutar app
# -----------------------------
if __name__ == "__main__":
    if not st.session_state.user:
        render_login_form()
    render_main_app()
