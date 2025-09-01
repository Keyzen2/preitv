import datetime
import streamlit as st
import folium
from streamlit_folium import st_folium

from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, search_workshops
from services.routes import get_route, calcular_coste
from services.supabase_client import sign_in, sign_up, sign_out, save_search, save_route, load_user_data
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos
from utils.ciudades_coords import ciudades_coords, ciudades_es

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
# Header
# -----------------------------
def render_header():
    st.markdown(
        f"""
        <div style='text-align:center'>
            <img src='https://raw.githubusercontent.com/tu_usuario/tu_repo/main/logo.png' width='120'/>
            <h1>{APP_TITLE}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# Footer
# -----------------------------
def render_footer():
    st.markdown(
        "<hr><p style='text-align:center;font-size:12px;'>© 2025 PreITV</p>",
        unsafe_allow_html=True
    )

# -----------------------------
# Funciones auxiliares
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
    if not st.session_state.user:
        return
    st.subheader(f"👋 Hola, {st.session_state.user.user_metadata.get('full_name', st.session_state.user.email)}")
    with st.expander("⚙️ Configuración de cuenta", expanded=True):
        # Cambiar nombre
        nuevo_nombre = st.text_input("Cambiar nombre", value=st.session_state.user.user_metadata.get("full_name",""))
        if st.button("Actualizar nombre"):
            if nuevo_nombre:
                try:
                    st.session_state.user.user_metadata["full_name"] = nuevo_nombre
                    st.success("Nombre actualizado correctamente")
                except Exception as e:
                    st.error(f"Error al actualizar nombre: {e}")

        # Cambiar contraseña
        nueva_pass = st.text_input("Nueva contraseña", type="password")
        if st.button("Actualizar contraseña"):
            if nueva_pass:
                try:
                    st.success("Contraseña actualizada correctamente")
                except Exception as e:
                    st.error(f"Error al actualizar contraseña: {e}")

    # Cerrar sesión
    if st.button("Cerrar sesión"):
        sign_out()
        for k in defaults.keys():
            st.session_state[k] = defaults[k]
        st.experimental_rerun()

# -----------------------------
# Aplicación principal
# -----------------------------
def render_main_app():
    render_header()

    tabs = ["Vehículos", "Rutas"]
    if st.session_state.user:
        tabs.append("Historial de búsquedas")
        tabs.append("Panel de usuario")

    selected_tab = st.tabs(tabs)

    # -----------------------------
    # Vehículos
    with selected_tab[0]:
        st.subheader("🚗 Buscador de Vehículos")
        st.info("Si quieres guardar tus búsquedas, por favor regístrate o inicia sesión.")

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
            checklist = recomendaciones_itv_detalladas(datetime.date.today().year-anio, km, combustible)
            for tarea, cat in checklist:
                st.markdown(f"- **{cat}:** {tarea}")
            if st.session_state.user:
                registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
                if registro not in st.session_state.historial:
                    st.session_state.historial.append(registro)
                    save_search(str(st.session_state.user.id), f"{marca} {modelo}", registro)

    # -----------------------------
    # Rutas
    with selected_tab[1]:
        st.subheader("🗺️ Planificador de ruta y coste")
        origen_nombre = st.selectbox("Ciudad de origen", options=ciudades_es, index=ciudades_es.index("Almería"))
        destino_nombre = st.selectbox("Ciudad de destino", options=ciudades_es, index=ciudades_es.index("Sevilla"))
        consumo = st.number_input("Consumo medio (L/100km)", value=6.5)
        precio = st.number_input("Precio combustible (€/L)", value=1.6)

        if st.button("Calcular ruta"):
            lat_o, lon_o = ciudades_coords[origen_nombre]
            lat_d, lon_d = ciudades_coords[destino_nombre]
            ruta = get_route((lon_o, lat_o), (lon_d, lat_d))
            if ruta:
                distancia_km, duracion_min, coords_linea = ruta
                horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
                duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
                litros, coste = calcular_coste(distancia_km, consumo, precio)

                # Guardamos en session_state
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

                # Guardado solo para usuarios logueados
                if st.session_state.user:
                    registro_ruta = {
                        "origen": origen_nombre,
                        "destino": destino_nombre,
                        "distancia_km": round(distancia_km, 1),
                        "duracion": duracion_str,
                        "consumo_l": round(litros, 2),
                        "coste": round(coste, 2)
                    }
                    st.session_state.historial_rutas.append(registro_ruta)
                    save_route(str(st.session_state.user.id), registro_ruta)

                # Mostrar mapa
                m = folium.Map(location=[lat_o, lon_o], zoom_start=6)
                folium.Marker([lat_o, lon_o], tooltip=origen_nombre, icon=folium.Icon(color="green")).add_to(m)
                folium.Marker([lat_d, lon_d], tooltip=destino_nombre, icon=folium.Icon(color="red")).add_to(m)
                folium.PolyLine(coords_linea, color="blue", weight=3, opacity=0.7).add_to(m)
                st_folium(m, width=700, height=500)

                st.markdown(f"**Distancia:** {round(distancia_km,1)} km — **Duración:** {duracion_str} — **Consumo:** {round(litros,2)} L — **Coste:** {round(coste,2)} €")

    # -----------------------------
    # Historial de búsquedas
    if st.session_state.user and "Historial de búsquedas" in tabs:
        with selected_tab[2]:
            st.subheader("📜 Historial de búsquedas")
            if st.session_state.historial:
                for i, r in enumerate(st.session_state.historial, 1):
                    st.markdown(f"{i}. **{r['marca']} {r['modelo']}** — {r['anio']} — {r['km']} km — {r['combustible']}")
            else:
                st.info("No tienes búsquedas guardadas")

            st.subheader("🗺️ Historial de rutas")
            if st.session_state.historial_rutas:
                for i, r in enumerate(st.session_state.historial_rutas, 1):
                    st.markdown(f"{i}. **{r['origen']} → {r['destino']}** — {r['distancia_km']} km — {r['duracion']} — {r['consumo_l']} L — {r['coste']} €")
            else:
                st.info("No tienes rutas guardadas")

    # -----------------------------
    # Panel de usuario
    if st.session_state.user and "Panel de usuario" in tabs:
        with selected_tab[-1]:
            render_user_panel()

    render_footer()


# -----------------------------
# Ejecutar la app
# -----------------------------
def main():
    if not st.session_state.user:
        render_login_form()
    render_main_app()


if __name__ == "__main__":
    main()
                                                                
