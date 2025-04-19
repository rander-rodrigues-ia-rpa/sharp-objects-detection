import cv2
import os
from ultralytics import YOLO
import numpy as np
from datetime import datetime

def processar_video(modelo_path, input_path, output_path=None, limiar_confianca=0.25, salvar_frames=False, frames_dir=None):
    """
    Processa um vídeo para detectar objetos cortantes usando YOLO.
    
    Args:
        modelo_path: Caminho para o modelo treinado
        input_path: Caminho para o vídeo de entrada
        output_path: Caminho para salvar o vídeo processado (opcional)
        limiar_confianca: Limiar de confiança para considerar uma detecção
        salvar_frames: Se deve salvar os frames onde foram detectados objetos
        frames_dir: Diretório para salvar os frames com detecções
    
    Returns:
        tuple: (caminho do vídeo processado, lista de detecções)
    """
    # Carregar modelo YOLO
    modelo = YOLO(modelo_path)
    
    # Abrir o vídeo
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Não foi possível abrir o vídeo: {input_path}")
    
    # Obter propriedades do vídeo
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Configurar o writer do vídeo se output_path for fornecido
    out = None
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Lista para armazenar informações sobre cada detecção
    deteccoes = []
    
    # Processar cada frame
    frame_num = 0
    already_detected_frames = set()  # Para evitar detecções duplicadas no mesmo frame
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Executar a detecção no frame atual
        resultados = modelo(frame, conf=limiar_confianca)
        
        # Verificar se algum objeto foi detectado neste frame
        if len(resultados[0].boxes) > 0:
            # Frame contém detecções
            frame_anotado = resultados[0].plot()
            
            # Salvar o frame com detecções, se solicitado
            frame_path = None
            if salvar_frames and frames_dir and frame_num not in already_detected_frames:
                os.makedirs(frames_dir, exist_ok=True)
                frame_path = os.path.join(frames_dir, f"frame_{frame_num:06d}.jpg")
                cv2.imwrite(frame_path, frame_anotado)
                already_detected_frames.add(frame_num)
                
            # Obter informações detalhadas sobre cada detecção neste frame
            for box in resultados[0].boxes:
                # Extrair coordenadas da caixa
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                
                # Extrair confiança
                confianca = float(box.conf[0].cpu().numpy())
                
                # Extrair classe (se aplicável)
                if hasattr(box, 'cls'):
                    classe_id = int(box.cls[0].cpu().numpy())
                    classe_nome = resultados[0].names[classe_id]
                else:
                    classe_nome = "objeto_cortante"
                
                # Adicionar esta detecção à lista
                deteccoes.append({
                    'frame_num': frame_num,
                    'tempo': frame_num / fps if fps > 0 else 0,
                    'classe': classe_nome,
                    'confianca': confianca,
                    'coordenadas': [int(x1), int(y1), int(x2), int(y2)],
                    'frame_path': frame_path
                })
        else:
            # Sem detecções, usar o frame original
            frame_anotado = frame
        
        # Escrever o frame processado no vídeo de saída, se solicitado
        if out:
            out.write(frame_anotado)
        
        frame_num += 1
        
        # Feedback de progresso a cada 100 frames
        if frame_num % 100 == 0:
            print(f"Processando frame {frame_num}/{total_frames} ({frame_num/total_frames*100:.1f}%)")
    
    # Liberar recursos
    cap.release()
    if out:
        out.release()
    
    return output_path, deteccoes