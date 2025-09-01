import datetime
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models
from services.routes import get_route, calcular_coste
from services.supabase_client import sign_in, sign_up, sign_out, save_search, save_route, load_user_data
from utils.helpers import local_css, recomendaciones_itv_detalladas, resumen_proximos_mantenimientos
from utils.ciudades import ciudades_coords

# -----------------------------
# Configuración de página y CSS
# -----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
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
    """Devuelve las coordenadas desde ciudades_coords en lugar de llamar a la API externa"""
    coords = ciudades_coords.get(city_name)
    if coords:
        return coords
    else:
        st.error(f"No se encontraron coordenadas para {city_name}")
    return None

# -----------------------------
# Render Login
# -----------------------------
def render_login_form():
    st.sidebar.subheader("🔐 Iniciar sesión / Registrarse")
    tab_login, tab_signup = st.sidebar.tabs(["Entrar", "Registrarse"])

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
# Panel de usuario
# -----------------------------
def render_user_panel():
    user_email = getattr(st.session_state.user, "email", None) or st.session_state.user.get("email")
    user_name = getattr(st.session_state.user, "user_metadata", {}).get("name", "")

    st.subheader(f"👋 Hola, {user_name or user_email}")

    with st.expander("⚙️ Configuración de cuenta", expanded=True):
        nuevo_nombre = st.text_input("Cambiar nombre", value=user_name)
        if st.button("Actualizar nombre"):
            if nuevo_nombre:
                try:
                    from services.supabase_client import supabase
                    supabase.auth.update_user({"data": {"name": nuevo_nombre}})
                    st.success("Nombre actualizado correctamente")
                    st.session_state.user.user_metadata["name"] = nuevo_nombre
                except Exception as e:
                    st.error(f"Error al actualizar nombre: {e}")

        nueva_pass = st.text_input("Nueva contraseña", type="password")
        if st.button("Actualizar contraseña"):
            if nueva_pass:
                try:
                    from services.supabase_client import supabase
                    supabase.auth.update_user({"password": nueva_pass})
                    st.success("Contraseña actualizada correctamente")
                except Exception as e:
                    st.error(f"Error al actualizar contraseña: {e}")

    if st.button("Cerrar sesión"):
        sign_out()
        for key in defaults.keys():
            st.session_state[key] = defaults[key]
        st.experimental_rerun()

# -----------------------------
# Render App Principal
# -----------------------------
def render_main_app():
    # Cargar historial solo si hay usuario
    if st.session_state.user and not st.session_state.data_loaded:
        historial, historial_rutas = load_user_data(str(st.session_state.user.id))
        st.session_state.historial = historial
        st.session_state.historial_rutas = historial_rutas
        st.session_state.data_loaded = True

    # Header con logo
    st.markdown(f"<div style='text-align:center;'><img src='logo.png' width='150'></div>", unsafe_allow_html=True)

    # Tabs principales
    tabs = ["Vehículos", "Rutas"]
    if st.session_state.user:
        tabs.append("Historial de búsquedas")
        tabs.append("Panel de usuario")

    selected_tab = st.tabs(tabs)

    # -----------------------------
    # Tab Vehículos
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
            st.success(f"Has seleccionado **{marca} {modelo}**")
            resumen = resumen_proximos_mantenimientos(km)
            st.info(f"📅 {resumen}")
            checklist = recomendaciones_itv_detalladas(datetime.date.today().year - anio, km, combustible)
            st.session_state.checklist = checklist

            if st.session_state.user:
                registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
                if registro not in st.session_state.historial:
                    st.session_state.historial.append(registro)
                    save_search(str(st.session_state.user.id), f"{marca} {modelo}", registro)
            else:
                st.info("Para guardar esta búsqueda, inicia sesión o regístrate.")

    # -----------------------------
# Tab Rutas
# -----------------------------
with selected_tab[1]:
    st.subheader("🗺️ Planificador de ruta y coste")
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
            ruta = get_route((lon_o, lat_o), (lon_d, lat_d))
            if ruta:
                distancia_km, duracion_min, coords_linea = ruta
                horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
                duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
                litros, coste = calcular_coste(distancia_km, consumo, precio)
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
                        "consumo_l": litros,
                        "coste": coste
                    }
                    if registro_ruta not in st.session_state.historial_rutas:
                        st.session_state.historial_rutas.append(registro_ruta)
                        save_route(
                            user_id=str(st.session_state.user.id),
                            origin=origen_nombre,
                            destination=destino_nombre,
                            distance_km=distancia_km,
                            duration=duracion_str,
                            consumption_l=litros,
                            cost=coste
                        )
                else:
                    st.info("Para guardar esta ruta, inicia sesión o regístrate.")

                # Mostrar mapa
                try:
                    m = folium.Map(location=[lat_o, lon_o], zoom_start=6)
                    folium.Marker(
                        [lat_o, lon_o],
                        tooltip=f"Origen: {origen_nombre}",
                        icon=folium.Icon(color="green", icon="play")
                    ).add_to(m)
                    folium.Marker(
                        [lat_d, lon_d],
                        tooltip=f"Destino: {destino_nombre}",
                        icon=folium.Icon(color="red", icon="stop")
                    ).add_to(m)
                    folium.PolyLine(
                        coords_linea,
                        color="blue",
                        weight=5,
                        opacity=0.7
                    ).add_to(m)
                    st_folium(m, width=700, height=400)
                except Exception as e:
                    st.error(f"No se pudo generar el mapa: {e}")
            else:
                st.error("No se pudo calcular la ruta. Intenta otra combinación de ciudades.")
        else:
            st.error("No se pudo obtener la ubicación de una o ambas ciudades.")

# -----------------------------
# Tab Historial de búsquedas (solo usuarios logueados)
# -----------------------------
if st.session_state.user and "Historial de búsquedas" in tabs:
    with selected_tab[tabs.index("Historial de búsquedas")]:
        st.subheader("📜 Historial de búsquedas")
        if st.session_state.historial:
            for i, h in enumerate(st.session_state.historial, start=1):
                st.markdown(f"**{i}. {h['marca']} {h['modelo']} — {h['anio']} — {h['km']} km — {h['combustible']}**")
        else:
            st.info("No hay búsquedas guardadas aún.")

        st.subheader("🗺️ Historial de rutas")
        if st.session_state.historial_rutas:
            for i, r in enumerate(st.session_state.historial_rutas, start=1):
                st.markdown(f"**{i}. {r['origen']} → {r['destino']}** — {r['distancia_km']} km — {r['duracion']} — {r['consumo_l']} L — {r['coste']} €")
        else:
            st.info("No hay rutas guardadas aún.")

# -----------------------------
# Tab Panel de usuario
# -----------------------------
if st.session_state.user and "Panel de usuario" in tabs:
    with selected_tab[tabs.index("Panel de usuario")]:
        render_user_panel()

# -----------------------------
# Footer
# -----------------------------
st.markdown("""
<hr>
<div style='text-align:center;'>
    &copy; 2025 PreITV | Todos los derechos reservados
</div>
""", unsafe_allow_html=True)
    with selected_tab[1]:
        st.subheader("🗺️ Planificador de ruta y coste")
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
                ruta = get_route((lon_o, lat_o), (lon_d, lat_d))
                if ruta:
                    distancia_km, duracion_min, coords_linea = ruta
                    horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
                    duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
                    litros, coste = calcular_coste(distancia_km, consumo, precio)
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

                    if st.session_state.user:
                        registro_ruta = {
                            "origen": origen_nombre,
                            "destino": destino_nombre,
                            "distancia_km": round(distancia_km, 1),
                            "duracion": duracion_str,
                            "consumo_l": litros,
                            "coste": coste
                        }
                        if registro_ruta not in st.session_state.historial_rutas:
                            st.session_state.historial_rutas.append(registro_ruta)
                            save_route(
                                user_id=str(st.session_state.user.id),
                                origin=origen_nombre,
                                destination=destino_nombre,
                                distance_km=distancia_km,
                                duration=duracion_str,
                                consumption_l=litros,
                                cost=coste
                            )
                    else:
                        st.info("Para guardar esta ruta, inicia sesión o regístrate.")

                    # Mapa
                    try:
                        m = folium.Map(location=st.session_state.ruta_datos["coords_origen"], zoom_start=6)
                        folium.Marker(
                            st.session_state.ruta_datos["coords_origen"],
                            tooltip=f"Origen: {origen_nombre}",
                            icon=folium.Icon(color="green", icon="play")
                        ).add_to(m)
                        folium.Marker(
                            st.session_state.ruta_datos["coords_destino"],
                            tooltip=f"Destino: {destino_nombre}",
                            icon=folium.Icon(color="red", icon="stop
