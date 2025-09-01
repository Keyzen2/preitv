import datetime
import streamlit as st
import folium
from streamlit_folium import st_folium

from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models
from services.routes import get_route, calcular_coste
from services.supabase_client import sign_in, sign_up, sign_out, save_search, save_route, load_user_data
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos
from utils.cities import ciudades_coords  # Coordenadas de ciudades de España

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
    # Obtenemos coordenadas desde ciudades_coords para evitar errores de conexión
    return ciudades_coords.get(city_name)

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
                        st.session_state.data_loaded = False  # Recargar historial
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

def render_user_panel():
    if not st.session_state.user:
        return
    user_email = getattr(st.session_state.user, "email", None)
    user_name = getattr(st.session_state.user, "user_metadata", {}).get("name", "")
    st.subheader(f"👋 Hola, {user_name or user_email}")

    with st.expander("⚙️ Configuración de cuenta", expanded=True):
        nuevo_nombre = st.text_input("Cambiar nombre", value=user_name)
        if st.button("Actualizar nombre"):
            if nuevo_nombre:
                try:
                    st.session_state.user.user_metadata["name"] = nuevo_nombre
                    st.success("Nombre actualizado correctamente")
                except Exception as e:
                    st.error(f"Error al actualizar nombre: {e}")
        nueva_pass = st.text_input("Nueva contraseña", type="password")
        if st.button("Actualizar contraseña"):
            if nueva_pass:
                st.success("Contraseña actualizada correctamente (simulada)")

    if st.button("Cerrar sesión"):
        sign_out()
        for k in defaults.keys():
            st.session_state[k] = defaults[k]
        st.experimental_rerun()  # Funciona en Streamlit >=1.18

# -----------------------------
# Render principal
# -----------------------------
def render_main_app():
    # Cargar historial si el usuario está logueado
    if st.session_state.user and not st.session_state.data_loaded:
        historial, historial_rutas = load_user_data(str(st.session_state.user.id))
        st.session_state.historial = historial
        st.session_state.historial_rutas = historial_rutas
        st.session_state.data_loaded = True

    # Header con logo
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 20px;'>
            <img src='https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/logo.png' width='150'>
        </div>
        """, unsafe_allow_html=True
    )

    # Tabs
    tabs = ["Vehículos", "Rutas"]
    if st.session_state.user:
        tabs.append("Historial de búsquedas")
        tabs.append("Panel de usuario")
    selected_tab = st.tabs(tabs)

    # -----------------------------
    # Vehículos
    # -----------------------------
    with selected_tab[0]:
        st.subheader("🚗 Buscador de Vehículos")
        makes = get_makes()
        marca = st.selectbox("Marca", options=makes)
        modelos = get_models(marca) if marca else []
        modelo = st.selectbox("Modelo", options=modelos)
        anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year)
        km = st.number_input("Kilometraje", min_value=0, step=1000)
        combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])
        if st.button("🔍 Buscar información"):
            st.session_state.checklist = recomendaciones_itv_detalladas(anio, km, combustible)
            registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
            if st.session_state.user:
                if registro not in st.session_state.historial:
                    st.session_state.historial.append(registro)
                    save_search(str(st.session_state.user.id), f"{marca} {modelo}", registro)
            else:
                st.info("Regístrate para guardar tus búsquedas")

        if st.session_state.historial:
            st.subheader("📜 Historial vehículos consultados")
            for item in st.session_state.historial:
                st.markdown(f"**{item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")

        if st.session_state.checklist:
            st.subheader("✅ Recomendaciones ITV")
            for tarea, cat in st.session_state.checklist:
                st.markdown(f"- **{cat}:** {tarea}")

    # -----------------------------
# Rutas
# -----------------------------
with selected_tab[1]:
    st.subheader("🗺️ Planificador de ruta y coste")
    origen = st.selectbox("Ciudad de origen", options=list(ciudades_coords.keys()))
    destino = st.selectbox("Ciudad de destino", options=list(ciudades_coords.keys()))
    consumo = st.number_input("Consumo medio (L/100km)", value=6.5)
    precio = st.number_input("Precio combustible (€/L)", value=1.6)

    if st.button("Calcular ruta"):
        coords_origen = geocode_city(origen)
        coords_destino = geocode_city(destino)
        if coords_origen and coords_destino:
            ruta = get_route(coords_origen, coords_destino)
            if ruta:
                distancia_km, duracion_min, coords_linea = ruta
                horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
                duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
                litros, coste = calcular_coste(distancia_km, consumo, precio)

                st.markdown(f"**{origen} → {destino}** — {distancia_km:.1f} km — {duracion_str} — {litros:.2f} L — {coste:.2f} €")

                # Mapa
                m = folium.Map(location=coords_origen, zoom_start=6)
                folium.Marker(location=coords_origen, tooltip="Origen").add_to(m)
                folium.Marker(location=coords_destino, tooltip="Destino").add_to(m)
                folium.PolyLine(coords_linea, color="blue", weight=5, opacity=0.7).add_to(m)
                st_folium(m, width=700, height=500)

                # Guardado solo para usuarios logueados
                if st.session_state.user:
                    registro_ruta = {
                        "origen": origen,
                        "destino": destino,
                        "distancia_km": round(distancia_km, 1),
                        "duracion": duracion_str,
                        "consumo_l": round(litros, 2),
                        "coste": round(coste, 2)
                    }
                    if registro_ruta not in st.session_state.historial_rutas:
                        st.session_state.historial_rutas.append(registro_ruta)
                        save_route(
                            str(st.session_state.user.id),
                            origen, destino,
                            distancia_km, duracion_str, litros, coste
                        )
                else:
                    st.info("Regístrate para guardar tus rutas")
            else:
                st.error("No se pudo calcular la ruta")
        else:
            st.error("No se pudo obtener la ubicación de una o ambas ciudades.")

# -----------------------------
# Historial de búsquedas (solo usuarios logueados)
# -----------------------------
if st.session_state.user:
    with selected_tab[2]:
        st.subheader("📜 Historial de búsquedas")
        if st.session_state.historial:
            st.markdown("**Vehículos consultados:**")
            for i, item in enumerate(st.session_state.historial, start=1):
                st.markdown(f"{i}. {item['marca']} {item['modelo']} — {item['anio']} — {item['km']} km — {item['combustible']}")
        else:
            st.info("No tienes historial de vehículos aún.")

        if st.session_state.historial_rutas:
            st.markdown("**Rutas consultadas:**")
            for i, r in enumerate(st.session_state.historial_rutas, start=1):
                st.markdown(
                    f"{i}. {r['origen']} → {r['destino']} — {r['distancia_km']} km — {r['duracion']} — {r['consumo_l']} L — {r['coste']} €"
                )
        else:
            st.info("No tienes historial de rutas aún.")

# -----------------------------
# Panel de usuario
# -----------------------------
if st.session_state.user:
    with selected_tab[3]:
        render_user_panel()

# -----------------------------
# Footer
# -----------------------------
st.markdown(
    """
    <div style='text-align: center; padding: 20px 0; margin-top: 50px; border-top: 1px solid #eee;'>
        © 2025 PreITV
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Ejecutar app
# -----------------------------
if __name__ == "__main__":
    render_main_app()
