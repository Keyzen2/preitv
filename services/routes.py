# Módulo para cálculo de rutas y coste

import requests

def get_route(origin: tuple, destination: tuple):
    """Devuelve distancia, duración y coordenadas de línea entre dos puntos."""
    try:
        lon_o, lat_o = origin
        lon_d, lat_d = destination
        url = f"http://router.project-osrm.org/route/v1/driving/{lon_o},{lat_o};{lon_d},{lat_d}?overview=full&geometries=geojson"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        route = data["routes"][0]
        distancia_m = route["distance"]
        duracion_s = route["duration"]
        coords = route["geometry"]["coordinates"]
        return distancia_m / 1000, duracion_s / 60, coords
    except Exception as e:
        return None

def calcular_coste(distancia_km, consumo_l_100km, precio_l):
    litros = distancia_km * consumo_l_100km / 100
    coste = litros * precio_l
    return round(litros, 2), round(coste, 2)
