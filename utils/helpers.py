import streamlit as st

def local_css(file_name):
    """Carga el CSS local desde el archivo indicado."""
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def recomendaciones_itv_detalladas(edad, km, combustible):
    """
    Devuelve lista de tuplas (tarea, categoría).
    Categorías: 'Kilometraje', 'Edad del vehículo', 'Combustible específico', 'Otros'
    """
    recs = []

    # Kilometraje
    if km >= 5000:
        recs.append(("Revisar nivel y estado del aceite del motor — Detectar fugas y evitar desgaste prematuro", "Kilometraje"))
        recs.append(("Comprobar estado de neumáticos — Grietas, deformaciones, dibujo mínimo", "Kilometraje"))
        recs.append(("Verificar funcionamiento de luces y limpiaparabrisas", "Kilometraje"))

    if km >= 10000:
        recs.append(("Alineación y balanceo de ruedas — Evita desgaste irregular", "Kilometraje"))
        recs.append(("Rotación de neumáticos — Alarga su vida útil", "Kilometraje"))
        recs.append(("Revisión básica del sistema eléctrico — Batería y conexiones", "Otros"))

    if km >= 15000:
        recs.append(("Cambio de aceite y filtro — Mantiene lubricación óptima", "Kilometraje"))
        recs.append(("Revisión de frenos — Grosor de pastillas y discos", "Kilometraje"))
        recs.append(("Verificación de batería y carga", "Otros"))
        recs.append(("Sustituir filtro de aire y de habitáculo si procede", "Kilometraje"))
        recs.append(("Revisión electrónica en taller", "Otros"))

    if km >= 30000:
        recs.append(("Cambio de pastillas de freno si no se hizo antes", "Kilometraje"))
        recs.append(("Revisión de discos de freno", "Kilometraje"))
        recs.append(("Comprobación del sistema de climatización", "Otros"))

    if km >= 40000:
        if combustible.lower() == "gasolina":
            recs.append(("Sustituir bujías y revisar encendido", "Combustible específico"))
        recs.append(("Sustitución de líquido de frenos", "Kilometraje"))
        recs.append(("Revisión de amortiguadores, manguitos y latiguillos", "Otros"))

    if km >= 60000:
        recs.append(("Cambio de filtro de aire y combustible", "Kilometraje"))
        recs.append(("Revisión o sustitución de correa de distribución si aplica", "Kilometraje"))
        recs.append(("Revisión del sistema de refrigeración", "Otros"))

    if km >= 80000:
        recs.append(("Revisión del sistema de escape", "Otros"))
        recs.append(("Sustitución de correa de distribución y accesorios si no se hizo antes", "Kilometraje"))
        recs.append(("Revisión de airbags (cada 5 años)", "Otros"))
        recs.append(("Comprobación de batería (vida útil media 5 años)", "Otros"))
        recs.append(("Revisión de carga de gas del aire acondicionado", "Otros"))

    # Edad
    if edad >= 4:
        recs.append(("Comprobar luces, señalización, suspensión y dirección — Requisitos ITV", "Edad del vehículo"))
    if edad >= 8:
        recs.append(("Inspección completa de frenos, dirección y chasis — Previene fallos estructurales", "Edad del vehículo"))

    # Combustible
    if combustible.lower() == "diésel":
        recs.append(("Comprobar filtro de partículas (DPF) e inyección — Evita pérdida de potencia y emisiones", "Combustible específico"))
    elif combustible.lower() == "híbrido":
        recs.append(("Revisar batería híbrida y sistema eléctrico — Mantiene autonomía", "Combustible específico"))
    elif combustible.lower() == "eléctrico":
        recs.append(("Comprobar batería de tracción y sistema de carga — Asegura rendimiento y autonomía", "Combustible específico"))

    return recs

def resumen_proximos_mantenimientos(km):
    """Devuelve texto breve sobre próximos hitos de mantenimiento."""
    if km < 5000:
        return "Próximo hito: revisión básica a los 5.000 km."
    elif km < 10000:
        return "Próximo hito: alineación y rotación de ruedas a los 10.000 km."
    elif km < 15000:
        return "Próximo hito: revisión completa y cambio de aceite a los 15.000 km."
    elif km < 30000:
        return "Próximo hito: cambio de pastillas de freno a los 30.000 km."
    elif km < 40000:
        return "Próximo hito: sustitución de líquido de frenos a los 40.000 km."
    elif km < 60000:
        return "Próximo hito: cambio de filtros y revisión de correa a los 60.000 km."
    elif km < 80000:
        return "Próximo hito: revisión completa a los 80.000 km."
    else:
        return "Se han alcanzado la mayoría de hitos de mantenimiento importantes."






