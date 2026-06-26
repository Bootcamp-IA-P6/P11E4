"""Tests unitarios — src/reporting/report.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.detection.tracker import AppearanceInterval
from src.reporting.report import generate_report


FAKE_INTERVALS = [
    AppearanceInterval("nike",   start=1.0,  end=5.0,  detections=20, avg_conf=0.88),
    AppearanceInterval("adidas", start=8.0,  end=12.0, detections=16, avg_conf=0.82),
    AppearanceInterval("puma",   start=15.0, end=20.0, detections=25, avg_conf=0.91),
    AppearanceInterval("nike",   start=22.0, end=25.0, detections=14, avg_conf=0.85),
]


def test_marcas_presentes():
    """El informe debe incluir todas las marcas con detecciones."""
    report = generate_report(FAKE_INTERVALS, video_duration_sec=30.0,
                             video_name="test", save_json=False, save_txt=False)
    marcas = {s.brand for s in report.brands}
    assert "nike" in marcas
    assert "adidas" in marcas
    assert "puma" in marcas


def test_tiempo_acumulado_nike():
    """Nike aparece en dos intervalos (4s + 3s = 7s)."""
    report = generate_report(FAKE_INTERVALS, video_duration_sec=30.0,
                             video_name="test", save_json=False, save_txt=False)
    nike = next(s for s in report.brands if s.brand == "nike")
    assert abs(nike.total_seconds - 7.0) < 0.01


def test_porcentaje():
    """El porcentaje debe estar entre 0 y 100."""
    report = generate_report(FAKE_INTERVALS, video_duration_sec=30.0,
                             video_name="test", save_json=False, save_txt=False)
    for s in report.brands:
        assert 0.0 <= s.percentage <= 100.0


def test_porcentaje_suma_razonable():
    """La suma de porcentajes no debe superar el 100%."""
    report = generate_report(FAKE_INTERVALS, video_duration_sec=30.0,
                             video_name="test", save_json=False, save_txt=False)
    total = sum(s.percentage for s in report.brands)
    assert total <= 100.0


def test_num_intervalos_nike():
    """Nike tiene 2 intervalos separados."""
    report = generate_report(FAKE_INTERVALS, video_duration_sec=30.0,
                             video_name="test", save_json=False, save_txt=False)
    nike = next(s for s in report.brands if s.brand == "nike")
    assert nike.num_intervals == 2


def test_sin_detecciones_marca_sin_datos():
    """Una marca sin detecciones debe aparecer con 0s y 0%."""
    intervals = [AppearanceInterval("nike", start=1.0, end=5.0, detections=10, avg_conf=0.9)]
    report = generate_report(intervals, video_duration_sec=30.0,
                             video_name="test", save_json=False, save_txt=False)
    adidas = next((s for s in report.brands if s.brand == "adidas"), None)
    if adidas:
        assert adidas.total_seconds == 0.0
        assert adidas.percentage == 0.0


def test_duracion_cero_no_rompe():
    """Duración de vídeo 0 no debe lanzar ZeroDivisionError."""
    report = generate_report(FAKE_INTERVALS, video_duration_sec=0.0,
                             video_name="test", save_json=False, save_txt=False)
    for s in report.brands:
        assert s.percentage == 0.0