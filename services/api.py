import requests
import logging
from urllib.parse import quote_plus
import streamlit as st
from config import EUROPEAN_MAKES

@st.cache_data(ttl=86400)
def get_makes():
    """Obtiene marcas europeas, con manejo de errores."""
    try:
        url = "https://vpic.nhtsa.dot.gov/api/vehicles/GetAllMakes?format=json"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error al obtener marcas: {e}")
        return []

    try:
        data = res.json()
    except ValueError:
        logging.error(f"Respuesta no es JSON válida: {res.text[:200]}")
        return []

    if "Results" not in data:
        logging.error(f"Estructura inesperada: {data}")
        return []

    makes = [m["Make_Name"] for m in data["Results"] if "Make_Name" in m]
    makes_eu = sorted([m for m in makes if m.strip().lower() in [em.lower() for em in EUROPEAN_MAKES]])
    return makes_eu


@st.cache_data(ttl=86400)
def get_models(make: str):
    """Obtiene modelos de una marca."""
    if not make:
        return []
    try:
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMake/{quote_plus(make)}?format=json"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error al obtener modelos: {e}")
        return []

    try:
        data = res.json()
    except ValueError:
        logging.error(f"Respuesta no es JSON válida: {res.text[:200]}")
        return []

    if "Results" not in data:
        logging.error(f"Estructura inesperada: {data}")
        return []

    models = [m["Model_Name"] for m in data["Results"] if "Model_Name" in m]
    return sorted(models)