import streamlit as st

def local_css(file_name):
    """Carga un archivo CSS local para personalizar la app."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"No se pudo cargar CSS: {e}")


def resumen_proximos_mantenimientos(km):
    """Devuelve un resumen básico de próximos mantenimientos según km."""
    resumen = "Próximos mantenimientos recomendados:\n"
    if km < 10000:
        resumen += "- Revisión inicial del motor y niveles.\n"
    elif km < 50000:
        resumen += "- Cambio de aceite y filtros.\n"
        resumen += "- Revisión frenos y suspensión.\n"
    elif km < 100000:
        resumen += "- Revisión completa de motor y transmisión.\n"
        resumen += "- Revisión frenos, suspensión y neumáticos.\n"
    else:
        resumen += "- Revisión integral (motor, transmisión, frenos, suspensión, neumáticos).\n"
    return resumen


def recomendaciones_itv_detalladas(edad, km, combustible):
    """
    Devuelve checklist detallado de inspección previa a la ITV según:
    - Antigüedad del vehículo
    - Kilometraje
    - Tipo de combustible
    """
    checklist = []

    # Seguridad
    if km > 100000 or edad > 10:
        checklist.append(("Revisar motor y transmisión", "Seguridad"))
        checklist.append(("Revisar frenos, suspensión y dirección", "Seguridad"))

    # Carrocería
    if edad > 5:
        checklist.append(("Revisar corrosión, chasis y carrocería", "Carrocería"))

    # Neumáticos y ruedas
    if km > 20000:
        checklist.append(("Revisar desgaste de neumáticos y presión", "Seguridad"))

    # Electricidad y luces
    checklist.append(("Comprobar alumbrado y sistemas eléctricos", "Electricidad"))

    # Emisiones y escape
    if combustible in ["Gasolina", "Diésel"]:
        checklist.append(("Revisar sistema de escape y emisiones", "Emisiones"))
    elif combustible in ["Híbrido", "Eléctrico"]:
        checklist.append(("Revisar batería y sistemas eléctricos", "Electricidad"))

    # Aceite y líquidos
    checklist.append(("Comprobar niveles de aceite, refrigerante y frenos", "Mantenimiento"))

    # Otros mantenimientos
    if km > 50000:
        checklist.append(("Revisión de correa de distribución", "Mantenimiento"))
    if km > 80000:
        checklist.append(("Revisión de la bomba de agua y transmisión", "Mantenimiento"))

    return checklist








