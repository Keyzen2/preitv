from supabase import create_client
import streamlit as st
from typing import Optional

# Credenciales desde secrets.toml (configuradas en Streamlit)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Autenticación
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
# Guardado de búsquedas y rutas
# -----------------------------
def save_search(user_id: Optional[str], city: str, results: dict):
    """Guardar búsqueda de talleres en la tabla 'searches'."""
    try:
        data = {
            "user_id": user_id,
            "city": city,
            "results": results
        }
        supabase.table("searches").insert(data).execute()
    except Exception as e:
        st.error(f"Error guardando búsqueda: {e}")

def save_route(user_id: Optional[str], origin: str, destination: str,
               distance_km: float, duration: str, consumption_l: float, cost: float):
    """Guardar ruta y coste en la tabla 'searches'."""
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
        st.error(f"Error guardando ruta: {e}")

# -----------------------------
# Carga de históricos de usuario
# -----------------------------
def load_user_data(user_id: str):
    """
    Carga el historial de vehículos y rutas del usuario desde Supabase.
    Devuelve dos listas: historial_vehiculos, historial_rutas
    """
    try:
        # Historial de vehículos
        vehiculos_resp = supabase.table("searches").select("*").eq("user_id", user_id).execute()
        vehiculos = vehiculos_resp.data if vehiculos_resp.data else []

        # Separar rutas de búsquedas de vehículos
        historial_vehiculos = [v for v in vehiculos if "distance_km" not in v.get("results", {})]
        historial_rutas = [v for v in vehiculos if "distance_km" in v.get("results", {})]

        return historial_vehiculos, historial_rutas
    except Exception as e:
        st.error(f"Error cargando históricos: {e}")
        return [], []



