import os
from ultralytics import YOLO

def criar_config_yaml(caminho_dataset, nome_arquivo="data.yaml"):
    config_path = os.path.join(caminho_dataset, nome_arquivo)
    if not os.path.exists(config_path):
        classes = set()
        labels_path = os.path.join(caminho_dataset, 'train', 'labels')
        for arquivo in os.listdir(labels_path):
            if arquivo.endswith('.txt'):
                with open(os.path.join(labels_path, arquivo), 'r') as f:
                    for linha in f:
                        if linha.strip():
                            classe = int(linha.strip().split()[0])
                            classes.add(classe)

        with open(config_path, 'w') as f:
            f.write(f"train: {os.path.join(caminho_dataset, 'train', 'images')}\n")
            f.write(f"val: {os.path.join(caminho_dataset, 'valid', 'images')}\n")
            f.write(f"nc: {len(classes)}\n")
            f.write("names: ['objeto_cortante']\n")

    return config_path

def treinar_modelo(config_path, modelo_pre_treinado='yolov8n.pt', epochs=80, imgsz=640, batch=16):
    modelo = YOLO(modelo_pre_treinado)
    resultados = modelo.train(
        data=config_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name='objeto_cortante_detector',
        augment=True
    )
    return resultados

def continuar_treinamento(modelo_path, config_path, epochs=80, imgsz=640, batch=16):
    modelo = YOLO(modelo_path)
    resultados = modelo.train(
        data=config_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name='objeto_cortante_detector_continuado',
        exist_ok=True
    )
    return resultados
