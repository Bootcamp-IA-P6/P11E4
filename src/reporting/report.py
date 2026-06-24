"""
src/reporting/report.py
─────────────────────────────────────────────────────────────────────────────
Genera el informe de aparición de marcas a partir de los intervalos del tracker.

Responsabilidades (Issue 2 — feat: cálculo de tiempo de aparición e informe):
  · Suma el tiempo total de aparición por marca
  · Calcula el % sobre la duración total del vídeo
  · Genera informe JSON  → outputs/<video>_report.json
  · Genera informe texto → outputs/<video>_report.txt

Uso:
    from src.reporting.report import generate_report
    report = generate_report(intervals, video_duration_sec, video_name="mi_video")
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.config import OUTPUTS_DIR, BRAND_CLASSES
from src.detection.tracker import AppearanceInterval


# ── Estructuras de datos del informe ─────────────────────────────────────────
@dataclass
class BrandStats:
    brand:             str
    total_seconds:     float       # tiempo total acumulado de aparición
    percentage:        float       # % sobre duración total del vídeo
    num_intervals:     int         # número de apariciones distintas
    avg_confidence:    float       # confianza media global de la marca
    intervals:         list[dict]  # detalles de cada intervalo


@dataclass
class VideoReport:
    video_name:        str
    video_duration_sec: float
    generated_at:      str         # ISO 8601
    brands:            list[BrandStats]
    total_detections:  int


# ── Función principal ─────────────────────────────────────────────────────────
def generate_report(
    intervals:          list[AppearanceInterval],
    video_duration_sec: float,
    video_name:         str = "video",
    output_dir:         Optional[Path] = None,
    save_json:          bool = True,
    save_txt:           bool = True,
) -> VideoReport:
    """
    Calcula estadísticas por marca y guarda los informes.

    Parámetros
    ----------
    intervals          : lista de AppearanceInterval del tracker
    video_duration_sec : duración total del vídeo en segundos
    video_name         : nombre base para los archivos de salida
    output_dir         : carpeta de salida (default: outputs/ de config)
    save_json          : guardar informe JSON
    save_txt           : guardar informe texto legible

    Retorna
    -------
    VideoReport con todas las estadísticas calculadas.
    """
    output_dir = Path(output_dir) if output_dir else OUTPUTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Agrupar intervalos por marca ──────────────────────────────────────────
    by_brand: dict[str, list[AppearanceInterval]] = {}
    for iv in intervals:
        by_brand.setdefault(iv.brand, []).append(iv)

    # ── Calcular estadísticas por marca ───────────────────────────────────────
    brand_stats: list[BrandStats] = []

    all_brands = set(BRAND_CLASSES) | set(by_brand.keys())   # incluye marcas sin detecciones
    for brand in sorted(all_brands):
        brand_intervals = by_brand.get(brand, [])

        total_sec = sum(iv.duration for iv in brand_intervals)
        percentage = (
            round((total_sec / video_duration_sec) * 100, 2)
            if video_duration_sec > 0
            else 0.0
        )

        # Confianza media ponderada por número de detecciones
        total_dets  = sum(iv.detections for iv in brand_intervals)
        avg_conf    = (
            sum(iv.avg_conf * iv.detections for iv in brand_intervals) / total_dets
            if total_dets > 0
            else 0.0
        )

        brand_stats.append(BrandStats(
            brand          = brand,
            total_seconds  = round(total_sec, 3),
            percentage     = percentage,
            num_intervals  = len(brand_intervals),
            avg_confidence = round(avg_conf, 4),
            intervals      = [
                {
                    "start":      iv.start,
                    "end":        iv.end,
                    "duration":   iv.duration,
                    "detections": iv.detections,
                    "avg_conf":   iv.avg_conf,
                }
                for iv in sorted(brand_intervals, key=lambda x: x.start)
            ],
        ))

    # Ordenar por tiempo total descendente
    brand_stats.sort(key=lambda s: s.total_seconds, reverse=True)

    report = VideoReport(
        video_name         = video_name,
        video_duration_sec = round(video_duration_sec, 3),
        generated_at       = datetime.utcnow().isoformat() + "Z",
        brands             = brand_stats,
        total_detections   = sum(s.num_intervals for s in brand_stats),
    )

    # ── Guardar JSON ──────────────────────────────────────────────────────────
    if save_json:
        json_path = output_dir / f"{video_name}_report.json"
        _save_json(report, json_path)
        print(f"[report] JSON guardado → {json_path}")

    # ── Guardar texto ─────────────────────────────────────────────────────────
    if save_txt:
        txt_path = output_dir / f"{video_name}_report.txt"
        _save_txt(report, txt_path)
        print(f"[report] TXT guardado  → {txt_path}")

    return report


# ── Serialización JSON ────────────────────────────────────────────────────────
def _save_json(report: VideoReport, path: Path) -> None:
    data = {
        "video_name":          report.video_name,
        "video_duration_sec":  report.video_duration_sec,
        "generated_at":        report.generated_at,
        "total_detections":    report.total_detections,
        "brands": [
            {
                "brand":          s.brand,
                "total_seconds":  s.total_seconds,
                "percentage":     s.percentage,
                "num_intervals":  s.num_intervals,
                "avg_confidence": s.avg_confidence,
                "intervals":      s.intervals,
            }
            for s in report.brands
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Informe texto legible ─────────────────────────────────────────────────────
def _save_txt(report: VideoReport, path: Path) -> None:
    lines = [
        "=" * 60,
        f"  INFORME DE DETECCIÓN DE MARCAS",
        "=" * 60,
        f"  Vídeo      : {report.video_name}",
        f"  Duración   : {_fmt_seconds(report.video_duration_sec)}",
        f"  Generado   : {report.generated_at}",
        "=" * 60,
        "",
    ]

    for stats in report.brands:
        bar = _progress_bar(stats.percentage)
        lines += [
            f"  {stats.brand.upper()}",
            f"    Tiempo total  : {_fmt_seconds(stats.total_seconds)}  ({stats.percentage:.1f}%)",
            f"    Apariciones   : {stats.num_intervals}",
            f"    Conf. media   : {stats.avg_confidence * 100:.1f}%",
            f"    {bar}",
            "",
        ]
        for i, iv in enumerate(stats.intervals, start=1):
            lines.append(
                f"    [{i}] {_fmt_seconds(iv['start'])} → {_fmt_seconds(iv['end'])}"
                f"  ({iv['duration']:.1f}s, conf {iv['avg_conf']*100:.1f}%)"
            )
        lines.append("")

    lines += ["=" * 60]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ── Helpers de formato ────────────────────────────────────────────────────────
def _fmt_seconds(sec: float) -> str:
    """Formatea segundos como mm:ss.d"""
    m, s = divmod(sec, 60)
    return f"{int(m):02d}:{s:04.1f}"


def _progress_bar(pct: float, width: int = 30) -> str:
    filled = int(pct / 100 * width)
    return f"[{'█' * filled}{'░' * (width - filled)}] {pct:.1f}%"


# ── Ejecución directa (test) ──────────────────────────────────────────────────
if __name__ == "__main__":
    """Test con datos ficticios para verificar el informe sin necesitar vídeo."""
    from src.detection.tracker import AppearanceInterval

    fake_intervals = [
        AppearanceInterval("nike",   start=1.0,  end=5.5,  detections=22, avg_conf=0.88),
        AppearanceInterval("adidas", start=8.0,  end=12.3, detections=17, avg_conf=0.82),
        AppearanceInterval("puma",   start=15.0, end=20.0, detections=25, avg_conf=0.91),
        AppearanceInterval("nike",   start=22.0, end=25.5, detections=14, avg_conf=0.85),
    ]

    report = generate_report(
        intervals          = fake_intervals,
        video_duration_sec = 30.0,
        video_name         = "test_dummy",
    )

    print("\n── Resumen ──")
    for s in report.brands:
        print(f"  {s.brand}: {s.total_seconds}s ({s.percentage}%)")
