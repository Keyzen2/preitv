import requests
import logging
from config import EUROPEAN_MAKES
import streamlit as st
from urllib.parse import quote_plus

@st.cache_data(ttl=86400)
def get_makes():
    """
    Obtiene todas las marcas de la API NHTSA y filtra solo las que están
    en la lista EUROPEAN_MAKES de config.py.
    """
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

    # Normalizar a minúsculas para comparación
    makes_api = [m["Make_Name"].strip() for m in data["Results"] if "Make_Name" in m]
    makes_filtradas = sorted([
        m for m in makes_api
        if m.lower() in [em.lower() for em in EUROPEAN_MAKES]
    ])

    return makes_filtradas


@st.cache_data(ttl=86400)
def get_models(make: str):
    """Obtiene todos los modelos de una marca desde la API NHTSA."""
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

    modelos = sorted([m["Model_Name"].strip() for m in data["Results"] if "Model_Name" in m])
    return modelos


def get_brand_image(brand):
    """
    Intenta obtener una imagen genérica de la marca desde Wikimedia Commons.
    Devuelve la URL de la imagen o None si no se encuentra.
    """
    search_url = (
        f"https://commons.wikimedia.org/w/api.php"
        f"?action=query&format=json&prop=pageimages&piprop=original"
        f"&titles={quote_plus(brand)}&redirects=1"
    )
    try:
        res = requests.get(search_url, timeout=10)
        res.raise_for_status()
        data = res.json()
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            if "original" in page:
                return page["original"]["source"]
    except Exception as e:
        logging.error(f"Error obteniendo imagen de Wikipedia: {e}")
    return None

