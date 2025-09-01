from supabase import create_client, Client
import streamlit as st

def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def get_users(supabase: Client):
    res = supabase.table("users").select("*").execute()
    return res.data if not res.error else []

def get_statistics(supabase: Client):
    users_count = supabase.table("users").select("id", count="exact").execute().count
    vehiculos_count = supabase.table("vehiculos").select("id", count="exact").execute().count
    rutas_count = supabase.table("routes").select("id", count="exact").execute().count
    return {"usuarios": users_count, "vehiculos": vehiculos_count, "rutas": rutas_count}
