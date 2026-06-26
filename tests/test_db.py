"""Tests unitarios — src/database/db.py"""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.database.db as db_module
from src.detection.tracker import AppearanceInterval
from src.reporting.report import generate_report


def _setup_tmp_db(tmp_path):
    """Redirige la BD a un directorio temporal para no contaminar outputs/."""
    db_module.DB_PATH = tmp_path / "test.db"


FAKE_INTERVALS = [
    AppearanceInterval("nike",   start=1.0, end=5.0, detections=20, avg_conf=0.88),
    AppearanceInterval("adidas", start=8.0, end=12.0, detections=16, avg_conf=0.82),
]


def test_init_db(tmp_path):
    _setup_tmp_db(tmp_path)
    db_module.init_db()
    assert db_module.DB_PATH.exists()


def test_guardar_y_consultar_video(tmp_path):
    _setup_tmp_db(tmp_path)
    db_module.init_db()

    report = generate_report(FAKE_INTERVALS, video_duration_sec=30.0,
                             video_name="test_video", save_json=False, save_txt=False)
    video_id = db_module.guardar_analisis("test_video", 30.0, FAKE_INTERVALS, report)

    videos = db_module.consultar_videos()
    assert len(videos) == 1
    assert videos[0]["nombre"] == "test_video"
    assert videos[0]["id"] == video_id


def test_consultar_informe(tmp_path):
    _setup_tmp_db(tmp_path)
    db_module.init_db()

    report = generate_report(FAKE_INTERVALS, video_duration_sec=30.0,
                             video_name="test_video", save_json=False, save_txt=False)
    video_id = db_module.guardar_analisis("test_video", 30.0, FAKE_INTERVALS, report)

    informe = db_module.consultar_informe(video_id)
    marcas = {row["marca"] for row in informe}
    assert "nike" in marcas
    assert "adidas" in marcas


def test_consultar_intervalos(tmp_path):
    _setup_tmp_db(tmp_path)
    db_module.init_db()

    report = generate_report(FAKE_INTERVALS, video_duration_sec=30.0,
                             video_name="test_video", save_json=False, save_txt=False)
    video_id = db_module.guardar_analisis("test_video", 30.0, FAKE_INTERVALS, report)

    intervalos = db_module.consultar_intervalos(video_id)
    assert len(intervalos) == 2


def test_multiples_videos(tmp_path):
    _setup_tmp_db(tmp_path)
    db_module.init_db()

    report = generate_report(FAKE_INTERVALS, video_duration_sec=30.0,
                             video_name="v", save_json=False, save_txt=False)
    db_module.guardar_analisis("video1", 30.0, FAKE_INTERVALS, report)
    db_module.guardar_analisis("video2", 45.0, FAKE_INTERVALS, report)

    videos = db_module.consultar_videos()
    assert len(videos) == 2


def test_bd_vacia_devuelve_lista_vacia(tmp_path):
    _setup_tmp_db(tmp_path)
    db_module.init_db()
    assert db_module.consultar_videos() == []
    assert db_module.consultar_informe(999) == []