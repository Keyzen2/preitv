
import streamlit as st
import requests
import json
from datetime import date
from pathlib import Path
from PIL import Image

st.set_page_config(page_title="PreITV.com", page_icon="🚗", layout="centered")

PRIMARY = "#1A237E"
SECONDARY = "#43A047"
BG = "#F5F5F5"

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
hr {{ border: none; border-top: 1px solid rgba(0,0,0,.08); margin: 18px 0; }}
.small {{
  font-size: 13px; color: #444;
}}
</style>
""", unsafe_allow_html=True)

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

@st.cache_data(ttl=60*60)
def get_makes():
    url = f"{API_BASE}/GetAllMakes?format=json"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    results = r.json().get("Results", [])
    makes = sorted({(m.get("Make_Name") or "").title() for m in results if m.get("Make_Name")})
    return makes

@st.cache_data(ttl=60*60)
def get_models_for_make(make):
    url = f"{API_BASE}/GetModelsForMake/{make}?format=json"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    results = r.json().get("Results", [])
    models = sorted({(m.get("Model_Name") or "").title() for m in results if m.get("Model_Name")})
    return models

@st.cache_data
def load_rules():
    with open("data/maintenance_rules.json", "r", encoding="utf-8") as f:
        return json.load(f)

rules = load_rules()

with st.form("veh_form"):
    st.subheader("1) Datos del vehículo")
    try:
        makes = get_makes()
    except Exception as e:
        st.error("No se han podido cargar las marcas desde la API VPIC.")
        st.stop()

    default_idx = makes.index("Volkswagen") if "Volkswagen" in makes else 0
    make = st.selectbox("Marca", makes, index=default_idx)

    try:
        models = get_models_for_make(make) if make else []
    except Exception:
        models = []

    model = st.selectbox("Modelo", models if models else ["(No disponible)"])

    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Año de matriculación", min_value=1980, max_value=date.today().year, value=2018, step=1)
    with col2:
        fuel = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

    km = st.slider("Kilometraje aproximado (km)", 0, 350000, 90000, 5000)
    submitted = st.form_submit_button("Generar checklist")

if submitted:
    age = date.today().year - int(year)
    st.subheader(f"2) Checklist Pre-ITV para {make} {model} ({age} años, {km} km, {fuel})")

    def pick_age_tasks(age_bands, years):
        for band in age_bands:
            if years <= band["max_years"]:
                return list(band["tasks"])
        return list(age_bands[-1]["tasks"])

    tasks = pick_age_tasks(rules["age_bands"], age)
    tasks += rules["fuel_overrides"].get(fuel, [])

    for tip in rules["mileage_tips"]:
        if km >= tip["min_km"]:
            tasks += tip["tips"]

    tasks += rules["brand_specific"].get(make.title(), [])

    seen, dedup = set(), []
    for t in tasks:
        if t not in seen:
            seen.add(t)
            dedup.append(t)

    for t in dedup:
        st.markdown(f"<div class='card'>✅ {t}</div>", unsafe_allow_html=True)

    st.info("Consejo: lleva el vehículo limpio, presión correcta y documentación (permiso de circulación y seguro).")

st.markdown("<div class='footer'>© 2025 PreITV.com · Datos: VPIC (NHTSA). Listado orientativo.</div>", unsafe_allow_html=True)
