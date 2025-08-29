def recomendaciones_itv_detalladas(edad, km, combustible):
    """
    Devuelve lista de cadenas con recomendaciones de mantenimiento
    basadas en kilometraje y antigüedad, usando buenas prácticas comunes
    publicadas en medios especializados (Autopista, Feu Vert, Autofácil...).
    """

    recomendaciones = []

    # 5.000 km
    if km >= 5000:
        recomendaciones.append("Revisar nivel y estado del aceite del motor — Detectar fugas y evitar desgaste prematuro")
        recomendaciones.append("Comprobar estado de neumáticos — Grietas, deformaciones, dibujo mínimo")
        recomendaciones.append("Verificar funcionamiento de luces y limpiaparabrisas")

    # 10.000 km
    if km >= 10000:
        recomendaciones.append("Alineación y balanceo de ruedas — Evita desgaste irregular")
        recomendaciones.append("Rotación de neumáticos — Alarga su vida útil")
        recomendaciones.append("Revisión básica del sistema eléctrico — Batería y conexiones")

    # 15.000-20.000 km o 1 año
    if km >= 15000:
        recomendaciones.append("Cambio de aceite y filtro — Mantiene lubricación óptima")
        recomendaciones.append("Revisión de frenos — Grosor de pastillas y discos")
        recomendaciones.append("Verificación de batería y carga")
        recomendaciones.append("Sustituir filtro de aire y de habitáculo si procede")
        recomendaciones.append("Revisión electrónica en taller")

    # 30.000 km
    if km >= 30000:
        recomendaciones.append("Cambio de pastillas de freno si no se hizo antes")
        recomendaciones.append("Revisión de discos de freno")
        recomendaciones.append("Comprobación del sistema de climatización")

    # 40.000 km
    if km >= 40000:
        if combustible.lower() == "gasolina":
            recomendaciones.append("Sustituir bujías y revisar encendido")
        recomendaciones.append("Sustitución de líquido de frenos")
        recomendaciones.append("Revisión de amortiguadores, manguitos y latiguillos")

    # 60.000 km
    if km >= 60000:
        recomendaciones.append("Cambio de filtro de aire y combustible")
        recomendaciones.append("Revisión o sustitución de correa de distribución si aplica")
        recomendaciones.append("Revisión del sistema de refrigeración")

    # 80.000 km
    if km >= 80000:
        recomendaciones.append("Revisión del sistema de escape")
        recomendaciones.append("Sustitución de correa de distribución y accesorios si no se hizo antes")
        recomendaciones.append("Revisión de airbags (cada 5 años)")
        recomendaciones.append("Comprobación de batería (vida útil media 5 años)")
        recomendaciones.append("Revisión de carga de gas del aire acondicionado")

    # Edad del vehículo
    if edad >= 4:
        recomendaciones.append("Comprobar luces, señalización, suspensión y dirección — Requisitos ITV")
    if edad >= 8:
        recomendaciones.append("Inspección completa de frenos, dirección y chasis — Previene fallos estructurales")

    # Combustible específico
    if combustible.lower() == "diésel":
        recomendaciones.append("Comprobar filtro de partículas (DPF) e inyección — Evita pérdida de potencia y emisiones")
    elif combustible.lower() == "híbrido":
        recomendaciones.append("Revisar batería híbrida y sistema eléctrico — Mantiene autonomía")
    elif combustible.lower() == "eléctrico":
        recomendaciones.append("Comprobar batería de tracción y sistema de carga — Asegura rendimiento y autonomía")

    return recomendaciones
