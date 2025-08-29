import os
import streamlit as st
import requests
import json
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus
from PIL import Image

# --- CONFIG ---
st.set_page_config(
    page_title="Buscador de Vehículos",
    page_icon="🚗",
    layout="centered"
)

# --- ESTILOS CSS ---
st.markdown(
    """
    <style>
    body {
        background-color: #f9fafb;
        font-family: 'Segoe UI', sans-serif;
    }
    .stSelectbox, .stTextInput, .stButton button {
        border-radius: 12px;
    }
    .stButton button {
        background-color: #007bff;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.6em 1.2em;
    }
    .stButton button:hover {
        background-color: #0056b3;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- FUNCIONES ---
@st.cache_data
def get_makes():
    """Obtiene todas las marcas de la API y filtra solo Europa."""
    url = "https://vpic.nhtsa.dot.gov/api/vehicles/GetAllMakes?format=json"
    res = requests.get(url)
    data = res.json()
    makes = [m["Make_Name"] for m in data["Results"]]

    # Filtrado marcas Europa (personalizable)
    european_makes = [
        "Audi", "BMW", "Citroen", "Dacia", "Fiat", "Ford",
        "Mercedes-Benz", "Opel", "Peugeot", "Renault",
        "SEAT", "Skoda", "Volkswagen", "Volvo", "Alfa Romeo",
        "Mini", "Porsche", "Jaguar", "Land Rover"
    ]

    # Filtrar case-insensitive
    makes_eu = sorted([m for m in makes if m.title() in european_makes])
    return makes_eu

@st.cache_data
def get_models(make: str):
    """Devuelve modelos de una marca concreta."""
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMake/{quote_plus(make)}?format=json"
    res = requests.get(url)
    data = res.json()
    models = [m["Model_Name"] for m in data["Results"]]
    return sorted(models)

# --- UI ---
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo disponible en Europa.")

# Selección Marca
makes = get_makes()
marca = st.selectbox("Marca", options=makes, index=0)

# Selección Modelo (dinámico)
modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos, index=0 if modelos else None)

# Botón de búsqueda
if st.button("🔍 Buscar información"):
    if marca and modelo:
        st.success(f"Has seleccionado **{marca} {modelo}**")
    else:
        st.warning("Selecciona una marca y modelo válido.")
