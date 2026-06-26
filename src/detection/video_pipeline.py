"""
src/detection/video_pipeline.py
─────────────────────────────────────────────────────────────────────────────
Pipeline de inferencia sobre vídeo con YOLOv8.

Responsabilidades (Issue 1 — feat: pipeline de inferencia):
  · Carga el vídeo con OpenCV frame a frame
  · Aplica el modelo YOLOv8 a cada frame (con salto configurable)
  · Dibuja bounding box + nombre de clase + % de confianza
  · Guarda el vídeo anotado en outputs/
  · Devuelve lista de detecciones para reporting y BD

Uso rápido:
    from src.detection.video_pipeline import run_pipeline
    detections = run_pipeline("data/videos/mi_video.mp4")
"""

import cv2
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from ultralytics import YOLO

# Importa config desde la raíz del proyecto
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import (
    MODEL_PATH,
    OUTPUTS_DIR,
    CONFIDENCE_THRESHOLD,
    FRAME_SKIP,
    IOU_THRESHOLD,
)

# ── Colores por clase (BGR) ───────────────────────────────────────────────────
CLASS_COLORS = {
    "adidas": (0,   200,  50),    # verde
    "nike":   (0,   120, 255),    # naranja
    "puma":   (200,  40,  40),    # azul oscuro
}
DEFAULT_COLOR = (180, 180, 180)


# ── Estructura de datos de una detección ─────────────────────────────────────
@dataclass
class Detection:
    frame_num:  int
    timestamp:  float           # segundos desde el inicio del vídeo
    class_name: str
    confidence: float           # 0.0 – 1.0
    bbox:       tuple           # (x1, y1, x2, y2) en píxeles


# ── Funciones de dibujo ───────────────────────────────────────────────────────
def _draw_detection(frame, det: Detection) -> None:
    """Dibuja bbox + etiqueta con % confianza sobre el frame (in-place)."""
    x1, y1, x2, y2 = det.bbox
    color = CLASS_COLORS.get(det.class_name, DEFAULT_COLOR)
    label = f"{det.class_name}  {det.confidence * 100:.1f}%"

    # Bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=2)

    # Fondo del texto para legibilidad
    (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    top_left  = (x1, max(y1 - th - baseline - 4, 0))
    bot_right = (x1 + tw + 4, max(y1, th + baseline + 4))
    cv2.rectangle(frame, top_left, bot_right, color, thickness=-1)   # relleno

    # Texto blanco encima
    cv2.putText(
        frame, label,
        (x1 + 2, max(y1 - baseline - 2, th + 2)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
        (255, 255, 255), thickness=2, lineType=cv2.LINE_AA,
    )


# ── Pipeline principal ────────────────────────────────────────────────────────
def run_pipeline(
    video_path: str | Path,
    model_path: str | Path = MODEL_PATH,
    output_path: Optional[str | Path] = None,
    conf_threshold: float = CONFIDENCE_THRESHOLD,
    frame_skip: int = FRAME_SKIP,
    save_video: bool = True,
) -> list[Detection]:
    """
    Procesa un vídeo completo y devuelve todas las detecciones.

    Parámetros
    ----------
    video_path    : ruta al vídeo de entrada
    model_path    : ruta al archivo best.pt
    output_path   : ruta del vídeo anotado de salida (auto si None)
    conf_threshold: umbral mínimo de confianza para incluir detección
    frame_skip    : procesar 1 de cada `frame_skip` frames
    save_video    : si True genera el vídeo anotado en outputs/

    Retorna
    -------
    Lista de Detection con todas las detecciones del vídeo.
    """
    video_path = Path(video_path)
    model_path = Path(model_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Vídeo no encontrado: {video_path}")
    if not model_path.exists():
        raise FileNotFoundError(
            f"Modelo no encontrado: {model_path}\n"
            "Coloca best.pt en models/ (ver README — archivo en gitignore)."
        )

    # ── Cargar modelo ─────────────────────────────────────────────────────────
    print(f"[pipeline] Cargando modelo: {model_path}")
    model = YOLO(str(model_path))

    # ── Abrir vídeo ───────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV no pudo abrir el vídeo: {video_path}")

    fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(
        f"[pipeline] Vídeo: {video_path.name}  |  "
        f"{total_frames} frames  |  {fps:.1f} fps  |  {width}x{height}"
    )

    # ── Escritor de vídeo anotado ─────────────────────────────────────────────
    writer = None
    if save_video:
        if output_path is None:
            output_path = OUTPUTS_DIR / f"{video_path.stem}_annotated.mp4"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        print(f"[pipeline] Vídeo anotado → {output_path}")

    # ── Recorrer frames ───────────────────────────────────────────────────────
    detections: list[Detection] = []
    frame_num   = 0
    t_start     = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Saltar frames según FRAME_SKIP
        if frame_num % frame_skip != 0:
            if writer:
                writer.write(frame)     # escribe frame sin anotar igualmente
            frame_num += 1
            continue

        timestamp = frame_num / fps

        # ── Inferencia YOLOv8 ─────────────────────────────────────────────────
        results = model.predict(
            frame,
            conf=conf_threshold,
            iou=IOU_THRESHOLD,
            verbose=False,
        )

        # ── Extraer detecciones ───────────────────────────────────────────────
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id     = int(box.cls[0])
                class_name = model.names[cls_id]
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                det = Detection(
                    frame_num  = frame_num,
                    timestamp  = round(timestamp, 3),
                    class_name = class_name,
                    confidence = round(confidence, 4),
                    bbox       = (x1, y1, x2, y2),
                )
                detections.append(det)
                _draw_detection(frame, det)

        if writer:
            writer.write(frame)

        # Progreso en consola cada 100 frames procesados
        if frame_num % (frame_skip * 100) == 0:
            elapsed = time.time() - t_start
            pct     = (frame_num / total_frames * 100) if total_frames else 0
            print(f"  frame {frame_num:>6}/{total_frames}  ({pct:5.1f}%)  "
                  f"detecciones acumuladas: {len(detections)}  "
                  f"tiempo: {elapsed:.1f}s")

        frame_num += 1

    # ── Cierre ────────────────────────────────────────────────────────────────
    cap.release()
    if writer:
        writer.release()

    elapsed = time.time() - t_start
    print(
        f"[pipeline] Finalizado en {elapsed:.1f}s — "
        f"{len(detections)} detecciones en {frame_num} frames"
    )

    return detections


# ── Ejecución directa (test rápido) ──────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline de detección de marcas")
    parser.add_argument("video",  help="Ruta al vídeo de entrada")
    parser.add_argument("--model", default=str(MODEL_PATH), help="Ruta a best.pt")
    parser.add_argument("--conf",  type=float, default=CONFIDENCE_THRESHOLD)
    parser.add_argument("--skip",  type=int,   default=FRAME_SKIP)
    parser.add_argument("--no-save", action="store_true", help="No guardar vídeo anotado")
    args = parser.parse_args()

    dets = run_pipeline(
        video_path    = args.video,
        model_path    = args.model,
        conf_threshold= args.conf,
        frame_skip    = args.skip,
        save_video    = not args.no_save,
    )

    print(f"\nResumen: {len(dets)} detecciones totales")
    from collections import Counter
    for cls, count in Counter(d.class_name for d in dets).most_common():
        print(f"  {cls}: {count} frames")
