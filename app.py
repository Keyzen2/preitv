import os
import streamlit as st
import requests
import json
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus
from PIL import Image

# If you moved .streamlit to streamlit/, force Streamlit to use that config
os.environ["STREAMLIT_CONFIG_FILE"] = os.path.join(os.path.dirname(__file__), "streamlit", "config.toml")

st.set_page_config(page_title="PreITV.com", page_icon="🚗", layout="centered")

PRIMARY = "#1A237E"
SECONDARY = "#43A047"
BG = "#F5F5F5"

# ------ Styles (branding) ------
st.markdown(f"""
<style>
:root {{
  --primary: {PRIMARY};
  --secondary: {SECONDARY};
  --bg: {BG};
}}
html, body, [class*="css"]  {{
  background-color: var(--bg) !important;
}}
h1,h2,h3,h4 {{
  color: var(--primary);
  font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, sans-serif;
}}
p,li,div,span {{
  font-family: 'Open Sans', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, sans-serif;
}}
.hero {{
  background: linear-gradient(135deg, rgba(26,35,126,.05), rgba(67,160,71,.05));
  border: 1px solid rgba(0,0,0,.05);
  border-radius: 20px;
  padding: 20px;
  margin: 10px 0 20px;
  box-shadow: 0 10px 30px rgba(0,0,0,.06);
}}
.cta-btn > button {{
  background-color: var(--primary);
  color: #fff;
  border-radius: 12px;
  font-weight: 700;
  padding: 10px 18px;
  transition: transform .12s ease, box-shadow .12s ease, background .2s ease;
  box-shadow: 0 6px 14px rgba(26,35,126,.22);
}}
.cta-btn > button:hover {{
  background-color: var(--secondary);
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(67,160,71,.25);
}}
.card {{
  background: #fff;
  border-radius: 18px;
  padding: 16px 18px;
  margin: 8px 0;
  box-shadow: 0 6px 18px rgba(0,0,0,.08);
  border: 1px solid rgba(0,0,0,.06);
  transition: transform .12s ease, box-shadow .12s ease;
}}
.card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 12px 26px rgba(0,0,0,.12);
}}
.badge {{
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(67,160,71,.1);
  color: var(--secondary);
  font-weight: 700;
  font-size: 12px;
  margin-left: 8px;
  border: 1px solid rgba(67,160,71,.2);
}}
.footer {{
  color: #555; font-size: 13px; text-align: center; margin-top: 30px;
}}
.small {{
  font-size: 13px; color: #444;
}}
</style>
""", unsafe_allow_html=True)

# ------ Logo & header ------
logo_path = Path("assets/logo.png")
if logo_path.exists():
    st.image(str(logo_path), width=200)

st.title("PreITV.com")
st.markdown("""
<div class="hero">
  <h3>Revisa antes de la ITV, conduce con confianza 🚗<span class="badge">Beta</span></h3>
  <p class="small">Introduce los datos de tu vehículo y genera un checklist personalizado con los puntos a revisar antes de la ITV. Datos de marcas y modelos en tiempo real vía VPIC (NHTSA).</p>
</div>
""", unsafe_allow_html=True)

API_BASE = "https://vpic.nhtsa.dot.gov/api/vehicles"

# ------ Helpers: VPIC requests with caching ------
@st.cache_data(ttl=60*60)
def get_makes():
    """Return sorted list of make names (title-cased)."""
    url = f"{API_BASE}/GetAllMakes?format=json"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json().get("Results", [])
        makes = sorted({(m.get("Make_Name") or "").title() for m in data if m.get("Make_Name")})
        return makes
    except Exception as e:
        st.session_state.setdefault("_vpic_error", str(e))
        return []

@st.cache_data(ttl=60*60)
def get_models_for_make(make_name: str):
    """Return sorted unique models for a given make. URL-encodes the make."""
    if not make_name:
        return []
    encoded = quote_plus(make_name)
    url = f"{API_BASE}/GetModelsForMake/{encoded}?format=json"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json().get("Results", [])
        models = sorted({(m.get("Model_Name") or "").title() for m in data if m.get("Model_Name")})
        return models
    except Exception as e:
        st.session_state.setdefault("_vpic_error", str(e))
        return []

@st.cache_data
def load_rules():
    p = Path("data/maintenance_rules.json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    # fallback minimal rules if file missing
    return {
        "age_bands": [
            {"max_years": 5, "tasks": ["Niveles, luces, neumáticos, frenos"]},
            {"max_years": 15, "tasks": ["Todo lo anterior + suspensión y batería"]},
            {"max_years": 100, "tasks": ["Revisión completa mecánica y carrocería"]}
        ],
        "fuel_overrides": {},
        "mileage_tips": [],
        "brand_specific": {}
    }

rules = load_rules()

# ------ Form (brand -> models dynamically) ------
with st.form("veh_form"):
    st.subheader("1) Datos del vehículo")
    makes = get_makes()
    if not makes:
        vpic_err = st.session_state.get("_vpic_error", None)
        st.error("No se han podido cargar las marcas desde VPIC. " + (f"Error: {vpic_err}" if vpic_err else ""))
        st.stop()

    default_idx = makes.index("Volkswagen") if "Volkswagen" in makes else 0
    make = st.selectbox("Marca", makes, index=default_idx, key="make_select")

    # Fetch models for the chosen make (dynamically)
    # Note: Streamlit reruns the script on widget change, so this will update the models list automatically.
    models = get_models_for_make(make)
    if not models:
        model = st.selectbox("Modelo", ["(No disponible)"])
        st.info("No hay modelos disponibles para esta marca en la API o la API no respondió.")
    else:
        model = st.selectbox("Modelo", models)

    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Año de matriculación", min_value=1980, max_value=date.today().year, value=2018, step=1)
    with col2:
        fuel = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

    km = st.slider("Kilometraje aproximado (km)", 0, 350000, 90000, 5000)
    submitted = st.form_submit_button("Generar checklist")

# ------ Results / Rule engine ------
if submitted:
    age = date.today().year - int(year)
    st.subheader(f"2) Checklist Pre-ITV para {make} {model} ({age} años, {km} km, {fuel})")

    def pick_age_tasks(age_bands, years):
        for band in age_bands:
            if years <= band["max_years"]:
                return list(band["tasks"])
        return list(age_bands[-1]["tasks"])

    tasks = pick_age_tasks(rules.get("age_bands", []), age)
    tasks += rules.get("fuel_overrides", {}).get(fuel, [])

    for tip in rules.get("mileage_tips", []):
        if km >= tip.get("min_km", 0):
            tasks += tip.get("tips", [])

    # brand-specific (case-insensitive match)
    brand_tasks = rules.get("brand_specific", {}).get(make.title(), []) or rules.get("brand_specific", {}).get(make.lower(), [])
    if brand_tasks:
        tasks += brand_tasks

    # Deduplicate preserving order
    seen = set()
    dedup = []
    for t in tasks:
        if t not in seen:
            seen.add(t)
            dedup.append(t)

    if not dedup:
        st.info("No hay tareas específicas para estos parámetros. Revisión general: niveles, luces, neumáticos y frenos.")
    else:
        for t in dedup:
            st.markdown(f"<div class='card'>✅ {t}</div>", unsafe_allow_html=True)

    st.info("Consejo: lleva el vehículo limpio, presión correcta y documentación (permiso de circulación y seguro).")

st.markdown("<div class='footer'>© 2025 PreITV.com · Datos: VPIC (NHTSA). Listado orientativo.</div>", unsafe_allow_html=True)
