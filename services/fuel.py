import requests
import logging
from math import radians, cos, sin, asin, sqrt

MITECO_URL = "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/"

def haversine(lon1, lat1, lon2, lat2):
    """Distancia en km entre dos coordenadas."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c

def get_fuel_prices():
    """Descarga listado de estaciones de servicio de MITECO."""
    try:
        res = requests.get(MITECO_URL, timeout=15)
        res.raise_for_status()
        data = res.json()
        return data.get("ListaEESSPrecio", [])
    except Exception as e:
        logging.error(f"Error obteniendo precios MITECO: {e}")
        return []

def filter_cheapest_on_route(stations, route_coords, fuel_type="Gasolina 95 E5", max_distance_km=5, limit=5):
    """
    Filtra estaciones cercanas a la ruta y devuelve las más baratas.
    - stations: lista de estaciones de MITECO
    - route_coords: lista [(lon, lat), ...] de la ruta OSRM
    - fuel_type: tipo de combustible a buscar
    - max_distance_km: distancia máxima a la ruta
    """
    candidates = []
    for st in stations:
        try:
            lat = float(st["Latitud"].replace(",", "."))
            lon = float(st["Longitud (WGS84)"].replace(",", "."))
            precio_str = st.get(f"Precio {fuel_type}")
            if not precio_str or precio_str.strip() == "":
                continue
            precio = float(precio_str.replace(",", "."))
            # Comprobar si está cerca de algún punto de la ruta
            for lon_r, lat_r in route_coords:
                if haversine(lon, lat, lon_r, lat_r) <= max_distance_km:
                    candidates.append({
                        "rotulo": st.get("Rótulo"),
                        "direccion": st.get("Dirección"),
                        "municipio": st.get("Municipio"),
                        "precio": precio,
                        "lat": lat,
                        "lon": lon
                    })
                    break
        except Exception:
            continue
    # Ordenar por precio ascendente
    candidates.sort(key=lambda x: x["precio"])
    return candidates[:limit]