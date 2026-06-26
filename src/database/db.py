"""
src/database/db.py
Capa de acceso a la base de datos SQLite.
Todos los módulos usan estas funciones — nunca SQL suelto fuera de aquí.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import OUTPUTS_DIR

DB_PATH = OUTPUTS_DIR / "detecciones.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # devuelve filas como dict
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Crea las tablas si no existen. Llamar al arrancar la app."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text())
    print(f"[db] BD inicializada en {DB_PATH}")


def guardar_analisis(video_nombre: str, duracion_sec: float, intervalos, informe) -> int:
    """
    Guarda un análisis completo en la BD.
    Devuelve el video_id generado.

    Parámetros
    ----------
    video_nombre : nombre del archivo de vídeo
    duracion_sec : duración total del vídeo en segundos
    intervalos   : lista de AppearanceInterval (de tracker.py)
    informe      : objeto Report (de report.py)
    """
    with get_connection() as conn:
        # 1. Insertar vídeo
        cur = conn.execute(
            "INSERT INTO videos (nombre, duracion_sec, fecha_analisis) VALUES (?, ?, ?)",
            (video_nombre, duracion_sec, datetime.now().isoformat())
        )
        video_id = cur.lastrowid

        # 2. Insertar intervalos
        for iv in intervalos:
            conn.execute(
                """INSERT INTO intervalos
                   (video_id, marca, inicio_sec, fin_sec, duracion_sec,
                    num_frames, confianza_avg, ruta_recorte)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (video_id, iv.brand, iv.start, iv.end, iv.duration,
                 iv.detections, iv.avg_conf, None)
            )

        # 3. Insertar resumen por marca (del informe)
        for brand in informe.brands:
            conn.execute(
                """INSERT INTO informes
                   (video_id, marca, tiempo_total_sec, porcentaje,
                    num_intervalos, confianza_avg)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (video_id, brand.brand, brand.total_seconds, brand.percentage,
                 brand.num_intervals, brand.avg_confidence)
            )

    print(f"[db] Análisis guardado — video_id={video_id}")
    return video_id


def consultar_videos() -> list[dict]:
    """Devuelve todos los vídeos analizados."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM videos ORDER BY fecha_analisis DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def consultar_informe(video_id: int) -> list[dict]:
    """Devuelve el informe de un vídeo concreto."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM informes WHERE video_id = ? ORDER BY tiempo_total_sec DESC",
            (video_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def consultar_intervalos(video_id: int) -> list[dict]:
    """Devuelve todos los intervalos de aparición de un vídeo."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM intervalos WHERE video_id = ? ORDER BY inicio_sec",
            (video_id,)
        ).fetchall()
    return [dict(r) for r in rows]