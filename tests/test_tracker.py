"""Tests unitarios — src/detection/tracker.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.detection.tracker import BrandTracker, build_intervals, AppearanceInterval
from src.detection.video_pipeline import Detection


def _make_det(brand, timestamp, conf=0.9):
    return Detection(
        frame_num=int(timestamp * 30),
        timestamp=timestamp,
        class_name=brand,
        confidence=conf,
        bbox=(0, 0, 100, 100)
    )


def test_intervalo_simple():
    """Detecciones consecutivas deben agruparse en un solo intervalo."""
    dets = [_make_det("nike", t) for t in [1.0, 1.1, 1.2, 1.3]]
    intervals = build_intervals(dets, gap_tolerance_sec=1.0)
    assert len(intervals) == 1
    assert intervals[0].brand == "nike"
    assert intervals[0].start == 1.0
    assert intervals[0].end == 1.3


def test_intervalo_con_gap_tolerable():
    """Un hueco pequeño (dentro de la tolerancia) no debe cerrar el intervalo."""
    dets = [_make_det("nike", 1.0), _make_det("nike", 1.5), _make_det("nike", 2.0)]
    intervals = build_intervals(dets, gap_tolerance_sec=1.0)
    assert len(intervals) == 1


def test_intervalo_con_gap_grande():
    """Un hueco mayor que la tolerancia debe generar dos intervalos distintos."""
    dets = [_make_det("nike", 1.0), _make_det("nike", 5.0)]
    intervals = build_intervals(dets, gap_tolerance_sec=1.0)
    assert len(intervals) == 2


def test_multimarca():
    """Marcas distintas deben generar intervalos independientes."""
    dets = [
        _make_det("nike",   1.0),
        _make_det("adidas", 1.1),
        _make_det("puma",   1.2),
    ]
    intervals = build_intervals(dets, gap_tolerance_sec=1.0)
    marcas = {iv.brand for iv in intervals}
    assert marcas == {"nike", "adidas", "puma"}


def test_duracion_correcta():
    """La duración del intervalo debe ser end - start."""
    dets = [_make_det("puma", 2.0), _make_det("puma", 5.0)]
    intervals = build_intervals(dets, gap_tolerance_sec=10.0)
    assert intervals[0].duration == 3.0


def test_sin_detecciones():
    """Sin detecciones debe devolver lista vacía."""
    intervals = build_intervals([])
    assert intervals == []


def test_confianza_media():
    """La confianza media debe calcularse correctamente."""
    dets = [_make_det("nike", 1.0, conf=0.8), _make_det("nike", 1.1, conf=0.6)]
    intervals = build_intervals(dets, gap_tolerance_sec=1.0)
    assert abs(intervals[0].avg_conf - 0.7) < 0.01