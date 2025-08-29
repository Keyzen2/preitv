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
def normalize_name(name: str) -> str:
    """Quita acentos y normaliza cadenas."""
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

def procesar_talleres(elements):
    """Procesa los elementos obtenidos de Overpass y devuelve información de talleres."""
    talleres = []
    for el in elements:
        tags = el.get("tags", {}) or {}
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        street = tags.get("addr:street")
        housenumber = tags.get("addr:housenumber")
        postcode = tags.get("addr:postcode")
        city_tag = tags.get("addr:city") or ""
        address = None
        if street or housenumber or postcode or city_tag:
            parts = []
            if street: parts.append(street)
            if housenumber: parts.append(housenumber)
            if postcode or city_tag: parts.append(f"{postcode or ''} {city_tag}".strip())
            address = ", ".join(parts)
        score = 0
        if tags.get("name"): score += 3
        if tags.get("phone"): score += 2
        if tags.get("website"): score += 1
        if tags.get("opening_hours"): score += 1
        if tags.get("brand"): score += 1
        talleres.append({
            "name": tags.get("name"),
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "website": tags.get("website") or tags.get("contact:website"),
            "opening_hours": tags.get("opening_hours"),
            "address": address,
            "lat": lat,
            "lon": lon,
            "score": score
        })
    return sorted(talleres, key=lambda x: (-x["score"], x.get("name") or "ZZZZ"))

@st.cache_data(ttl=3600)
def search_workshops(city: str, limit: int = 5):
    """Busca talleres mecánicos en una ciudad de España usando Overpass con fallback."""
    if not city:
        return []

    city_norm = normalize_name(city)
    ENDPOINTS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.nchc.org.tw/api/interpreter"
    ]

    # Query principal: busca nodos/ways/relations con amenity=car_repair que contengan el nombre de la ciudad
    query_main = f"""
    [out:json][timeout:25];
    (
      node["amenity"="car_repair"]["name"~"{city_norm}", i];
      way["amenity"="car_repair"]["name"~"{city_norm}", i];
      relation["amenity"="car_repair"]["name"~"{city_norm}", i];
    );
    out center tags;
    """

    # Fallback: buscar por área administrativa
    query_fallback = f"""
    [out:json][timeout:25];
    area["name"~"{city}", i]["place"~"city|town"];
    (
      node["amenity"="car_repair"](area);
      way["amenity"="car_repair"](area);
      relation["amenity"="car_repair"](area);
    );
    out center tags;
    """

    elements = []
    for ep in ENDPOINTS:
        for q in [query_main, query_fallback]:
            try:
                res = requests.post(ep, data={"data": q}, timeout=25)
                res.raise_for_status()
                data = res.json()
                if data.get("elements"):
                    elements = data["elements"]
                    break
            except Exception as e:
                logging.warning(f"Overpass endpoint {ep} falló: {e}")
        if elements:
            break

    return procesar_talleres(elements)[:limit]
