import requests
import logging
from urllib.parse import quote_plus
import streamlit as st
import unicodedata
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

def normalize_city(city: str):
    """Normaliza el nombre de la ciudad quitando acentos y espacios extras."""
    city = city.strip()
    city = unicodedata.normalize('NFKD', city).encode('ASCII', 'ignore').decode('utf-8')
    return city

@st.cache_data(ttl=3600)
def search_workshops(city: str, limit: int = 5):
    """Busca talleres mecánicos (amenity=car_repair) en España usando Overpass API."""
    if not city:
        return []

    city_norm = normalize_city(city)

    overpass_endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]

    query_area = f"""
    [out:json][timeout:25];
    area
      ["boundary"="administrative"]
      ["name"="{city_norm}"]
      ["ISO3166-1"="ES"]
      ["admin_level"~"^(8|9|10)$"];
    (node["amenity"="car_repair"](area);
     way["amenity"="car_repair"](area);
     relation["amenity"="car_repair"](area););
    out center tags;
    """

    query_place = f"""
    [out:json][timeout:25];
    node["amenity"="car_repair"]["place"="city"]["name"="{city_norm}"];
    out center tags;
    """

    for endpoint in overpass_endpoints:
        try:
            # Intentamos primero por área administrativa
            res = requests.post(endpoint, data={"data": query_area}, timeout=25)
            res.raise_for_status()
            data = res.json()
            elements = data.get("elements", [])
            if elements:
                break  # si encontramos resultados, salimos del loop

            # Si no hay resultados, buscamos por place=city
            res = requests.post(endpoint, data={"data": query_place}, timeout=25)
            res.raise_for_status()
            data = res.json()
            elements = data.get("elements", [])
            if elements:
                break
        except Exception as e:
            logging.warning(f"Overpass endpoint {endpoint} falló para {city}: {e}")
            elements = []

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

        street = tags.get("addr:street")
        housenumber = tags.get("addr:housenumber")
        postcode = tags.get("addr:postcode")
        city_tag = tags.get("addr:city") or city
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
    items = sorted(items, key=lambda x: (-x["score"], (x["name"] or "ZZZZ")))
    return items[:limit]








