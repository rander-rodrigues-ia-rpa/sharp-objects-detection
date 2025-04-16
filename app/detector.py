import cv2
import os
from ultralytics import YOLO

def processar_video(modelo_path, video_path, output_path='videos/output/video_processado.mp4'):
    modelo = YOLO(modelo_path)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError("Erro ao abrir o vídeo.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    objeto_detectado = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        resultados = modelo(frame, conf=0.25)
        if len(resultados[0].boxes) > 0:
            objeto_detectado = True

        frame_anotado = resultados[0].plot()
        out.write(frame_anotado)

    cap.release()
    out.release()

    return output_path, objeto_detectado
