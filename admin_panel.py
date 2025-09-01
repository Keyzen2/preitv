import streamlit as st
from database import get_users, get_statistics

def render_admin_panel(supabase):
    st.header("⚙️ Panel de administrador")
    stats = get_statistics(supabase)
    st.metric("Usuarios registrados", stats["usuarios"])
    st.metric("Vehículos registrados", stats["vehiculos"])
    st.metric("Rutas calculadas", stats["rutas"])

    st.subheader("👥 Listado de usuarios")
    users = get_users(supabase)
    if users:
        for u in users:
            st.markdown(f"**{u['email']}** — Rol: {u.get('role','usuario')}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Eliminar {u['email']}", key=f"del_{u['id']}"):
                    supabase.table("users").delete().eq("id", u["id"]).execute()
                    st.session_state['update'] = True
            with col2:
                if st.button(f"Promover {u['email']} a admin", key=f"admin_{u['id']}"):
                    supabase.table("users").update({"role":"admin"}).eq("id", u["id"]).execute()
                    st.session_state['update'] = True
