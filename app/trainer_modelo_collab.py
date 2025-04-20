# Instalação das dependências necessárias
!pip install -q ultralytics
!pip install -q roboflow

# Import de bibliotecas
import os
import cv2
import numpy as np
from ultralytics import YOLO
from google.colab import drive
import matplotlib.pyplot as plt
from IPython.display import clear_output, display

# Montar o Google Drive (para salvar modelos)
drive.mount('/content/drive')

# Download do dataset manualmente
caminho_dataset = "/content/drive/MyDrive/FIAP_TECH_CHALLENGE_V/Cortantes.v1i.yolov12"  # Ajuste para o caminho onde você fez upload dos arquivos

# Verifica estrutura do dataset
!ls -la {caminho_dataset}
print("Verificando pastas train e valid:")
!ls -la {caminho_dataset}/train
!ls -la {caminho_dataset}/valid

# ==============================
# Treinamento do modelo
# ==============================

# Configuração para o treinamento
def criar_arquivo_config(nome_arquivo="data.yaml"):
    # Verifica se o arquivo já existe
    if not os.path.exists(f"{caminho_dataset}/{nome_arquivo}"):
        print(f"Arquivo {nome_arquivo} não encontrado. Criando arquivo de configuração...")
        # Obter o número de classes contando os arquivos na pasta train/labels
        arquivos_labels = os.listdir(f"{caminho_dataset}/train/labels")
        
        # Lê um dos arquivos para determinar as classes
        classes = set()
        for arquivo in arquivos_labels[:10]:  # Verificar os 10 primeiros arquivos
            if arquivo.endswith('.txt'):
                with open(f"{caminho_dataset}/train/labels/{arquivo}", 'r') as f:
                    for linha in f:
                        if linha.strip():
                            classe = int(linha.strip().split()[0])
                            classes.add(classe)
        
        num_classes = len(classes)
        print(f"Número de classes detectadas: {num_classes}")
        
        # Cria o arquivo de configuração
        with open(f"{caminho_dataset}/{nome_arquivo}", 'w') as f:
            f.write(f"train: {caminho_dataset}/train/images\n")
            f.write(f"val: {caminho_dataset}/valid/images\n")
            f.write(f"nc: {num_classes}\n")
            f.write("names: ['objeto_cortante']\n")
    else:
        print(f"Arquivo {nome_arquivo} encontrado. Usando configuração existente.")
    
    return f"{caminho_dataset}/{nome_arquivo}"

# Criar ou verificar arquivo de configuração
config_path = criar_arquivo_config()

# Função para treinar o modelo
def treinar_modelo(config_path, epochs=100, imgsz=640, batch=16):
    # Inicializa o modelo YOLOv8
    modelo = YOLO('yolov8n.pt')
    
    # Treina o modelo
    print("Iniciando treinamento...")
    resultados = modelo.train(
        data=config_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name='objeto_cortante_detector',
        augment=True  # Ativa augmentation
    )
    
    # Salva o modelo no Google Drive
    modelo_path = f'/content/runs/detect/objeto_cortante_detector/weights/best.pt'
    drive_path = '/content/drive/MyDrive/FIAP_TECH_CHALLENGE_V/objeto_cortante_detector_best.pt'
    !cp {modelo_path} {drive_path}
    print(f"Modelo salvo em: {drive_path}")
    
    return modelo_path

#Função para continuar o treinamento de onde parou
def continuar_treinamento(modelo_path, config_path, epochs=50, imgsz=640, batch=16):
    # Carrega o modelo existente
    modelo = YOLO(modelo_path)  # Carrega objeto_cortante.pt
    
    # Continua o treinamento
    print("Continuando treinamento do modelo...")
    resultados = modelo.train(
        data=config_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name='objeto_cortante_detector_continuado',  # Nome diferente para não sobrescrever
        exist_ok=True  # Permite continuar em uma pasta existente
    )
    
    # Salva o modelo no Google Drive
    modelo_path_novo = f'/content/runs/detect/objeto_cortante_detector_continuado/weights/best.pt'
    drive_path = '/content/drive/MyDrive/FIAP_TECH_CHALLENGE_V/objeto_cortante_detector_melhorado.pt'
    !cp {modelo_path_novo} {drive_path}
    print(f"Modelo atualizado salvo em: {drive_path}")
    
    return modelo_path_novo

# Função para mostrar algumas métricas e resultados do treinamento
def mostrar_resultados_treinamento():
    # Mostrar as métricas de treinamento (se disponíveis)
    for img_path in ['results.png', 'confusion_matrix.png', 'val_batch0_pred.jpg']:
        img_full_path = f'/content/runs/detect/objeto_cortante_detector/{img_path}'
        if os.path.exists(img_full_path):
            img = cv2.imread(img_full_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            plt.figure(figsize=(12, 8))
            plt.imshow(img)
            plt.title(img_path)
            plt.axis('off')
            plt.show()

# ==============================
# Detecção em vídeo
# ==============================

def processar_video(modelo_path, video_path, output_path='video_processado_3.mp4'):
    # Carrega o modelo treinado
    modelo = YOLO(modelo_path)
    
    # Abre o vídeo
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Erro ao abrir o vídeo")
        return
    
    # Obtém propriedades do vídeo
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Configura o gravador de vídeo
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Processa cada frame
    frame_count = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print("Processando vídeo...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Realiza a detecção
        resultados = modelo(frame, conf=0.15)  # Limiar de confiança de 25%
        
        # Desenha as caixas delimitadoras
        quadro_anotado = resultados[0].plot()
        
        # Escreve o frame no vídeo de saída
        out.write(quadro_anotado)
        
        # Exibe progresso
        frame_count += 1
        if frame_count % 10 == 0:
            print(f"Progresso: {frame_count}/{total_frames} frames ({frame_count/total_frames*100:.1f}%)")
    
    # Libera recursos
    cap.release()
    out.release()
    
    print(f"Vídeo processado salvo em: {output_path}")
    # Copia para o Google Drive
    drive_video_path = f'/content/drive/MyDrive/FIAP_TECH_CHALLENGE_V/{os.path.basename(output_path)}'
    !cp {output_path} {drive_video_path}
    print(f"Vídeo copiado para: {drive_video_path}")
    
    return output_path

# ==============================
# Função principal - Executa o fluxo completo
# ==============================

def executar_fluxo_completo(video_path, epochs=50, modelo_existente=None):
    """
    Executa o fluxo completo: treinamento do modelo e processamento do vídeo
    
    Args:
        video_path (str): Caminho para o vídeo que será analisado
        epochs (int): Número de épocas para o treinamento
        modelo_existente (str, optional): Caminho para um modelo existente para continuar o treinamento
    """
    print("=== Iniciando fluxo de trabalho para detecção de objetos cortantes ===")
    
    # 1. Cria/verifica arquivo de configuração
    config_path = criar_arquivo_config()
    print(f"Arquivo de configuração: {config_path}")
    
    # 2. Treina o modelo ou continua treinamento
    if modelo_existente:
        modelo_path = continuar_treinamento(modelo_existente, config_path, epochs=epochs)
        print("Treinamento continuado concluído!")
        print(f"Cópia do modelo no Drive: /content/drive/MyDrive/FIAP_TECH_CHALLENGE_V/objeto_cortante_detector_melhorado.pt")
    else:
        modelo_path = treinar_modelo(config_path, epochs=epochs)
        print("Treinamento do zero concluído!")
        print(f"Cópia do modelo no Drive: /content/drive/MyDrive/FIAP_TECH_CHALLENGE_V/objeto_cortante_detector_best.pt")
    
    # 3. Mostra resultados do treinamento
    mostrar_resultados_treinamento()
    
    # 4. Processa o vídeo
    video_processado = processar_video(modelo_path, video_path)
    
    print("=== Fluxo de trabalho concluído com sucesso! ===")
    print(f"Modelo salvo em: {modelo_path}")
    print(f"Vídeo processado: {video_processado}")
    print(f"Cópia do vídeo no Drive: /content/drive/MyDrive/FIAP_TECH_CHALLENGE_V/{os.path.basename(video_processado)}")


# Execução do processamento:
executar_fluxo_completo('/content/drive/MyDrive/FIAP_TECH_CHALLENGE_V/video.mp4', epochs=50, modelo_existente='/content/drive/MyDrive/FIAP_TECH_CHALLENGE_V/objeto_cortante_detector_best.pt')