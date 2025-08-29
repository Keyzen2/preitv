from supabase import create_client
import streamlit as st
from typing import Optional

# Leer credenciales desde secrets.toml de Streamlit
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Funciones de autenticación
# -----------------------------
def sign_up(email: str, password: str):
    """Registrar un nuevo usuario."""
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_in(email: str, password: str):
    """Iniciar sesión."""
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def sign_out():
    """Cerrar sesión."""
    return supabase.auth.sign_out()

def get_user():
    """Obtener usuario actual."""
    return supabase.auth.get_user()

# -----------------------------
# Guardar búsquedas y rutas
# -----------------------------
def save_search(user_id: Optional[str], city: str, results: dict):
    """Guardar búsqueda de talleres."""
    try:
        data = {
            "user_id": user_id,
            "city": city,
            "results": results
        }
        supabase.table("searches").insert(data).execute()
    except Exception as e:
        st.error(f"Error guardando búsqueda en Supabase: {e}")

def save_route(user_id: Optional[str], origin: str, destination: str,
               distance_km: float, duration: str, consumption_l: float, cost: float):
    """Guardar ruta y coste."""
    try:
        data = {
            "user_id": user_id,
            "city": f"{origin} → {destination}",
            "results": {
                "distance_km": distance_km,
                "duration": duration,
                "consumption_l": consumption_l,
                "cost": cost
            }
        }
        supabase.table("searches").insert(data).execute()
    except Exception as e:
        st.error(f"Error guardando ruta en Supabase: {e}")



