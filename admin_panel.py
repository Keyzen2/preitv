import streamlit as st
from utils.database import supabase_client
from io import BytesIO
from PIL import Image
import base64

# -----------------------------
# Funciones auxiliares
# -----------------------------
def get_users(supabase_client):
    """Obtiene listado de usuarios desde Supabase"""
    res = supabase_client.table("users").select("*").execute()
    if res.error:
        st.error("Error al obtener usuarios")
        return []
    return res.data

def get_statistics(supabase_client):
    """Obtiene estadísticas básicas de la app"""
    users_count = supabase_client.table("users").select("id", count="exact").execute().count
    vehiculos_count = supabase_client.table("vehiculos").select("id", count="exact").execute().count
    rutas_count = supabase_client.table("routes").select("id", count="exact").execute().count
    return {"usuarios": users_count, "vehiculos": vehiculos_count, "rutas": rutas_count}

def upload_logo():
    """Subir logo de la web"""
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

# -----------------------------
# Panel de administrador
# -----------------------------
def render_admin_panel(supabase_client):
    st.header("⚙️ Panel de administrador")

    # Estadísticas
    st.subheader("📊 Estadísticas de la app")
    stats = get_statistics(supabase_client)
    st.metric("Usuarios registrados", stats["usuarios"])
    st.metric("Vehículos registrados", stats["vehiculos"])
    st.metric("Rutas calculadas", stats["rutas"])

    st.markdown("---")
    # Gestión de usuarios
    st.subheader("👥 Listado de usuarios")
    users = get_users(supabase_client)
    if users:
        for u in users:
            st.markdown(f"**{u['email']}** — Rol: {u.get('role', 'usuario')}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Eliminar {u['email']}", key=f"del_{u['id']}"):
                    supabase_client.table("users").delete().eq("id", u["id"]).execute()
                    st.experimental_rerun()
            with col2:
                if st.button(f"Promover {u['email']} a admin", key=f"admin_{u['id']}"):
                    supabase_client.table("users").update({"role": "admin"}).eq("id", u["id"]).execute()
                    st.success(f"{u['email']} ahora es admin")
                    st.experimental_rerun()
    else:
        st.info("No hay usuarios registrados")

    st.markdown("---")
    # Logo de la web
    st.subheader("🖼️ Logo de la web")
    logo_base64 = upload_logo()
    if logo_base64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_base64}" width="200">',
            unsafe_allow_html=True
        )
