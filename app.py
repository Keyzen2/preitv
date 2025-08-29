import datetime
import time
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, search_workshops
from services.routes import get_route, calcular_coste
from services.supabase_client import (
    sign_in, sign_up, sign_out, save_search, save_route,
    update_profile, delete_searches, delete_routes
)
from utils.helpers import (
    local_css, recomendaciones_itv_detalladas,
    resumen_proximos_mantenimientos, ciudades_es
)

# -----------------------------
# Configuración página
# -----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# -----------------------------
# Utilidad: geocodificación
# -----------------------------
def geocode_city(city_name: str):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city_name, "format": "json", "limit": 1, "countrycodes": "es"}
        headers = {"User-Agent": "PreITV-App"}
        res = requests.get(url, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        st.error(f"Error geocodificando {city_name}: {e}")
    return None

# -----------------------------
# Estado inicial
# -----------------------------
defaults = {
    "historial": [],
    "historial_rutas": [],
    "checklist": [],
    "user": None,
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
# Login / Registro
# -----------------------------
if not st.session_state.user:
    st.subheader("🔐 Iniciar sesión o registrarse")
    tab_login, tab_signup = st.tabs(["Iniciar sesión", "Registrarse"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_password")
        if st.button("Entrar"):
            if email and password:
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
            else:
                st.warning("Debes introducir email y contraseña")

    with tab_signup:
        email_s = st.text_input("Email nuevo", key="signup_email")
        password_s = st.text_input("Contraseña nueva", type="password", key="signup_password")
        if st.button("Crear cuenta"):
            if email_s and password_s:
                try:
                    res = sign_up(email_s, password_s)
                    if getattr(res, "user", None):
                        st.success("Cuenta creada. Revisa tu email para verificar.")
                    else:
                        st.error("No se pudo crear la cuenta")
                except Exception as e:
                    st.error(f"Error al registrarse: {e}")
            else:
                st.warning("Debes introducir email y contraseña")
    st.stop()

# -----------------------------
# Usuario logueado: saludo y panel
# -----------------------------
col_user1, col_user2 = st.columns([3, 1])
with col_user1:
    if st.button(f"👋 Hola, {st.session_state.user.user_metadata.get('full_name','Usuario')}"):
        st.subheader("Panel de usuario")
        new_name = st.text_input("Cambiar nombre", value=st.session_state.user.user_metadata.get('full_name',''))
        new_pass = st.text_input("Cambiar contraseña", type="password")
        if st.button("Guardar cambios"):
            try:
                update_profile(st.session_state.user.id, new_name, new_pass)
                st.success("Perfil actualizado")
            except Exception as e:
                st.error(f"No se pudo actualizar: {e}")

with col_user2:
    if st.button("Cerrar sesión"):
        sign_out()
        st.session_state.user = None
        st.experimental_rerun()

# -----------------------------
# 🚗 Buscador de Vehículos
# -----------------------------
st.subheader("🚗 Buscador de Vehículos")
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox("Marca", options=makes, index=makes.index(st.session_state.ultima_marca) if st.session_state.ultima_marca in makes else 0)
modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos, index=modelos.index(st.session_state.ultima_modelo) if st.session_state.ultima_modelo in modelos else 0)
anio = st.number_input("Año de matriculación", min_value=1900, max_value=datetime.date.today().year, value=st.session_state.ultimo_anio or 2000)
km = st.number_input("Kilometraje", min_value=0, step=1000, value=st.session_state.ultimo_km or 0)
combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"], index=["Gasolina","Diésel","Híbrido","Eléctrico"].index(st.session_state.ultimo_combustible or "Gasolina"))

if st.button("🔍 Buscar información"):
    if marca and modelo:
        st.session_state.ultima_marca = marca
        st.session_state.ultima_modelo = modelo
        st.session_state.ultimo_anio = anio
        st.session_state.ultimo_km = km
        st.session_state.ultimo_combustible = combustible

        st.success(f"Has seleccionado **{marca} {modelo}**")
        resumen = resumen_proximos_mantenimientos(km)
        st.info(f"📅 {resumen}")
        edad = datetime.date.today().year - anio
        st.session_state.checklist = recomendaciones_itv_detalladas(edad, km, combustible)

        registro = {"marca": marca, "modelo": modelo, "anio": anio, "km": km, "combustible": combustible}
        if registro not in st.session_state.historial:
            st.session_state.historial.append(registro)
            save_search(str(st.session_state.user.id), registro)

if st.session_state.historial:
    st.subheader("📜 Coches consultados")
    for item in st.session_state.historial:
        st.markdown(f"**{item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")
    if st.button("🗑 Limpiar historial de vehículos"):
        st.session_state.historial = []
        delete_searches(str(st.session_state.user.id))
        st.success("Historial borrado")

if st.session_state.checklist:
    st.subheader("✅ Recomendaciones antes de la ITV")
    for tarea, cat in st.session_state.checklist:
        st.markdown(f"- **{cat}:** {tarea}")

# -----------------------------
# 🔧 Talleres por ciudad
# -----------------------------
st.markdown("---")
st.subheader("🔧 Talleres en tu ciudad")
ciudad_busqueda = st.selectbox("Selecciona ciudad", ["— Escribe tu ciudad —"] + ciudades_es)
ciudad_txt = st.text_input("O escribe tu ciudad", value="" if ciudad_busqueda == "— Escribe tu ciudad —" else "")
busqueda_final = ciudad_txt.strip() if ciudad_txt.strip() else (None if ciudad_busqueda == "— Escribe tu ciudad —" else ciudad_busqueda)

if st.button("Buscar talleres"):
    if busqueda_final:
        st.session_state.talleres = search_workshops(busqueda_final, limit=5)
        save_search(str(st.session_state.user.id), {"city": busqueda_final, "results": st.session_state.talleres})
    else:
        st.warning("Selecciona o escribe una ciudad válida")

if st.session_state.talleres:
    st.subheader("Resultados de talleres")
    for i, t in enumerate(st.session_state.talleres, start=1):
        st.markdown(f"**{i}. {t.get('name','Taller')}** — {t.get('address','')}")

# -----------------------------
# 🗺️ Planificador de ruta y coste
# -----------------------------
st.markdown("---")
st.subheader("🗺️ Planificador de ruta y coste")
origen_nombre = st.text_input("Ciudad de origen", "Almería", key="origen")
destino_nombre = st.text_input("Ciudad de destino", "Sevilla", key="destino")
consumo = st.number_input("Consumo medio (L/100km)", value=6.5)
precio = st.number_input("Precio combustible (€/L)", value=1.6)

if st.button("Calcular ruta"):
    coords_origen = geocode_city(origen_nombre.strip())
    coords_destino = geocode_city(destino_nombre.strip())
    if coords_origen and coords_destino:
        lat_o, lon_o = coords_origen
        lat_d, lon_d = coords_destino
        ruta = get_route((lon_o, lat_o), (lon_d, lat_d))
        if ruta:
            distancia_km, duracion_min, coords_linea = ruta
            horas, minutos = int(duracion_min // 60), int(duracion_min % 60)
            duracion_str = f"{horas} h {minutos} min" if horas > 0 else f"{minutos} min"
            litros, coste = calcular_coste(distancia_km, consumo, precio)

            # Guardar en session_state
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

            # Guardar histórico y en Supabase
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
            st.error("No se pudo calcular la ruta.")
    else:
        st.error("No se pudo obtener la ubicación de una o ambas ciudades.")

# Mostrar mapa y datos de la ruta
if st.session_state.ruta_datos:
    datos = st.session_state.ruta_datos
    st.success(f"Distancia: {datos['distancia_km']:.1f} km — Duración: {datos['duracion']}")
    st.info(f"Consumo estimado: {datos['litros']} L — Coste estimado: {datos['coste']} €")
    try:
        m = folium.Map(location=datos["coords_origen"], zoom_start=6)
        folium.Marker(datos["coords_origen"], tooltip=f"Origen: {datos['origen']}").add_to(m)
        folium.Marker(datos["coords_destino"], tooltip=f"Destino: {datos['destino']}").add_to(m)
        folium.PolyLine(
            [(lat, lon) for lon, lat in datos["coords_linea"]],
            color="blue",
            weight=4
        ).add_to(m)
        st_folium(m, width=700, height=500)
    except Exception as e:
        st.warning(f"No se pudo renderizar el mapa: {e}")

# Histórico de rutas
st.markdown("---")
st.subheader("📜 Histórico de rutas")
if st.session_state.historial_rutas:
    for r in st.session_state.historial_rutas:
        st.markdown(
            f"**{r['origen']} → {r['destino']}** — {r['distancia_km']} km — "
            f"{r['duracion']} — {r['consumo_l']} L — {r['coste']} €"
        )
    if st.button("🗑 Limpiar historial de rutas"):
        st.session_state.historial_rutas = []
        st.session_state.ruta_datos = None
        delete_routes(str(st.session_state.user.id))
        st.success("Histórico de rutas borrado.")
else:
    st.info("Aún no has guardado rutas en esta sesión.")
