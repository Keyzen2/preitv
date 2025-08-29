def recomendaciones_itv(edad, km, combustible):
    recomendaciones = []

    if km >= 5000:
        recomendaciones.append("Revisar nivel de aceite, fugas y neumáticos — Evita desgaste prematuro")
    if km >= 10000:
        recomendaciones.append("Alineación, balanceo y rotación de neumáticos — Mantiene estabilidad")
    if km >= 15000:
        recomendaciones.append("Cambio de aceite y filtro, revisión frenos y batería — Lubricación y frenado óptimos")
    if km >= 30000:
        recomendaciones.append("Cambio de pastillas de freno, revisión discos — Mejora frenado")
    if km >= 40000 and combustible.lower() == "gasolina":
        recomendaciones.append("Sustituir bujías y revisar encendido — Optimiza combustión")
    if km >= 60000:
        recomendaciones.append("Cambio de filtro de aire y combustible, revisar correa distribución — Previene averías graves")
    if km >= 100000:
        recomendaciones.append("Sustituir correa distribución y revisar refrigeración — Evita rotura de motor")

    if edad >= 4:
        recomendaciones.append("Comprobar luces, señalización y suspensión — Requisitos ITV")
    if edad >= 8:
        recomendaciones.append("Inspección completa de frenos, dirección y chasis — Previene fallos estructurales")

    if combustible.lower() == "diésel":
        recomendaciones.append("Comprobar filtro de partículas (DPF) e inyección — Evita pérdida de potencia")
    elif combustible.lower() == "híbrido":
        recomendaciones.append("Revisar batería híbrida y sistema eléctrico — Mantiene autonomía")
    elif combustible.lower() == "eléctrico":
        recomendaciones.append("Comprobar batería de tracción y sistema de carga — Asegura rendimiento")

    return recomendaciones
