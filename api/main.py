from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import shutil
import os
from app.detector import processar_video
from app.email_alert import enviar_email_alerta
from app.trainer import criar_config_yaml, treinar_modelo
from datetime import datetime

app = FastAPI()

MODELO_PATH = 'models/objeto_cortante.pt'

@app.post("/analisar-video")
def analisar_video(
    video: UploadFile,
    alertar_email: bool = Form(...),
    gerar_video: bool = Form(...),
    destinatario: str = Form(default=''),
    remetente: str = Form(default=''),
    senha: str = Form(default='')
):
    input_path = f"videos/input/{video.filename}"
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = f"videos/output/processado_{current_datetime}_{video.filename}"

    video_processado, objeto_detectado = processar_video(MODELO_PATH, input_path, output_path)

    if alertar_email and objeto_detectado:
        sucesso = enviar_email_alerta(destinatario, remetente, senha, video.filename)
        if not sucesso:
            return JSONResponse(status_code=500, content={"mensagem": "Erro ao enviar e-mail."})

    resposta = {"objeto_detectado": objeto_detectado}

    if gerar_video:
        resposta["video_processado"] = video_processado

    return resposta

@app.post("/treinar-modelo")
def treinar_modelo_api(
    dataset_path: str = Form(...),
    epochs: int = Form(default=80)
):
    try:
        config_path = criar_config_yaml(dataset_path)
        resultados = treinar_modelo(config_path, epochs=epochs)

        modelo_treinado_path = os.path.join("runs", "detect", "objeto_cortante_detector", "weights", "best.pt")
        if os.path.exists(modelo_treinado_path):
            os.makedirs("models", exist_ok=True)
            shutil.copy(modelo_treinado_path, MODELO_PATH)

        return {"mensagem": "Treinamento concluído com sucesso.", "modelo_salvo_em": MODELO_PATH}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})
