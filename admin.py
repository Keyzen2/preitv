from fastapi import FastAPI, HTTPException
import json
import os

app = FastAPI(title="Admin API - Ciudades")

# Ruta al archivo JSON
CITIES_FILE = os.path.join(os.path.dirname(__file__), "data", "ciudades_coords.json")

def load_cities():
    with open(CITIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cities(cities):
    with open(CITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cities, f, indent=4, ensure_ascii=False)

@app.get("/ciudades")
def listar_ciudades():
    """Lista todas las ciudades con sus coordenadas"""
    return load_cities()

@app.get("/ciudades/{nombre}")
def obtener_ciudad(nombre: str):
    """Obtiene coordenadas de una ciudad"""
    cities = load_cities()
    ciudad = cities.get(nombre)
    if not ciudad:
        raise HTTPException(status_code=404, detail="Ciudad no encontrada")
    return {nombre: ciudad}

@app.post("/ciudades")
def agregar_ciudad(nombre: str, lat: float, lon: float):
    """Agrega una nueva ciudad"""
    cities = load_cities()
    if nombre in cities:
        raise HTTPException(status_code=400, detail="Ciudad ya existe")
    cities[nombre] = [lat, lon]
    save_cities(cities)
    return {"mensaje": "Ciudad agregada", nombre: [lat, lon]}

@app.put("/ciudades/{nombre}")
def actualizar_ciudad(nombre: str, lat: float, lon: float):
    """Actualiza coordenadas de una ciudad"""
    cities = load_cities()
    if nombre not in cities:
        raise HTTPException(status_code=404, detail="Ciudad no encontrada")
    cities[nombre] = [lat, lon]
    save_cities(cities)
    return {"mensaje": "Ciudad actualizada", nombre: [lat, lon]}

@app.delete("/ciudades/{nombre}")
def eliminar_ciudad(nombre: str):
    """Elimina una ciudad"""
    cities = load_cities()
    if nombre not in cities:
        raise HTTPException(status_code=404, detail="Ciudad no encontrada")
    coords = cities.pop(nombre)
    save_cities(cities)
    return {"mensaje": "Ciudad eliminada", nombre: coords}
