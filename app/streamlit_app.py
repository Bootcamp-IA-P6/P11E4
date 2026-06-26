"""
app/streamlit_app.py
feat: conexión del frontend con el pipeline real (#12)
Ejecutar:
    uv run streamlit run app/streamlit_app.py
"""

import sys
import tempfile
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import subprocess
import shutil

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import BRAND_CLASSES, OUTPUTS_DIR
from src.database.db import (
    consultar_informe,
    consultar_intervalos,
    consultar_videos,
    init_db,
)
from src.run import main as run_pipeline

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Brand Detection — P11E4",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos globales ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fuente base */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* Título principal */
    h1 { 
        font-size: 2rem !important; 
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Subtítulos */
    h2 { 
        font-size: 1.2rem !important; 
        font-weight: 600 !important;
        color: #e0e0e0 !important;
        border-bottom: 1px solid #333;
        padding-bottom: 6px;
        margin-top: 1.5rem !important;
    }

    /* Métricas más grandes */
    [data-testid="metric-container"] {
        background: #1e1e2e;
        border: 1px solid #2e2e4e;
        border-radius: 12px;
        padding: 16px !important;
    }
    [data-testid="metric-container"] label {
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #888 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    /* Botón principal */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6c63ff, #48cae4);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 2rem;
        font-size: 1rem;
        transition: opacity 0.2s;
    }
    div.stButton > button[kind="primary"]:hover {
        opacity: 0.85;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #13131f;
    }

    /* Uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #333;
        border-radius: 12px;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── Colores por marca ─────────────────────────────────────────────────────────
BRAND_COLORS = {
    "nike":   "#48cae4",
    "adidas": "#6c63ff",
    "puma":   "#f77f00",
}

def get_color(brand: str) -> str:
    return BRAND_COLORS.get(brand.lower(), "#aaaaaa")


# ── Helpers de formato ────────────────────────────────────────────────────────
def fmt_seconds(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"{int(m)}m {s:.1f}s" if m else f"{s:.1f}s"


# ── Gráfica: barras de tiempo por marca ──────────────────────────────────────
def chart_tiempo_marca(informe: list[dict]) -> None:
    df = pd.DataFrame(informe)
    if df.empty or "tiempo_total_sec" not in df.columns:
        st.info("Sin datos suficientes para la gráfica.")
        return

    df = df[df["tiempo_total_sec"] > 0].sort_values("tiempo_total_sec", ascending=True)
    if df.empty:
        st.info("Ninguna marca detectada en este vídeo.")
        return

    fig = px.bar(
        df,
        x="tiempo_total_sec",
        y="marca",
        orientation="h",
        text=df["tiempo_total_sec"].apply(fmt_seconds),
        color="marca",
        color_discrete_map=BRAND_COLORS,
        labels={"tiempo_total_sec": "Tiempo en pantalla (s)", "marca": ""},
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        plot_bgcolor="#0e0e1a",
        paper_bgcolor="#0e0e1a",
        font_color="#e0e0e0",
        showlegend=False,
        margin=dict(l=10, r=30, t=10, b=10),
        height=220,
        xaxis=dict(gridcolor="#1e1e2e"),
        yaxis=dict(gridcolor="#1e1e2e"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Gráfica: donut de porcentajes ─────────────────────────────────────────────
def chart_donut(informe: list[dict]) -> None:
    df = pd.DataFrame(informe)
    if df.empty:
        return

    df = df[df["porcentaje"] > 0]
    if df.empty:
        return

    # Añadir "Sin marca" para completar el 100%
    resto = max(0.0, 100.0 - df["porcentaje"].sum())
    if resto > 0.5:
        df = pd.concat([
            df,
            pd.DataFrame([{"marca": "Sin marca", "porcentaje": round(resto, 2)}])
        ], ignore_index=True)

    colores = [get_color(m) for m in df["marca"]]

    fig = go.Figure(go.Pie(
        labels=df["marca"],
        values=df["porcentaje"],
        hole=0.6,
        marker=dict(colors=colores, line=dict(color="#0e0e1a", width=2)),
        textinfo="label+percent",
        textfont=dict(size=13),
    ))
    fig.update_layout(
        plot_bgcolor="#0e0e1a",
        paper_bgcolor="#0e0e1a",
        font_color="#e0e0e0",
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Gráfica: timeline de intervalos ──────────────────────────────────────────
def chart_timeline(intervalos: list[dict], duracion: float) -> None:
    if not intervalos:
        st.info("No hay intervalos para mostrar.")
        return

    df = pd.DataFrame(intervalos)
    df["duracion_sec"] = df["fin_sec"] - df["inicio_sec"]

    fig = px.timeline(
        df.assign(
            inicio_dt=pd.to_datetime(df["inicio_sec"], unit="s"),
            fin_dt=pd.to_datetime(df["fin_sec"], unit="s"),
        ),
        x_start="inicio_dt",
        x_end="fin_dt",
        y="marca",
        color="marca",
        color_discrete_map=BRAND_COLORS,
        hover_data={"confianza_avg": ":.0%", "duracion_sec": ":.1f"},
        labels={"marca": ""},
    )

    # Reformatear eje X como segundos reales
    tick_vals = list(range(0, int(duracion) + 1, max(1, int(duracion) // 8)))
    fig.update_layout(
        plot_bgcolor="#0e0e1a",
        paper_bgcolor="#0e0e1a",
        font_color="#e0e0e0",
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=220,
        xaxis=dict(
            title="Segundo del vídeo",
            gridcolor="#1e1e2e",
            tickformat="%S",
        ),
        yaxis=dict(gridcolor="#1e1e2e"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Sidebar — historial de vídeos ─────────────────────────────────────────────
def render_sidebar() -> int | None:
    """Muestra el historial y devuelve el video_id seleccionado o None."""
    with st.sidebar:
        st.markdown("## Historial")
        videos = consultar_videos()

        if not videos:
            st.caption("Aún no hay vídeos analizados.")
            return None

        opciones = {f"#{v['id']} — {v['nombre']}": v["id"] for v in videos}
        seleccion = st.radio(
            "Vídeos analizados",
            list(opciones.keys()),
            label_visibility="collapsed",
        )
        st.divider()
        st.caption(f"{len(videos)} vídeo(s) en la BD")
        return opciones[seleccion]

    return None


# ── Sección de resultados ─────────────────────────────────────────────────────
def render_resultados(video_id: int) -> None:
    videos = consultar_videos()
    video  = next((v for v in videos if v["id"] == video_id), None)
    if not video:
        st.error("Vídeo no encontrado en la BD.")
        return

    informe    = consultar_informe(video_id)
    intervalos = consultar_intervalos(video_id)
    duracion   = video["duracion_sec"]

    st.markdown(f"## Resultados — `{video['nombre']}`")
    st.caption(f"Duración: {fmt_seconds(duracion)}  ·  Analizado: {video['fecha_analisis'][:19]}")

    # ── Métricas superiores ───────────────────────────────────────────────────
    marcas_detectadas = [r for r in informe if r["tiempo_total_sec"] > 0]
    total_tiempo      = sum(r["tiempo_total_sec"] for r in marcas_detectadas)
    conf_media        = (
        sum(r["confianza_avg"] for r in marcas_detectadas) / len(marcas_detectadas)
        if marcas_detectadas else 0.0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Marcas detectadas",   len(marcas_detectadas))
    c2.metric("Tiempo total en pantalla", fmt_seconds(total_tiempo))
    c3.metric("Confianza media",     f"{conf_media * 100:.1f}%")
    c4.metric("Intervalos totales",  len(intervalos))

    st.markdown("## Distribución de tiempo")
    col_bar, col_donut = st.columns([3, 2])
    with col_bar:
        st.caption("Tiempo en pantalla por marca")
        chart_tiempo_marca(informe)
    with col_donut:
        st.caption("% del vídeo")
        chart_donut(informe)

    st.markdown("## Timeline de apariciones")
    chart_timeline(intervalos, duracion)

    st.markdown("## Detalle por marca")
    for row in sorted(informe, key=lambda r: r["tiempo_total_sec"], reverse=True):
        if row["tiempo_total_sec"] == 0:
            continue
        color = get_color(row["marca"])
        with st.expander(f"**{row['marca'].upper()}** — {fmt_seconds(row['tiempo_total_sec'])} ({row['porcentaje']:.1f}%)"):
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("Tiempo total",    fmt_seconds(row["tiempo_total_sec"]))
            cc2.metric("Apariciones",     row["num_intervalos"])
            cc3.metric("Confianza media", f"{row['confianza_avg'] * 100:.1f}%")

            ivs = [iv for iv in intervalos if iv["marca"] == row["marca"]]
            if ivs:
                df_ivs = pd.DataFrame(ivs)[["inicio_sec", "fin_sec", "duracion_sec", "confianza_avg"]]
                df_ivs.columns = ["Inicio (s)", "Fin (s)", "Duración (s)", "Confianza"]
                df_ivs["Confianza"] = df_ivs["Confianza"].apply(lambda x: f"{x*100:.1f}%")
                st.dataframe(df_ivs, hide_index=True, use_container_width=True)

    # ── Vídeo anotado ─────────────────────────────────────────────────────────
    annotated = OUTPUTS_DIR / f"{video['nombre']}_annotated.mp4"
    if annotated.exists():
        st.markdown("## Vídeo anotado")
        fixed = OUTPUTS_DIR / f"{video['nombre']}_annotated_h264.mp4"
        if not fixed.exists():
            ffmpeg_path = (
                shutil.which("ffmpeg") or
                r"C:\Users\bruno\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"
            )
            subprocess.run([
                ffmpeg_path,
                "-y", "-i", str(annotated),
                "-vcodec", "libx264", "-acodec", "aac",
                str(fixed)
            ], capture_output=True)

        if fixed.exists():
            st.markdown("""
            <style>
                video {
                    max-height: 400px;
                    border-radius: 10px;
                }
            </style>
            """, unsafe_allow_html=True)
            st.video(str(fixed))
        else:
            with open(annotated, "rb") as f:
                st.download_button(
                    label="Descargar vídeo anotado",
                    data=f,
                    file_name=annotated.name,
                    mime="video/mp4",
                )


# ── Sección de análisis nuevo ─────────────────────────────────────────────────
def render_upload() -> None:
    st.markdown("## Analizar nuevo vídeo")

    uploaded = st.file_uploader("Sube un vídeo .mp4", type=["mp4"])

    col_btn, col_opts = st.columns([2, 3])
    with col_opts:
        frame_skip = st.slider("Frame skip (velocidad vs precisión)", 1, 10, 3,
                               help="1 = analiza todos los frames (lento). 5 = más rápido, algo menos preciso.")
        save_video = st.checkbox("Guardar vídeo anotado", value=True)

    with col_btn:
        analizar = st.button("Analizar vídeo", type="primary", disabled=uploaded is None)

    if not analizar or uploaded is None:
        if uploaded is None:
            st.caption("Sube un vídeo para empezar.")
        return

    # Guardar temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(uploaded.read())
        tmp_path = Path(tmp.name)

    with st.spinner("Analizando vídeo... esto puede tardar unos minutos."):
        t0 = time.time()
        try:
            run_pipeline(
                video_path     = tmp_path,
                frame_skip     = frame_skip,
                save_video     = save_video,
            )
            elapsed = time.time() - t0
            st.success(f"Análisis completado en {elapsed:.1f}s. Selecciona el vídeo en el historial.")
            st.rerun()
        except Exception as e:
            st.error(f"Error durante el análisis: {e}")
        finally:
            tmp_path.unlink(missing_ok=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    init_db()

    st.markdown("# Brand Detection")
    st.caption("Sistema de detección de logos en vídeo — P11E4")
    st.divider()

    video_id = render_sidebar()

    tab_nuevo, tab_resultados = st.tabs(["Analizar vídeo", "Ver resultados"])

    with tab_nuevo:
        render_upload()

    with tab_resultados:
        if video_id is None:
            st.info("Analiza un vídeo primero o selecciona uno del historial.")
        else:
            render_resultados(video_id)


if __name__ == "__main__":
    main()