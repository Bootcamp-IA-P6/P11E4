# Briefing del proyecto — BrandVision

## Contexto

Una empresa de publicidad necesita evaluar la presencia de sus marcas en contenido audiovisual. El objetivo es construir un sistema que analice vídeos automáticamente, detecte los logos de las marcas representadas y genere un informe con el tiempo y porcentaje de aparición de cada una.

El procesado no necesita ser en tiempo real: el sistema analiza vídeos pregrabados y presenta los resultados en un informe.

## Marcas seleccionadas

Adidas, Nike y Puma — logos con suficiente representación visual y disponibilidad de imágenes para entrenar un modelo robusto.

## Niveles de entrega cubiertos

**Esencial** — modelo entrenado que detecta logos con bounding box visible, al menos una marca reconocida, repositorio Git organizado con documentación.

**Medio** — el modelo funciona sobre archivos de vídeo completos, mostrando el nombre de la clase detectada en cada bounding box.

**Avanzado** — porcentaje de confianza visible junto al nombre, detecciones guardadas en base de datos (video, marca, timestamp, confianza, imagen recortada del bbox), modelo multimarca capaz de reconocer las tres marcas simultáneamente.

**Experto** — frontend web en Streamlit para subir vídeos y visualizar resultados.

## Stack tecnológico

- Modelo: YOLOv8n (Ultralytics) — transfer learning sobre pesos preentrenados, 50 épocas, imagen 640px, batch 16, early stopping (patience 20)
- Etiquetado: Roboflow (formato YOLO, bounding boxes)
- Procesado de vídeo: OpenCV (frame a frame)
- Base de datos: SQLite
- Frontend: Streamlit
- Entorno: Python 3.11 + uv
- Despliegue: ngrok (demo pública temporal)

## División del equipo — Byte Lab

**Camila Arenas** — Dataset, etiquetado con Roboflow, entrenamiento YOLOv8, data augmentation (flip, crop, color jitter), entrega del modelo `best.pt`, presentación técnica.

**Iris Fernanda Amorim** — Pipeline de inferencia sobre vídeo (OpenCV + YOLOv8), visualización de bboxes y confianza, tracker de intervalos de aparición, generación de informes JSON y TXT, documentación (README y briefing).

**Raúl Machaca** — Esquema de base de datos SQLite, capa de acceso a datos, conexión con el pipeline, tests end-to-end, conversión de vídeo anotado con ffmpeg para reproducción en el navegador, integración backend-frontend & despliegue.

**Jose-Julio Ramírez y Sánchez-Escobar** — Setup inicial, repositorio GitHub, Frontend Streamlit, subida de vídeo, visualización de resultados, documentación.

## Resultado del entrenamiento

- Modelo YOLOv8n entrenado sobre 165 imágenes / 191 logos (3 clases) con data augmentation (volteo horizontal, rotación, variación HSV, mosaic).
- Validación sobre el set completo: mAP@50 0.91, precisión 0.86, recall 0.91.
- Por marca: Adidas 0.94, Puma 0.91, Nike 0.87. 
- Velocidad de inferencia de 2.1ms por imagen.
