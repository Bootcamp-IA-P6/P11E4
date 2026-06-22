"""
Entrenamiento del modelo de detección de logos (Nike, Adidas, Puma)con YOLOv8 (Ultralytics) mediante transfer learning.


Este script reentrena un modelo YOLOv8 preentrenado sobre el dataset
propio de logos, aplicando aumento de datos, y valida el resultado.

Uso:
    python src/training/train.py

Requisitos:
    pip install ultralytics
    (o `uv add ultralytics` según el entorno del proyecto)


"""

from ultralytics import YOLO


def main():
    # ------------------------------------------------------------------
    # 1. Cargar el modelo base preentrenado (transfer learning)
    # ------------------------------------------------------------------
    # 'yolov8n.pt' = versión nano (la más ligera y rápida).
    # No se entrena desde cero: se parte de un modelo que ya sabe
    # reconocer formas y objetos genéricos, y se le enseña encima
    # a detectar nuestros 3 logos. Esto acelera el entrenamiento
    # y funciona bien con un dataset de tamaño moderado.
    model = YOLO("yolov8n.pt")

    # ------------------------------------------------------------------
    # 2. Entrenar con el dataset propio
    # ------------------------------------------------------------------
    results = model.train(
        # Ruta al data.yaml que define las clases y las particiones.
        # Ajustar según dónde esté el dataset al ejecutar.
        data="datasets/brands/data.yaml",

        # Número de pasadas completas por el dataset.
        epochs=50,

        # Tamaño al que se redimensionan las imágenes (preprocesado).
        imgsz=640,

        # Nº de imágenes procesadas a la vez (ajustar según la GPU).
        batch=16,

        # Para automáticamente si no mejora en 20 épocas seguidas
        # (early stopping: evita entrenar de más y malgastar tiempo).
        patience=20,

        # --------------------------------------------------------------
        # Aumento de datos (data augmentation) integrado de YOLOv8.
        # Crea variaciones de las imágenes en cada época para que el
        # modelo generalice mejor en lugar de memorizar.
        # --------------------------------------------------------------
        fliplr=0.5,     # volteo horizontal (50% de probabilidad)
        flipud=0.0,     # volteo vertical desactivado (los logos no van boca abajo)
        hsv_h=0.015,    # variación de tono (hue)
        hsv_s=0.7,      # variación de saturación
        hsv_v=0.4,      # variación de brillo (value)
        mosaic=1.0,     # combina 4 imágenes en una (aumenta variedad de contexto)
        degrees=15.0,   # rotación aleatoria de ±15 grados

        # Nombre de la carpeta donde se guardan los resultados.
        name="logos_yolov8n",
    )

    # ------------------------------------------------------------------
    # 3. Validar el modelo contra el set de validación
    # ------------------------------------------------------------------
    # Devuelve las métricas (mAP50, mAP50-95, precisión, recall),
    # tanto globales como por clase.
    metrics = model.val()
    print("Métricas de validación:")
    print(metrics)

    # Los pesos finales quedan en:
    #   runs/detect/logos_yolov8n/weights/best.pt   (mejor época)
    #   runs/detect/logos_yolov8n/weights/last.pt   (última época)
    # El entregable es 'best.pt'.


if __name__ == "__main__":
    main()