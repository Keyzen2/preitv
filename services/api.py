import requests
import logging
from urllib.parse import quote_plus
import streamlit as st
from config import EUROPEAN_MAKES

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

@st.cache_data(ttl=3600)
def search_workshops(city: str, limit: int = 5):
    """
    Busca talleres (amenity=car_repair) en una ciudad de España usando Overpass API.
    Devuelve hasta 'limit' resultados con nombre, dirección, teléfono, web, horario y coordenadas.
    """
    city = city.strip()
    if not city:
        return []

    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    area["boundary"="administrative"]["name"="{city}"]["ISO3166-1"="ES"]["admin_level"~"^(8|9|10)$"];
    (node["amenity"="car_repair"](area); way["amenity"="car_repair"](area); relation["amenity"="car_repair"](area););
    out center {limit};
    """

    try:
        res = requests.post(overpass_url, data={"data": query}, timeout=25)
        res.raise_for_status()
        data = res.json()
    except requests.RequestException as e:
        logging.error(f"Error Overpass para {city}: {e}")
        return []
    except ValueError:
        logging.error("Respuesta Overpass no es JSON válida.")
        return []

    elements = data.get("elements", [])
    if not elements:
        return []

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

        # Dirección
        street = tags.get("addr:street")
        housenumber = tags.get("addr:housenumber")
        postcode = tags.get("addr:postcode")
        city_tag = tags.get("addr:city") or city
        address = None
        if street or housenumber or postcode or city_tag:
            parts = []
            if street: parts.append(street)
            if housenumber: parts.append(housenumber)
            if postcode or city_tag: parts.append(f"{postcode or ''} {city_tag}".strip())
            address = ", ".join(parts)

        # Score heurístico
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
    items = sorted(items, key=lambda x: (-x["score"], (x["name"] or "ZZZZ")))
    return items[:limit]





