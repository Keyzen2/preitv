import streamlit as st
from supabase import create_client, Client
from utils.helpers import (
    local_css,
    recomendaciones_itv_detalladas,
    resumen_proximos_mantenimientos,
    ciudades_coords
)
from io import BytesIO
from PIL import Image
import base64

# -----------------------------
# Configuración Supabase
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Inicialización sesión
# -----------------------------
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "historial" not in st.session_state:
    st.session_state.historial = []
if "logo_base64" not in st.session_state:
    st.session_state.logo_base64 = None
if "role" not in st.session_state:
    st.session_state.role = "user"

# -----------------------------
# Funciones auxiliares
# -----------------------------
def geocode_city(city_name: str):
    """Devuelve coordenadas desde ciudades_coords"""
    coords = ciudades_coords.get(city_name)
    if coords:
        return coords
    st.error(f"No se encontraron coordenadas para {city_name}")
    return None

def upload_logo():
    uploaded_file = st.file_uploader("Subir logo", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Logo subido", use_column_width=True)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        st.session_state["logo_base64"] = img_str
        st.success("Logo cargado correctamente")
        return img_str
    return None

def render_admin_panel():
    st.header("⚙️ Panel de administrador")
    # Estadísticas
    st.subheader("📊 Estadísticas de la app")
    users_count = supabase.table("users").select("id", count="exact").execute().count
    vehiculos_count = supabase.table("vehiculos").select("id", count="exact").execute().count
    rutas_count = supabase.table("routes").select("id", count="exact").execute().count
    st.metric("Usuarios registrados", users_count)
    st.metric("Vehículos registrados", vehiculos_count)
    st.metric("Rutas calculadas", rutas_count)
    st.markdown("---")
    # Listado de usuarios
    st.subheader("👥 Listado de usuarios")
    response = supabase.table("users").select("*").execute()
    if response.data:
        for u in response.data:
            st.markdown(f"**{u['email']}** — Rol: {u.get('role','usuario')}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Eliminar {u['email']}", key=f"del_{u['id']}"):
                    supabase.table("users").delete().eq("id", u["id"]).execute()
                    st.experimental_rerun()
            with col2:
                if st.button(f"Promover a admin", key=f"admin_{u['id']}"):
                    supabase.table("users").update({"role": "admin"}).eq("id", u["id"]).execute()
                    st.success(f"{u['email']} ahora es admin")
                    st.experimental_rerun()
    else:
        st.info("No hay usuarios registrados")
    st.markdown("---")
    # Logo
    st.subheader("🖼️ Logo de la web")
    upload_logo()

# -----------------------------
# Login lateral
# -----------------------------
with st.sidebar:
    st.title("🔐 PreITV Login")
    if not st.session_state.user_logged_in:
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            # Verificar credenciales Supabase
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user_logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = email.split("@")[0]
                user_data = supabase.table("users").select("*").eq("email", email).execute()
                if user_data.data:
                    st.session_state.role = user_data.data[0].get("role", "user")
            except Exception:
                st.error("Error al iniciar sesión")
    else:
        st.write(f"👋 Hola {st.session_state.user_name}")
        if st.button("Cerrar sesión"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.experimental_rerun()

# -----------------------------
# Header con logo
# -----------------------------
if st.session_state.logo_base64:
    st.markdown(
        f'<div style="text-align:center;"><img src="data:image/png;base64,{st.session_state.logo_base64}" width="200"></div>',
        unsafe_allow_html=True
    )
st.markdown("## 🚗 PreITV")

# -----------------------------
# Contenedor principal
# -----------------------------
main_container = st.container()
with main_container:
    if st.session_state.user_logged_in and st.session_state.role == "admin":
        render_admin_panel()

    tabs = st.tabs(["Vehículos", "Rutas"] + (["Historial"] if st.session_state.user_logged_in else []))
    
    # -----------------------------
    # Tab Vehículos
    # -----------------------------
    with tabs[0]:
        st.header("Vehículos")
        st.write("Aquí iría el buscador de vehículos y recomendaciones ITV")
    
    # -----------------------------
    # Tab Rutas
    # -----------------------------
    with tabs[1]:
        st.header("🗺️ Planificador de rutas")
        origen = st.selectbox("Ciudad de origen", list(ciudades_coords.keys()))
        destino = st.selectbox("Ciudad de destino", list(ciudades_coords.keys()))
        consumo = st.number_input("Consumo medio (L/100km)", min_value=1.0, value=5.5)
        precio_comb = st.number_input("Precio combustible (€/L)", min_value=0.5, value=1.9)
        if st.button("Calcular ruta"):
            origen_coords = geocode_city(origen)
            destino_coords = geocode_city(destino)
            if origen_coords and destino_coords:
                distancia = ((origen_coords[0]-destino_coords[0])**2 + (origen_coords[1]-destino_coords[1])**2)**0.5*111
                duracion = distancia / 50  # suposición 50 km/h
                consumo_total = distancia * consumo / 100
                coste = consumo_total * precio_comb
                st.markdown(f"**{origen} → {destino}** — {distancia:.1f} km — {duracion:.1f} h — {consumo_total:.1f} L — {coste:.2f} €")
                # Guardado solo para usuarios logueados
                if st.session_state.user_logged_in:
                    st.session_state.historial.append({
                        "origen": origen, "destino": destino, "distancia_km": distancia,
                        "duracion": duracion, "consumo_l": consumo_total, "coste": coste
                    })
    
    # -----------------------------
    # Tab Historial (solo usuarios logueados)
    # -----------------------------
    if st.session_state.user_logged_in:
        with tabs[2]:
            st.header("📜 Historial de búsquedas")
            if st.session_state.historial:
                for i, r in enumerate(st.session_state.historial, start=1):
                    st.markdown(
                        f"**{i}. {r['origen']} → {r['destino']}** — {r['distancia_km']:.1f} km — {r['duracion']:.1f} h — {r['consumo_l']:.1f} L — {r['coste']:.2f} €"
                    )
            else:
                st.info("Aún no hay búsquedas guardadas.")

# -----------------------------
# Footer
# -----------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;">© 2025 PreITV</div>',
    unsafe_allow_html=True
)
