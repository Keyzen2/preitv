from supabase import create_client
import streamlit as st
from typing import Optional

# Credenciales desde secrets.toml
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

# -----------------------------
# Guardado y carga de datos
# -----------------------------
def save_search(user_id: Optional[str], city: str, results: dict):
    """Guardar búsqueda de vehículos para usuarios registrados."""
    if not user_id:
        return
    try:
        data = {"user_id": user_id, "city": city, "results": results}
        supabase.table("searches").insert(data).execute()
    except Exception as e:
        st.error(f"Error guardando búsqueda: {e}")

def save_route(user_id: Optional[str], origin: str, destination: str,
               distance_km: float, duration: str, consumption_l: float, cost: float):
    """Guardar ruta y coste para usuarios registrados."""
    if not user_id:
        return
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

def load_user_data(user_id: str):
    """Cargar historial de un usuario."""
    historial = []
    historial_rutas = []
    if not user_id:
        return historial, historial_rutas
    try:
        res = supabase.table("searches").select("*").eq("user_id", user_id).execute()
        if res.data:
            for row in res.data:
                results = row.get("results", {})
                if "marca" in results:  # Vehículos
                    historial.append(results)
                elif "distance_km" in results:  # Rutas
                    historial_rutas.append(results)
    except Exception as e:
        st.error(f"Error cargando datos de usuario: {e}")
    return historial, historial_rutas
