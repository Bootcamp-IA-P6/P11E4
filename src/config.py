"""
Rutas y constantes centralizadas del proyecto P11E4.
Todos los módulos importan desde aquí — nunca hardcodear rutas.
"""

from pathlib import Path

# ── Raíz del proyecto ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent   # P11E4/

# ── Modelo ───────────────────────────────────────────────────────────────────
MODELS_DIR = ROOT / "models"
MODEL_PATH  = MODELS_DIR / "best.pt"            # YOLOv8s entrenado por Persona 1

# ── Datos ────────────────────────────────────────────────────────────────────
DATA_DIR    = ROOT / "data"
VIDEOS_DIR  = DATA_DIR / "videos"

# ── Salidas ──────────────────────────────────────────────────────────────────
OUTPUTS_DIR = ROOT / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Inferencia ───────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.40     # detecciones por debajo se descartan
FRAME_SKIP           = 3        # procesar 1 de cada N frames (1 = todos)
IOU_THRESHOLD        = 0.45     # NMS IoU

# ── Tracker ──────────────────────────────────────────────────────────────────
# Segundos de silencio antes de cerrar un intervalo de aparición
TRACKER_GAP_TOLERANCE_SEC = 1.0

# ── Clases del modelo (deben coincidir con data.yaml) ────────────────────────
BRAND_CLASSES = ["adidas", "nike", "puma"]
