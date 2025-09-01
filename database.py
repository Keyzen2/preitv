# database.py
from supabase import create_client, Client
import streamlit as st
from typing import List, Dict, Optional

# -----------------------------
# Configuración del cliente Supabase
# -----------------------------
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

# -----------------------------
# Usuarios
# -----------------------------
def get_current_user() -> Optional[Dict]:
    """Devuelve datos del usuario logueado"""
    user = supabase.auth.get_user()
    if user.data:
        return user.data
    return None

def get_all_users() -> List[Dict]:
    """Solo admins: devuelve todos los usuarios"""
    response = supabase.table("users").select("*").execute()
    if response.error:
        st.error(f"Error al obtener usuarios: {response.error}")
        return []
    return response.data

def promote_to_admin(user_id: str):
    supabase.table("users").update({"role": "admin"}).eq("id", user_id).execute()

def delete_user(user_id: str):
    supabase.table("users").delete().eq("id", user_id).execute()

# -----------------------------
# Vehículos
# -----------------------------
def add_vehicle(user_id: str, marca: str, modelo: str, anio: int, km: int, combustible: str):
    supabase.table("vehiculos").insert({
        "user_id": user_id,
        "marca": marca,
        "modelo": modelo,
        "anio": anio,
        "km": km,
        "combustible": combustible
    }).execute()

def get_user_vehicles(user_id: str) -> List[Dict]:
    response = supabase.table("vehiculos").select("*").eq("user_id", user_id).execute()
    if response.error:
        st.error(f"Error al obtener vehículos: {response.error}")
        return []
    return response.data

# -----------------------------
# Rutas
# -----------------------------
def add_route(user_id: str, origen: str, destino: str, distancia_km: float,
              duracion: str, consumo_l: float, coste: float):
    supabase.table("routes").insert({
        "user_id": user_id,
        "origen": origen,
        "destino": destino,
        "distancia_km": distancia_km,
        "duracion": duracion,
        "consumo_l": consumo_l,
        "coste": coste
    }).execute()

def get_user_routes(user_id: str) -> List[Dict]:
    response = supabase.table("routes").select("*").eq("user_id", user_id).execute()
    if response.error:
        st.error(f"Error al obtener rutas: {response.error}")
        return []
    return response.data

# -----------------------------
# Configuración de la app (logo, etc.)
# -----------------------------
def get_app_config() -> Dict:
    response = supabase.table("app_config").select("*").limit(1).execute()
    if response.error or not response.data:
        return {}
    return response.data[0]

def update_app_logo(logo_base64: str):
    # Si ya existe un registro, actualiza, sino inserta
    config = get_app_config()
    if config:
        supabase.table("app_config").update({"logo_base64": logo_base64}).eq("id", config["id"]).execute()
    else:
        supabase.table("app_config").insert({"logo_base64": logo_base64}).execute()
