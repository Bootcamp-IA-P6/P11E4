CREATE TABLE IF NOT EXISTS videos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    duracion_sec  REAL    NOT NULL,
    fecha_analisis TEXT   NOT NULL
);

CREATE TABLE IF NOT EXISTS intervalos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id      INTEGER NOT NULL REFERENCES videos(id),
    marca         TEXT    NOT NULL,
    inicio_sec    REAL    NOT NULL,
    fin_sec       REAL    NOT NULL,
    duracion_sec  REAL    NOT NULL,
    num_frames    INTEGER NOT NULL,
    confianza_avg REAL    NOT NULL,
    ruta_recorte  TEXT                  -- imagen recortada del bbox, puede ser NULL
);

CREATE TABLE IF NOT EXISTS informes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id        INTEGER NOT NULL REFERENCES videos(id),
    marca           TEXT    NOT NULL,
    tiempo_total_sec REAL   NOT NULL,
    porcentaje       REAL   NOT NULL,
    num_intervalos   INTEGER NOT NULL,
    confianza_avg    REAL   NOT NULL
);