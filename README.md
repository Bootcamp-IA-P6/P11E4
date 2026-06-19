# P11E4 — Detección de marcas en vídeo (Computer Vision)

Detección de logos de marcas en vídeo con YOLOv8: entrena un modelo, analiza
un vídeo, calcula tiempo y % de aparición de cada marca y guarda las
detecciones en una base de datos. Frontend en Streamlit.

## Estructura
- `src/training/`  — entrenamiento del modelo + data augmentation
- `src/detection/` — pipeline de vídeo (inferencia frame a frame)
- `src/reporting/` — cálculo de tiempos/% e informe
- `src/database/`  — esquema SQLite y acceso a datos
- `app/`           — frontend Streamlit
- `datasets/`      — dataset en formato YOLO (`data.yaml` versionado)

## Cómo empezar (uv, Python 3.11)
```bash
uv sync                                      # crea .venv e instala desde uv.lock
uv run streamlit run app/streamlit_app.py    # arranca el frontend
```

## Equipo
- Jose-Julio Ramírez y Sánchez-Escobar (@Jose-JulioRamirezySanchez-Escobar)
- Camila Arenas (@mcarenashd)
- Iris Fernanda Amorim (@IrisFernandaAmorim)
- Raúl Machaca (@RaulCtm)
