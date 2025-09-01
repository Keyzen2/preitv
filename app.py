import streamlit as st
from utils.helpers import (
    local_css,
    recomendaciones_itv_detalladas,
    resumen_proximos_mantenimientos,
    ciudades_es,
    ciudades_coords
)
from supabase import create_client, Client
from io import BytesIO
from PIL import Image
import base64

# -----------------------------
# Configuración de Supabase
# -----------------------------
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

# -----------------------------
# Funciones auxiliares
# -----------------------------
def geocode_city(city_name: str):
    """Devuelve coordenadas desde ciudades_coords sin llamar a API externa"""
    coords = ciudades_coords.get(city_name)
    if coords:
        return coords
    st.error(f"No se encontraron coordenadas para {city_name}")
    return None

def upload_logo():
    """Subir logo de la web (opcional)"""
    uploaded_file = st.file_uploader("Subir logo", type=["png","jpg","jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Logo subido", use_column_width=True)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        st.session_state["logo_base64"] = img_str
        return img_str
    return None

def get_users():
    response = supabase.table("users").select("*").execute()
    if response.error:
        st.error("Error al obtener usuarios")
        return []
    return response.data

def get_statistics():
    users_count = supabase.table("users").select("id", count="exact").execute().count
    vehiculos_count = supabase.table("vehiculos").select("id", count="exact").execute().count
    rutas_count = supabase.table("routes").select("id", count="exact").execute().count
    return {"usuarios": users_count, "vehiculos": vehiculos_count, "rutas": rutas_count}

# -----------------------------
# Panel de usuario
# -----------------------------
def render_user_panel():
    st.header(f"👋 Hola, {st.session_state.user_email}")
    tabs = ["Vehículos", "Rutas", "Historial de búsquedas"]
    selected_tab = st.radio("Selecciona sección", tabs, horizontal=True)

    if selected_tab == "Vehículos":
        st.subheader("🚗 Vehículos")
        st.write("Aquí iría la gestión de vehículos...")

    elif selected_tab == "Rutas":
        st.subheader("🗺️ Planificador de ruta y coste")
        origen = st.selectbox("Ciudad de origen", ciudades_es)
        destino = st.selectbox("Ciudad de destino", ciudades_es)
        consumo = st.number_input("Consumo medio (L/100km)", min_value=0.0, value=6.5)
        precio = st.number_input("Precio combustible €/L", min_value=0.0, value=1.9)

        if st.button("Calcular ruta"):
            coord_origen = geocode_city(origen)
            coord_destino = geocode_city(destino)
            if coord_origen and coord_destino:
                distancia_km = 200  # Simulación
                duracion = "2h 30m"  # Simulación
                coste = distancia_km * consumo / 100 * precio
                st.markdown(f"**{origen} → {destino}** — {distancia_km} km — {duracion} — {consumo} L — {coste:.2f} €")

    elif selected_tab == "Historial de búsquedas":
        st.subheader("📜 Historial de búsquedas")
        historial = st.session_state.get("historial", [])
        if historial:
            for i, r in enumerate(historial, 1):
                st.markdown(f"{i}. {r['origen']} → {r['destino']} — {r['distancia_km']} km")
        else:
            st.info("No hay búsquedas guardadas")

    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.experimental_rerun()  # Solo aquí fuera de bucles y tabs

# -----------------------------
# Panel de administrador
# -----------------------------
def render_admin_panel():
    st.header("⚙️ Panel de administrador")
    stats = get_statistics()
    st.metric("Usuarios registrados", stats["usuarios"])
    st.metric("Vehículos registrados", stats["vehiculos"])
    st.metric("Rutas calculadas", stats["rutas"])

    st.markdown("---")
    st.subheader("👥 Listado de usuarios")
    users = get_users()
    for u in users:
        st.markdown(f"**{u['email']}** — Rol: {u.get('role','usuario')}")
        col1, col2 = st.columns(2)
        if col1.button(f"Eliminar {u['email']}", key=f"del_{u['id']}"):
            supabase.table("users").delete().eq("id", u["id"]).execute()
            st.success(f"{u['email']} eliminado")
        if col2.button(f"Promover {u['email']} a admin", key=f"admin_{u['id']}"):
            supabase.table("users").update({"role":"admin"}).eq("id", u["id"]).execute()
            st.success(f"{u['email']} ahora es admin")

# -----------------------------
# Main
# -----------------------------
def main():
    st.set_page_config(page_title="PreITV", layout="wide")
    local_css("assets/style.css")

    # Login lateral
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        with st.sidebar:
            st.title("🔐 Iniciar sesión")
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            if st.button("Login"):
                # Simulación: validar contra Supabase
                user = supabase.table("users").select("*").eq("email", email).eq("password", password).execute()
                if user.data:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.user_role = user.data[0].get("role","usuario")
                    st.experimental_rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
    else:
        if st.session_state.user_role == "admin":
            render_admin_panel()
        render_user_panel()

if __name__ == "__main__":
    main()
