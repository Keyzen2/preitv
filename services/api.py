import requests
import logging
from config import EUROPEAN_MAKES
import streamlit as st
from urllib.parse import quote_plus

@st.cache_data(ttl=86400)
def get_makes():
    """Obtiene marcas de la API NHTSA y filtra solo las que están en EUROPEAN_MAKES."""
    try:
        url = "https://vpic.nhtsa.dot.gov/api/vehicles/GetAllMakes?format=json"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error al obtener marcas: {e}")
        return []

    data = res.json()
    makes_api = [m["Make_Name"].strip() for m in data.get("Results", []) if "Make_Name" in m]
    makes_filtradas = sorted([
        m for m in makes_api if m.lower() in [em.lower() for em in EUROPEAN_MAKES]
    ])
    return makes_filtradas

@st.cache_data(ttl=86400)
def get_models(make: str):
    """Obtiene modelos de una marca desde la API NHTSA."""
    if not make:
        return []
    try:
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMake/{quote_plus(make)}?format=json"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error al obtener modelos: {e}")
        return []

    data = res.json()
    modelos = sorted([m["Model_Name"].strip() for m in data.get("Results", []) if "Model_Name" in m])
    return modelos



