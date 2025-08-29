import requests
import logging

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

def get_route(origin, destination):
    """
    Obtiene la ruta entre dos puntos usando OSRM.
    origin y destination son tuplas (lon, lat) en formato decimal.
    Devuelve distancia en km, duración en minutos y lista de coordenadas.
    """
    try:
        coords = f"{origin[0]},{origin[1]};{destination[0]},{destination[1]}"
        url = f"{OSRM_URL}/{coords}?overview=full&geometries=geojson"
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()
        if not data.get("routes"):
            return None
        route = data["routes"][0]
        distancia_km = route["distance"] / 1000
        duracion_min = route["duration"] / 60
        coords_linea = route["geometry"]["coordinates"]
        return distancia_km, duracion_min, coords_linea
    except Exception as e:
        logging.error(f"Error obteniendo ruta OSRM: {e}")
        return None

def calcular_coste(distancia_km, consumo_l_100km, precio_litro):
    """
    Calcula el coste estimado de combustible.
    consumo_l_100km: litros cada 100 km
    precio_litro: euros por litro
    """
    litros_totales = (distancia_km * consumo_l_100km) / 100
    coste_total = litros_totales * precio_litro
    return round(litros_totales, 2), round(coste_total, 2)