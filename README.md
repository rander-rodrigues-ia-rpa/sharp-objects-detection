# Sharp Objects Detection

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
├── api/                  # Endpoints da API
│   └── frontend.py
|   |__ main.py
├── app/                  # Lógica do modelo e serviços
|   |__ alertatelegram.py
│   ├── detector.py
│   ├── trainer.py
│   └── email_alert.py
|   |__ trainer.py
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

## 🛠️ Como Iniciar o Projeto Localmente

### 1. Baixando o Projeto
Para começar, clone o repositório do projeto no seu ambiente local usando o Git:
```bash
git clone https://github.com/rander-rodrigues-ia-rpa/sharp-objects-detection.git
```

### 2. Configurando o Ambiente Local
## 2.1 Criar o Ambiente Virtual
Primeiro, crie um ambiente virtual para isolar as dependências do projeto.
```bash
python -m venv environment
```

## 2.2 Ativar o Ambiente Virtual
Ative o ambiente virtual com o seguinte comando:
Windows:
```bash
.\environment\Scripts\Activate
```

Linux/macOS:
```bash
source environment/bin/activate
```

## 2.3 Instalar as Dependências
Instale todas as dependências necessárias para o projeto:
```bash
pip install -r requirements.txt
```

### 3. Rodando a API Backend (FastAPI)
A API foi construída usando FastAPI. Para rodá-la, siga os seguintes passos:

## 3.1 Entrar na pasta do projeto
Se você ainda não estiver na pasta principal do projeto, entre nela:
```bash
cd SHARP-OBJECTS-DETECTION
```

## 3.2 Iniciar o Backend
Inicie o servidor backend com o seguinte comando:
```bash
uvicorn api.main:app --reload
```
O servidor backend estará disponível em http://127.0.0.1:8000.

### 4. Rodando o Frontend (Streamlit)
Agora, vamos rodar o frontend com Streamlit:

## 4.1 Entrar na Pasta api
Se você não está na pasta api, vá até ela:
```bash
cd api
```
## 4.2 Iniciar o Frontend
Agora, execute o Streamlit para rodar o frontend da aplicação:
```bash
streamlit run frontend.py
```
O frontend será acessado em http://127.0.0.1:8501.

⚠️ Observações Importantes:
Backend (API): A API deve ser iniciada com o comando uvicorn antes de rodar o frontend.

Frontend (Streamlit): Certifique-se de entrar na pasta api antes de rodar o frontend, já que o frontend.py está localizado lá.


### 📤 Treinamento do Modelo
Este método permite treinar o modelo via API
## Endpoint: `POST /treinar-modelo`
```bash
curl --location 'http://localhost:8000/treinar-modelo' \
--form 'dataset_path="Cortantes.v1i.yolov12"' \
--form 'epochs="100"'
```

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
### Importante: O modelo inicial do YOLO deve estar presente em uma pasta na raiz do projeto com o seguinte nome: Cortantes.v1i.yolov12 
---

## 📼 Análise de Vídeo

### Endpoint: `POST /analisar-video`
```bash
curl --location 'http://127.0.0.1:8000/analisar-video' \
--header 'accept: application/json' \
--form 'video=@"/C:/Users/sharp-objects-detection/videos/input/video2.mp4"' \
--form 'alertar_telegram="False"' \
--form 'usuario_telegram="rrr"' \
--form 'gerar_video="true"' \
--form 'alertar_email="False"' \
--form 'destinatario_email="xxx@gmail.com"'
```

### Endpoint: `POST /registrar-telegram`
```bash
curl --location 'http://127.0.0.1:8000/registrar-telegram' \
--header 'accept: application/json' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'usuario_telegram=rrr'
```
Importante: Este endpoint deve ser consumido somente após a interação com o bot no telegram. 
Abra seu Telegram e encontre o seguinte usuário: sharpobjectdetectionBot. Diga "Olá" para o sharpobjectdetectionBot iniciar uma conversa com você. para conferir se o usuário foi registrado no chat, basta acionar a api do Telegram informando o Token da conversa com o Bot: https://api.telegram.org/SEU-TOKEN-BOT/getUpdates


## 🔧 Requisitos
- Python 3.8+
- `yolov8n.pt` (modelo base da ultralytics)
- Dataset estruturado com `train/images`, `train/labels`, `valid/images`, `valid/labels`

### Manual do Usuário
```bash
1 - Passo 1: Faça o upload do vídeo que deseja ser analisado.
2 - Passo 2: Escolha o método de alerta.
  As opções de alerta disponíveis são:
     2.1 - Telegram: Informe o nome de usuário o Telegram, interaja com o Bot no telegram (sharpobjectdetectionBot)
     2.2 - E-mail: Informe o e-mail do destinatário para receber os alertas via e-mail.
     2.3 - Apenas gerar vídeo: Essa opção permite fazer o download do vídeo analisado.
3 - Escolha o limiar de confiança para a detecção de imagens.
```
