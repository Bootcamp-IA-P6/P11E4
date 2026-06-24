"""
src/detection/tracker.py
─────────────────────────────────────────────────────────────────────────────
Agrupa detecciones frame a frame en intervalos de aparición continua.

Sin este módulo calcularíamos el tiempo sumando frames individuales, lo que
sobreestimaría si hay huecos pequeños (p.ej. la marca queda oculta 1 segundo).
El tracker tolera silencios cortos (GAP_TOLERANCE) antes de cerrar un intervalo.

Ejemplo de salida:
    [
      AppearanceInterval(brand="nike",   start=2.1,  end=8.4,  detections=62),
      AppearanceInterval(brand="adidas", start=10.0, end=15.7, detections=45),
      ...
    ]
"""

from dataclasses import dataclass, field
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import TRACKER_GAP_TOLERANCE_SEC
from src.detection.video_pipeline import Detection


# ── Intervalo de aparición continua ──────────────────────────────────────────
@dataclass
class AppearanceInterval:
    brand:       str
    start:       float          # timestamp inicio (segundos)
    end:         float          # timestamp fin (segundos)
    detections:  int = 0        # nº de frames con detección en el intervalo
    avg_conf:    float = 0.0    # confianza media en el intervalo

    @property
    def duration(self) -> float:
        """Duración real del intervalo en segundos."""
        return round(self.end - self.start, 3)


# ── Estado interno del tracker por marca ─────────────────────────────────────
@dataclass
class _BrandState:
    current_interval: Optional[AppearanceInterval] = None
    conf_sum:         float = 0.0
    det_count:        int   = 0


# ── Tracker principal ─────────────────────────────────────────────────────────
class BrandTracker:
    """
    Recibe una lista de Detection (ordenada por timestamp) y produce
    una lista de AppearanceInterval agrupando apariciones continuas.

    Parámetros
    ----------
    gap_tolerance_sec : tiempo máximo de ausencia antes de cerrar un intervalo.
                        Valor por defecto desde config.py.
    """

    def __init__(self, gap_tolerance_sec: float = TRACKER_GAP_TOLERANCE_SEC):
        self.gap_tolerance = gap_tolerance_sec
        self._states: dict[str, _BrandState] = {}
        self._closed: list[AppearanceInterval] = []

    # ── API pública ───────────────────────────────────────────────────────────

    def process(self, detections: list[Detection]) -> list[AppearanceInterval]:
        """
        Procesa todas las detecciones y devuelve los intervalos de aparición.
        Las detecciones deben estar ordenadas por timestamp (lo estarán si
        vienen de run_pipeline, que las genera en orden de frame).
        """
        # Ordenar por seguridad
        sorted_dets = sorted(detections, key=lambda d: d.timestamp)

        for det in sorted_dets:
            self._update(det)

        # Cerrar intervalos abiertos al final del vídeo
        self._flush_all()

        return self._closed

    # ── Lógica interna ────────────────────────────────────────────────────────

    def _update(self, det: Detection) -> None:
        brand = det.class_name
        if brand not in self._states:
            self._states[brand] = _BrandState()
        state = self._states[brand]

        if state.current_interval is None:
            # Primera detección de esta marca → abrir nuevo intervalo
            state.current_interval = AppearanceInterval(
                brand=brand, start=det.timestamp, end=det.timestamp
            )
            state.conf_sum   = det.confidence
            state.det_count  = 1
        else:
            gap = det.timestamp - state.current_interval.end
            if gap <= self.gap_tolerance:
                # Dentro de la tolerancia → extender intervalo actual
                state.current_interval.end = det.timestamp
                state.conf_sum  += det.confidence
                state.det_count += 1
            else:
                # Brecha demasiado grande → cerrar el actual y abrir uno nuevo
                self._close_interval(brand, state)
                state.current_interval = AppearanceInterval(
                    brand=brand, start=det.timestamp, end=det.timestamp
                )
                state.conf_sum  = det.confidence
                state.det_count = 1

    def _close_interval(self, brand: str, state: _BrandState) -> None:
        if state.current_interval is None:
            return
        interval             = state.current_interval
        interval.detections  = state.det_count
        interval.avg_conf    = round(
            state.conf_sum / state.det_count if state.det_count else 0.0, 4
        )
        self._closed.append(interval)
        state.current_interval = None
        state.conf_sum         = 0.0
        state.det_count        = 0

    def _flush_all(self) -> None:
        """Cierra todos los intervalos aún abiertos (fin de vídeo)."""
        for brand, state in self._states.items():
            if state.current_interval is not None:
                self._close_interval(brand, state)


# ── Función de conveniencia ───────────────────────────────────────────────────
def build_intervals(
    detections: list[Detection],
    gap_tolerance_sec: float = TRACKER_GAP_TOLERANCE_SEC,
) -> list[AppearanceInterval]:
    """Atajo para usar el tracker sin instanciar la clase directamente."""
    tracker = BrandTracker(gap_tolerance_sec=gap_tolerance_sec)
    return tracker.process(detections)
