import requests
import logging
import unicodedata
from urllib.parse import quote_plus
import streamlit as st
from config import EUROPEAN_MAKES

# -----------------------------
# Funciones de vehículos
# -----------------------------
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
    makes_filtradas = sorted([m for m in makes_api if m.lower() in [em.lower() for em in EUROPEAN_MAKES]])
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

# -----------------------------
# Funciones de talleres
# -----------------------------
def normalize_name(name):
    """Quita acentos y normaliza el nombre de la ciudad."""
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

def procesar_talleres(elements):
    """Procesa los elementos obtenidos de Overpass y devuelve información de talleres."""
    def extract(el):
        tags = el.get("tags", {}) or {}
        name = tags.get("name")
        phone = tags.get("phone") or tags.get("contact:phone")
        website = tags.get("website") or tags.get("contact:website")
        opening_hours = tags.get("opening_hours")

        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center") or {}
            lat, lon = center.get("lat"), center.get("lon")

        street = tags.get("addr:street")
        housenumber = tags.get("addr:housenumber")
        postcode = tags.get("addr:postcode")
        city_tag = tags.get("addr:city") or ""
        address = None
        if street or housenumber or postcode or city_tag:
            parts = []
            if street:
                parts.append(street)
            if housenumber:
                parts.append(housenumber)
            if postcode or city_tag:
                parts.append(f"{postcode or ''} {city_tag}".strip())
            address = ", ".join(parts)

        score = 0
        if name: score += 3
        if phone: score += 2
        if website: score += 1
        if opening_hours: score += 1
        if tags.get("brand"): score += 1

        return {
            "name": name,
            "phone": phone,
            "website": website,
            "opening_hours": opening_hours,
            "address": address,
            "lat": lat,
            "lon": lon,
            "score": score
        }

    items = [extract(e) for e in elements]
    return sorted(items, key=lambda x: (-x["score"], x.get("name") or "ZZZZ"))

@st.cache_data(ttl=3600)
def search_workshops(city, limit=5):
    """
    Busca talleres mecánicos en una ciudad de España usando Overpass API.
    Arranca directamente de un área administrativa o place=city|town para maximizar resultados.
    """
    if not city:
        return []

    city_norm = normalize_name(city)

    # Query: buscar área administrativa o place=city/town y luego talleres dentro
    query_area = f"""
    [out:json][timeout:25];
    area["name"="{city}"]["place"~"city|town"]["boundary"="administrative"];
    (node["amenity"="car_repair"](area);
     way["amenity"="car_repair"](area);
     relation["amenity"="car_repair"](area););
    out center tags;
    """

    ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.nchc.org.tw/api/interpreter"
    ]

    elements = []
    for ep in ENDPOINTS:
        try:
            res = requests.post(ep, data={"data": query_area}, timeout=25)
            res.raise_for_status()
            data = res.json()
            if data.get("elements"):
                elements = data["elements"]
                break
        except Exception as e:
            logging.warning(f"Overpass endpoint {ep} falló: {e}")

    return procesar_talleres(elements)[:limit]








