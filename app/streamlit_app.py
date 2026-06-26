"""
app/streamlit_app.py - Prototipo de frontend (issue #11, P11E4)

Prototipo NAVEGABLE con DATOS MOCK. La interfaz no depende del modelo:
cuando Persona 2 (pipeline + informe) y Persona 3 (base de datos) estEn
listos, solo se sustituye la seccion "FUENTE DE DATOS (MOCK)" por las
consultas reales; el resto de la UI no se toca.

Ejecutar:
    uv run streamlit run app/streamlit_app.py

Dependencias (ya en el entorno del proyecto): streamlit, pandas, pillow.
"""

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw

# ------------------------------------------------------------------ #
# FUENTE DE DATOS (MOCK)  <-- UNICO punto que Persona 2/3 sustituiran
# ------------------------------------------------------------------ #
# Resumen agregado por marca (lo produce el informe de Persona 2):
RESUMEN_MARCAS = [
    {"marca": "nike",      "segundos_aparicion": 42.5, "pct_video": 17.3},
    {"marca": "coca-cola", "segundos_aparicion": 18.0, "pct_video":  7.3},
    {"marca": "adidas",    "segundos_aparicion":  9.5, "pct_video":  3.9},
]

# Detecciones individuales con su recorte (lo guarda la BD de Persona 3):
DETECCIONES = [
    {"video": "demo.mp4", "marca": "nike",      "segundo":  3.2, "confianza": 0.94, "ruta_recorte": "outputs/crops/nike_0001.jpg"},
    {"video": "demo.mp4", "marca": "coca-cola", "segundo": 12.8, "confianza": 0.88, "ruta_recorte": "outputs/crops/coca_0001.jpg"},
    {"video": "demo.mp4", "marca": "adidas",    "segundo": 27.1, "confianza": 0.79, "ruta_recorte": "outputs/crops/adidas_0001.jpg"},
    {"video": "demo.mp4", "marca": "nike",      "segundo": 41.0, "confianza": 0.91, "ruta_recorte": "outputs/crops/nike_0002.jpg"},
]

# Color por marca, solo para las miniaturas de marcador de posicion.
COLORES_MARCA = {"nike": (33, 33, 33), "coca-cola": (196, 30, 58), "adidas": (0, 102, 204)}
# ------------------------------------------------------------------ #


def placeholder_recorte(marca: str, confianza: float, size=(200, 150)) -> Image.Image:
    """Genera al vuelo una miniatura de marcador de posicion (sin archivos ni red).
    Para datos reales, esta funcion se reemplaza por: Image.open(ruta_recorte)."""
    color = COLORES_MARCA.get(marca, (90, 90, 90))
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    draw.multiline_text((12, 12), f"{marca}\n{confianza:.0%}", fill=(255, 255, 255))
    return img


def main():
    st.set_page_config(page_title="Deteccion de marcas - P11E4", layout="wide")

    st.title("Deteccion de marcas en video")
    st.caption("Prototipo (issue #11) - datos de ejemplo; el pipeline real aun no esta conectado.")

    col_sub, col_info = st.columns([2, 1])
    with col_sub:
        video = st.file_uploader("Sube un video", type=["mp4"])
    with col_info:
        st.info("Demo con datos de ejemplo. Sube un .mp4 y pulsa **Analizar video**.")

    if not st.button("Analizar video", type="primary"):
        return

    if video is None:
        st.warning("Selecciona primero un video .mp4 para analizar.")
        return

    st.success(f"Analizado: {video.name} (resultado de ejemplo).")

    st.subheader("Resumen por marca")
    df = pd.DataFrame(RESUMEN_MARCAS).rename(columns={
        "marca": "Marca",
        "segundos_aparicion": "Tiempo en pantalla (s)",
        "pct_video": "% del video",
    })
    st.dataframe(df, hide_index=True, use_container_width=True)

    st.subheader("Recortes detectados")
    columnas = st.columns(4)
    for i, det in enumerate(DETECCIONES):
        with columnas[i % 4]:
            st.image(
                placeholder_recorte(det["marca"], det["confianza"]),
                caption=f'{det["marca"]} - {det["confianza"]:.0%} - t={det["segundo"]:.1f}s',
            )


if __name__ == "__main__":
    main()
