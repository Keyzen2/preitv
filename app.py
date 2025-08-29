import datetime
from utils.helpers import local_css, recomendaciones_itv
from services.api import get_makes, get_models
from config import APP_TITLE, APP_ICON

# Config
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")
local_css("styles/theme.css")

# UI
st.title("🚗 Buscador de Vehículos (Versión PRO)")
st.write("Selecciona una marca y modelo disponible en Europa.")

# Selección Marca
with st.spinner("Cargando marcas..."):
    makes = get_makes()

marca = st.selectbox("Marca", options=makes, index=None)
modelos = get_models(marca) if marca else []
modelo = st.selectbox("Modelo", options=modelos, index=None)

# Datos para checklist ITV
anio = st.number_input("Año de matriculación", min_value=1980, max_value=datetime.date.today().year)
km = st.number_input("Kilometraje", min_value=0, step=1000)
combustible = st.selectbox("Combustible", ["Gasolina", "Diésel", "Híbrido", "Eléctrico"])

# Botón
if st.button("🔍 Buscar información"):
    if marca and modelo:
        st.success(f"Has seleccionado **{marca} {modelo}**")
        
        edad = datetime.date.today().year - anio
        checklist = recomendaciones_itv(edad, km, combustible)

        if checklist:
            st.subheader("✅ Recomendaciones antes de la ITV")
            for item in checklist:
                st.checkbox(item, value=False)
        else:
            st.info("No hay recomendaciones específicas para este vehículo.")
    else:
        st.warning("Selecciona una marca y modelo válido.")
