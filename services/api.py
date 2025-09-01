# Módulo para las APIs de marcas y modelos de vehículos

import requests

API_BASE = "https://parallelum.com.br/fipe/api/v1/carros"

def get_makes():
    try:
        res = requests.get(f"{API_BASE}/marcas")
        res.raise_for_status()
        data = res.json()
        return [item["nome"] for item in data]
    except:
        return []

def get_models(make_name):
    try:
        # Obtener código de marca
        res_marca = requests.get(f"{API_BASE}/marcas")
        marca = next((m for m in res_marca.json() if m["nome"] == make_name), None)
        if not marca:
            return []
        codigo = marca["codigo"]
        res_models = requests.get(f"{API_BASE}/marcas/{codigo}/modelos")
        res_models.raise_for_status()
        data = res_models.json()
        return [item["nome"] for item in data.get("modelos", [])]
    except:
        return []

