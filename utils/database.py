from supabase import create_client, Client
import streamlit as st
import os

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
