# Cutting Object Detector

Projeto de detecção de objetos cortantes em vídeos usando YOLOv8 com treinamento personalizado e API REST para envio de vídeos e alertas.

---

## 🧠 Funcionalidades

- Treinamento de modelo YOLO com dataset customizado
- Upload de vídeos para análise via API
- Geração de vídeo com detecção de objetos
- Envio de alerta por e-mail ao detectar objeto cortante
- Interface de API interativa via Swagger (FastAPI)

---

## 📦 Estrutura do Projeto

```
Sharp_objects_detection/
├── app/                  # Lógica do modelo e serviços
│   ├── detector.py
│   ├── trainer.py
│   └── email_alert.py
├── api/                  # Endpoints da API
│   └── main.py
├── models/               # Modelos treinados (best.pt)
│   └── objeto_cortante.pt
├── videos/
│   ├── input/            # Vídeos enviados para análise
│   └── output/           # Vídeos processados com detecção
├── config/               # Arquivo YAML do dataset
│   └── data.yaml
├── requirements.txt      # Dependências do projeto
└── README.md             # Este arquivo
```

---

## ▶️ Como Rodar Localmente

### 1. Clone o projeto
```bash
git clone https://github.com/seuusuario/cutting_object_detector.git
cd cutting_object_detector
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Inicie o servidor
```bash
uvicorn api.main:app --reload
```

### 4. Acesse a interface de testes
```
http://127.0.0.1:8000/docs
```

---

## 📤 Treinamento do Modelo

### Endpoint: `POST /treinar-modelo`

**Campos:**
- `dataset_path`: Caminho da pasta do dataset (ex: `Cortantes.v1i.yolov12`)
- `epochs` (opcional): Número de épocas de treinamento

```json
{
  "dataset_path": "Cortantes.v1i.yolov12",
  "epochs": 100
}
```

O modelo treinado será salvo automaticamente em `models/objeto_cortante.pt`

---

## 📼 Análise de Vídeo

### Endpoint: `POST /analisar-video`

**Form-Data:**
- `video`: arquivo de vídeo
- `alertar_email`: true/false
- `gerar_video`: true/false
- `destinatario`: e-mail de destino (caso envie alertas)
- `remetente`: e-mail remetente (Gmail)
- `senha`: senha do remetente (ou App Password do Gmail)

**Resposta:**
```json
{
  "objeto_detectado": true,
  "video_processado": "videos/output/processado_video.mp4"
}
```

---

## 📧 Envio de E-mails
Utiliza SMTP Gmail para envio de alertas.
- Recomendado usar senha de aplicativo (App Password) para segurança.

---

## 🔧 Requisitos
- Python 3.8+
- `yolov8n.pt` (modelo base da ultralytics)
- Dataset estruturado com `train/images`, `train/labels`, `valid/images`, `valid/labels`

---

## 📌 Observações
- Toda detecção e treinamento roda localmente (sem Google Drive)
- Caso queira rodar em produção, considere usar Docker + Nginx + HTTPS

---

Feito com 💡 para o FIAP Tech Challenge

