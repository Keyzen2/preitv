import datetime
import streamlit as st
from config import APP_TITLE, APP_ICON
from services.api import get_makes, get_models, get_brand_image
from utils.helpers import local_css, recomendaciones_itv_detalladas

# Diccionario de enlaces oficiales por marca
ENLACES_MANTENIMIENTO = {
    "Audi": "https://www.audi.es/es/web/es/servicio/audi-service/mantenimiento.html",
    "BMW": "https://www.bmw.es/es/topics/servicios/mantenimiento.html",
    "Citroen": "https://www.citroen.es/servicios-citroen/mantenimiento.html",
    "Dacia": "https://www.dacia.es/servicios-y-accesorios/mantenimiento.html",
    "Fiat": "https://www.fiat.es/servicios/mantenimiento",
    "Ford": "https://www.ford.es/propietario/revision-y-mantenimiento/servicio/mi-plan-de-mantenimiento",
    "Mercedes-Benz": "https://www.mercedes-benz.es/passengercars/being-an-owner/vehicle-care/maintenance.html",
    "Opel": "https://www.opel.es/servicios/mantenimiento.html",
    "Peugeot": "https://www.peugeot.es/servicios-y-accesorios/mantenimiento.html",
    "Renault": "https://www.renault.es/posventa/mantenimiento.html",
    "SEAT": "https://www.seat.es/posventa/mantenimiento.html",
    "Skoda": "https://www.skoda.es/servicios/mantenimiento",
    "Volkswagen": "https://www.volkswagen.es/es/servicio-postventa/mantenimiento.html",
    "Volvo": "https://www.volvocars.com/es/own/maintenance",
    "Alfa Romeo": "https://www.alfaromeo.es/servicios/mantenimiento",
    "Mini": "https://www.mini.es/es_ES/home/servicios/servicio-mini/mantenimiento.html",
    "Porsche": "https://www.porsche.com/spain/accessoriesandservice/porscheservice/vehicleinformation/maintenance/",
    "Jaguar": "https://www.jaguar.es/ownership/service-warranties/maintenance.html",
    "Land Rover": "https://www.landrover.es/ownership/service-warranties/maintenance.html"
}

# Configuración
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# Inicializar histórico
if "historial" not in st.session_state:
    st.session_state.historial = []

# UI principal
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo con enlace oficial de mantenimiento.")

# Filtrar marcas por las que tienen enlace oficial
with st.spinner("Cargando marcas..."):
    makes = [m for m in get_makes() if m in ENLACES_MANTENIMIENTO.keys()]

marca = st.selectbox("Marca", options=makes, index=None, placeholder="Elige una marca")
modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos, index=None, placeholder="Elige un modelo")

# Datos para checklist ITV
anio = st.number_input("Año de matriculación", min_value=1980, max_value=datetime.date.today().year)
km = st.number_input("Kilometraje", min_value=0, step=1000)
combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Buscar información"):
        if marca and modelo:
            st.success(f"Has seleccionado **{marca} {modelo}**")

            # Imagen genérica de la marca
            img_url = get_brand_image(marca)
            if img_url:
                st.image(img_url, caption=f"{marca}", use_column_width=True)
            else:
                st.info("No se encontró imagen para esta marca.")

            # Generar recomendaciones
            edad = datetime.date.today().year - anio
            st.session_state.checklist = recomendaciones_itv_detalladas(edad, km, combustible)

            # Guardar en histórico
            registro = {
                "marca": marca,
                "modelo": modelo,
                "anio": anio,
                "km": km,
                "combustible": combustible
            }
            if registro not in st.session_state.historial:
                st.session_state.historial.append(registro)
        else:
            st.warning("Selecciona una marca y modelo válido.")

with col2:
    if st.button("📜 Coches consultados"):
        if st.session_state.historial:
            st.subheader("Histórico de coches consultados en esta sesión")
            for item in st.session_state.historial:
                st.markdown(f"**{item['marca']} {item['modelo']}** — {item['anio']} — {item['km']} km — {item['combustible']}")
        else:
            st.info("Aún no has consultado ningún coche.")

# Mostrar checklist
if "checklist" in st.session_state and st.session_state.checklist:
    st.subheader("✅ Recomendaciones antes de la ITV")
    for tarea in st.session_state.checklist:
        st.write(f"• {tarea}")

    # Nota aclaratoria con enlace dinámico
    enlace = ENLACES_MANTENIMIENTO.get(marca)
    if enlace:
        st.markdown(f"""
**ℹ️ Nota:** Estas recomendaciones son orientativas y están basadas en guías de mantenimiento publicadas por medios especializados (Autopista, Feu Vert, Autofácil...).  
Para conocer el **plan de mantenimiento oficial** de tu vehículo, consulta siempre el manual del fabricante o su portal de servicio posventa:  
👉 [Plan oficial de mantenimiento de {marca}]({enlace})
        """)
    else:
        st.markdown("""
**ℹ️ Nota:** Estas recomendaciones son orientativas y están basadas en guías de mantenimiento publicadas por medios especializados (Autopista, Feu Vert, Autofácil...).  
Para conocer el **plan de mantenimiento oficial** de tu vehículo, consulta siempre el manual del fabricante o su portal de servicio posventa.
        """)
