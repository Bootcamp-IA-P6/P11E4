"""
src/run.py
─────────────────────────────────────────────────────────────────────────────
Punto de entrada principal del sistema de detección de marcas.

Conecta: pipeline de vídeo → tracker → informe
Uso:
    uv run python src/run.py data/videos/mi_video.mp4
    uv run python src/run.py data/videos/mi_video.mp4 --skip 2 --no-video
"""

import argparse
import sys
import time
from pathlib import Path

import cv2

# ── Rutas del proyecto ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import MODEL_PATH, CONFIDENCE_THRESHOLD, FRAME_SKIP
from src.detection.video_pipeline import run_pipeline
from src.detection.tracker import build_intervals
from src.reporting.report import generate_report


def main(
    video_path: str | Path,
    model_path: str | Path = MODEL_PATH,
    conf_threshold: float = CONFIDENCE_THRESHOLD,
    frame_skip: int = FRAME_SKIP,
    save_video: bool = True,
) -> None:
    video_path = Path(video_path)

    # ── Duración del vídeo ────────────────────────────────────────────────────
    cap = cv2.VideoCapture(str(video_path))
    fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration_sec = total_frames / fps
    cap.release()

    print(f"\n{'='*50}")
    print(f"  P11E4 — Detección de marcas en vídeo")
    print(f"{'='*50}")
    print(f"  Vídeo     : {video_path.name}")
    print(f"  Duración  : {duration_sec:.1f}s  |  {fps:.0f} fps")
    print(f"  Modelo    : {model_path}")
    print(f"  Confianza : {conf_threshold:.0%}  |  Frame skip: {frame_skip}")
    print(f"{'='*50}\n")

    t_start = time.time()

    # ── 1. Pipeline de inferencia ─────────────────────────────────────────────
    print("[1/3] Ejecutando pipeline de inferencia...")
    detections = run_pipeline(
        video_path     = video_path,
        model_path     = model_path,
        conf_threshold = conf_threshold,
        frame_skip     = frame_skip,
        save_video     = save_video,
    )

    # ── 2. Tracker ────────────────────────────────────────────────────────────
    print("\n[2/3] Agrupando detecciones en intervalos...")
    intervals = build_intervals(detections)
    print(f"  {len(intervals)} intervalos de aparición encontrados")

    # ── 3. Informe ────────────────────────────────────────────────────────────
    print("\n[3/3] Generando informe...")
    report = generate_report(
        intervals          = intervals,
        video_duration_sec = duration_sec,
        video_name         = video_path.stem,
    )

    # ── Resumen final ─────────────────────────────────────────────────────────
    elapsed = time.time() - t_start
    print(f"\n{'='*50}")
    print(f"  Completado en {elapsed:.1f}s")
    print(f"{'='*50}")
    for brand in report.brands:
        bar = "█" * int(brand.percentage / 5)
        print(f"  {brand.brand:<8} {brand.total_seconds:>6.1f}s  "
              f"({brand.percentage:>5.1f}%)  {bar}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="P11E4 — Detecta marcas en vídeo y genera informe"
    )
    parser.add_argument(
        "video",
        help="Ruta al vídeo de entrada (ej: data/videos/test.mp4)"
    )
    parser.add_argument(
        "--model",
        default=str(MODEL_PATH),
        help=f"Ruta al modelo best.pt (default: {MODEL_PATH})"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=CONFIDENCE_THRESHOLD,
        help=f"Umbral de confianza (default: {CONFIDENCE_THRESHOLD})"
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=FRAME_SKIP,
        help=f"Procesar 1 de cada N frames (default: {FRAME_SKIP})"
    )
    parser.add_argument(
        "--no-video",
        action="store_true",
        help="No guardar vídeo anotado (más rápido)"
    )
    args = parser.parse_args()

    main(
        video_path     = args.video,
        model_path     = args.model,
        conf_threshold = args.conf,
        frame_skip     = args.skip,
        save_video     = not args.no_video,
    )