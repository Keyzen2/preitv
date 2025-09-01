# PreITV App

**PreITV** es una aplicación web que permite a los usuarios consultar información de vehículos y planificar rutas entre ciudades de España.  
El login es opcional: cualquier persona puede acceder a la app, pero solo los usuarios registrados podrán **guardar búsquedas de vehículos y rutas** en Supabase.

---

## 🔹 Funcionalidades

- Consultar información de vehículos por marca, modelo, año y combustible.  
- Recibir recomendaciones antes de la ITV según edad del vehículo, kilometraje y tipo de combustible.  
- Planificar rutas entre ciudades españolas con cálculo de distancia, tiempo estimado, consumo y coste.  
- Guardar historial de consultas y rutas **solo para usuarios registrados**.  
- Panel de usuario para cambiar nombre y contraseña.  
- Eliminada la búsqueda de talleres, será incorporada más adelante con API de registro.

> ⚠️ Mensaje destacado en la app:  
> "Si quieres guardar tus búsquedas y rutas, regístrate en la app."

---

## 🔹 Requisitos

- Python 3.13+
- Instalar dependencias:

```bash
pip install -r requirements.txt

