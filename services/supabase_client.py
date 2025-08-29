from supabase import create_client
import streamlit as st

# Leer credenciales desde secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_search(user_id: str, city: str, results: dict):
    """
    Guarda una búsqueda en la tabla 'searches'.
    - user_id: identificador del usuario (puede ser None si no hay login)
    - city: ciudad buscada
    - results: diccionario con los resultados (se guardará como JSONB)
    """
    try:
        data = {
            "user_id": user_id,
            "city": city,
            "results": results
        }
        response = supabase.table("searches").insert(data).execute()
        return response
    except Exception as e:
        st.error(f"Error guardando búsqueda en Supabase: {e}")
        return None



