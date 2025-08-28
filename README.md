
# PreITV.com — Versión Avanzada (Streamlit + VPIC + Reglas Pre-ITV)

App en Streamlit con **diseño moderno**, conexión a **VPIC (NHTSA)** para obtener **marcas y modelos reales**, y un **motor de reglas** para generar el checklist pre-ITV según **antigüedad, combustible y kilometraje**.

## Estructura
```
preitv_streamlit_advanced/
├─ app.py
├─ requirements.txt
├─ assets/
│  └─ logo.png
├─ data/
│  └─ maintenance_rules.json
└─ .streamlit/
   └─ config.toml
```

## Despliegue local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Despliegue en Streamlit Cloud
1. Sube esta carpeta a un repositorio de GitHub.
2. En Streamlit Cloud, crea una App y selecciona este repositorio.
3. Main file: `app.py`. Python 3.13 es compatible.

## Notas
- VPIC es internacional; puedes añadir filtrado para modelos comunes en España.
- Amplía `data/maintenance_rules.json` con tareas específicas por marca/modelo.
