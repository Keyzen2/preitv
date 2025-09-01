import os
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from database import get_all_users, get_all_routes, save_config, get_config


# -----------------------------
# Logo
# -----------------------------
def save_logo(uploaded_file):
    assets_dir = "assets"
    os.makedirs(assets_dir, exist_ok=True)
    file_path = os.path.join(assets_dir, "logo.png")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    save_config("logo_path", file_path)
    return file_path


def load_logo():
    logo_path = get_config("logo_path")
    if logo_path and os.path.exists(logo_path):
        return logo_path
    return "assets/logo.png"  # logo por defecto


# -----------------------------
# Estadísticas
# -----------------------------
def mostrar_estadisticas():
    users = get_all_users()
    rutas = get_all_routes()

    st.subheader("📊 Estadísticas de la aplicación")
    col1, col2 = st.columns(2)
    col1.metric("Usuarios registrados", len(users))
    col2.metric("Rutas guardadas", len(rutas))

    if rutas:
        df = pd.DataFrame(rutas, columns=[
            "id", "user_id", "origen", "destino", "distancia", "duracion", "consumo", "coste", "fecha"
        ])

        # Gráfico: evolución de rutas
        df["fecha"] = pd.to_datetime(df["fecha"])
        rutas_por_fecha = df.groupby(df["fecha"].dt.date).size()

        fig, ax = plt.subplots()
        rutas_por_fecha.plot(kind="line", ax=ax, marker="o")
        ax.set_title("Evolución de rutas guardadas")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Nº rutas")
        st.pyplot(fig)

        # Consumo medio
        consumo_medio = df["consumo"].mean()
        coste_medio = df["coste"].mean()
        st.write(f"🔋 Consumo medio: **{consumo_medio:.2f} L**")
        st.write(f"💶 Coste medio: **{coste_medio:.2f} €**")
