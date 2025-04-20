from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import shutil
import os
import json
import requests
import asyncio
import logging
from app.detector import processar_video
from app.alerta_telegram import enviar_alerta_telegram, gerar_mensagem_padrao
from datetime import datetime
import base64
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

MODELO_PATH = os.environ.get('MODELO_PATH')
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
URL_LAMBDA = os.environ.get('URL_LAMBDA')

app = FastAPI()


# Função para enviar mensagem ao usuário e capturar o chat_id automaticamente
def registrar_telegram_usuario(usuario_telegram):
    """
    Registra um usuário do Telegram e obtém seu chat_id.
    """
    try:
        # Enviar mensagem para o usuário, isso vai fazer o Telegram registrar o chat_id
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        parametros = {
            'chat_id': usuario_telegram,  # Nome de usuário no Telegram
            'text': "Olá! Seu chat ID foi registrado com sucesso. Agora você pode enviar vídeos para análise!"
        }
        
        # Enviar a requisição e obter a resposta
        response = requests.post(url, params=parametros, timeout=30)
        
        # Verificar se a resposta foi bem-sucedida
        if response.status_code != 200:
            logger.error(f"Erro ao registrar usuário: {response.text}")
            return None
            
        # Exibir a resposta do Telegram para depuração
        logger.info(f"Resposta do Telegram: {response.json()}")
        
        # Tentar obter o chat_id da resposta
        chat_id = response.json().get("result", {}).get("chat", {}).get("id")
        
        return chat_id
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {str(e)}")
        return None


# Função para obter o chat_id automaticamente
def obter_chat_id(username):
    """
    Obtém o chat_id de um usuário específico através do nome de usuário do Telegram.
    Utiliza o método getUpdates para procurar pelo username e obter o chat_id associado.
    """
    try:

        # Usar o getUpdates para capturar as mensagens enviadas para o bot
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/getUpdates"
        response = requests.get(url, timeout=30)
        
        # Verificar se a resposta foi bem-sucedida
        data = response.json()
        
        # Verificar se há mensagens e procurar pelo username
        if data["ok"] and len(data["result"]) > 0:
            for update in data["result"]:
                message = update.get("message", {})
                chat = message.get("chat", {})
                from_user = message.get("from", {})
                
                # Verificar se o username corresponde ao fornecido
                if from_user.get("username") == username:
                    chat_id = chat.get("id")
                    return chat_id
        
        # Se não encontrar o username, retornar None
        return None

    except Exception as e:
        logger.error(f"Erro ao obter chat_id para {username}: {str(e)}")
        return None

# Endpoint para registrar o usuário do Telegram
@app.post("/registrar-telegram")
def registrar_telegram(usuario_telegram: str = Form(...)):
    try:
        # Obter o chat_id automaticamente ao interagir com o bot
        chat_id = obter_chat_id(usuario_telegram)
        
        if chat_id is None:
            # Tentar registrar diretamente
            chat_id = registrar_telegram_usuario(usuario_telegram)
        
        if chat_id is None:
            return JSONResponse(status_code=400, content={"mensagem": "Não foi possível obter o chat_id. Verifique se o bot recebeu a mensagem."})

        # Verificar se o arquivo já existe. Caso contrário, criá-lo
        try:
            with open("usuarios_telegram.json", "r") as file:
                usuarios = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            usuarios = {}

        # Armazenar o chat_id associado ao usuário
        usuarios[usuario_telegram] = chat_id
        
        # Salvar novamente os dados no arquivo
        with open("usuarios_telegram.json", "w") as file:
            json.dump(usuarios, file)
        
        return {"mensagem": f"Usuário {usuario_telegram} registrado com sucesso!", "chat_id": chat_id}
    except Exception as e:
        logger.error(f"Erro no registro do Telegram: {str(e)}")
        return JSONResponse(status_code=500, content={"erro": str(e)})
    
@app.post("/analisar-video")
async def analisar_video(
    video: UploadFile,
    alertar_telegram: bool = Form(...),  # Adicionado parâmetro para enviar alerta via Telegram
    alertar_email: bool = Form(False),  # Parâmetro para enviar por e-mail
    usuario_telegram: str = Form(...),   # Nome de usuário do Telegram
    gerar_video: bool = Form(...),      # Se deve gerar vídeo processado
    limiar_confianca: float = Form(0.25), # Limiar de confiança para a detecção
    destinatario_email: str = Form(default="")  # Remetente do e-mail
):

    try:

        if alertar_telegram:
            # Buscar o chat_id do usuário no arquivo JSON
            try:
                with open("usuarios_telegram.json", "r") as file:
                    usuarios = json.load(file)
                chat_id_telegram = usuarios.get(usuario_telegram)
            except (FileNotFoundError, json.JSONDecodeError):
                return JSONResponse(status_code=400, content={"mensagem": "Usuário não registrado. Registre-se primeiro no bot."})

            if not chat_id_telegram:
                return JSONResponse(status_code=400, content={"mensagem": "Usuário não registrado. Registre-se primeiro no bot."})

        # Criar diretórios necessários
        os.makedirs("videos/input", exist_ok=True)
        os.makedirs("c:/temp/videos/output", exist_ok=True)
        
        # Criar diretório para salvar os frames com detecções
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        frames_dir = f"videos/frames/{timestamp}_{video.filename.split('.')[0]}"
        os.makedirs(frames_dir, exist_ok=True)

        # Salvar o vídeo recebido
        input_path = f"videos/input/{video.filename}"
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        output_path = f"c:/temp/videos/output/processado_{timestamp}_{video.filename}" if gerar_video else None

        # Processar o vídeo e detectar objetos cortantes
        video_processado, deteccoes = processar_video(
            modelo_path=MODELO_PATH, 
            input_path=input_path, 
            output_path=output_path,
            limiar_confianca=limiar_confianca,
            salvar_frames=True,
            frames_dir=frames_dir
        )

        # Verificar se algum objeto foi detectado
        objeto_detectado = len(deteccoes) > 0
        
        resposta = {
            "objeto_detectado": objeto_detectado,
            "total_deteccoes": len(deteccoes)
        }

        # Enviar alertas via Telegram para cada detecção
        alertas_enviados = 0
        falhas_envio = 0

        # Enviar e-mail com os frames detectados, se solicitado
        if alertar_email and objeto_detectado:
            for deteccao in deteccoes:
                frame_path = deteccao.get("frame_path")
                
                # Converter o frame para base64
                with open(frame_path, "rb") as img_file:
                    imagem_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                    imagem_base64 = f"data:image/png;base64,{imagem_base64}" 

                # Montar o payload para o envio via API Lambda
                payload = {
                    "email": destinatario_email,
                    "mensagem": "Olá, segue em anexo uma imagem registrada por nossos sistemas de vigilância.",
                    "imagemBase64": imagem_base64
                }

                # Enviar o e-mail via Lambda API
                response = requests.post(URL_LAMBDA, json=payload)

                # Adicionar um tempo de espera de 3 segundos antes de continuar
                time.sleep(3)

                # Verificar o sucesso do envio
                if response.status_code == 200:
                    resposta["alerta_email"] = f"E-mail enviado com sucesso com os frames detectados."
                else:
                    resposta["alerta_email"] = f"Falha ao enviar e-mail. Status: {response.status_code}"

        
        if alertar_telegram and objeto_detectado:
            # Para limitar a quantidade de alertas em vídeos com muitas detecções
            max_alertas = 10  # Limite de alertas para não sobrecarregar o usuário
            
            # Se houver muitas detecções, escolher frames mais espaçados
            if len(deteccoes) > max_alertas:
                # Selecionar detecções distribuídas uniformemente
                indices = [int(i * len(deteccoes) / max_alertas) for i in range(max_alertas)]
                deteccoes_selecionadas = [deteccoes[i] for i in indices]
            else:
                deteccoes_selecionadas = deteccoes
            
            for idx, deteccao in enumerate(deteccoes_selecionadas):
                frame_num = deteccao.get("frame_num")
                confianca = deteccao.get("confianca")
                frame_path = deteccao.get("frame_path")
                
                # Gerar mensagem para esta detecção específica
                mensagem = gerar_mensagem_padrao(
                    video_nome=video.filename,
                    objeto_detectado=True,
                    confianca=confianca,
                    frame_num=frame_num
                )
                
                # Enviar alerta com o frame capturado
                sucesso = enviar_alerta_telegram(
                    chat_id=chat_id_telegram,
                    token=TOKEN_TELEGRAM,
                    mensagem=mensagem,
                    foto_path=frame_path
                )
                
                if sucesso:
                    alertas_enviados += 1
                else:
                    falhas_envio += 1
                
                # Aguardar um pouco entre os envios para evitar limitação de taxa
                if idx < len(deteccoes_selecionadas) - 1:
                    await asyncio.sleep(1)
            
            # Se houver mais detecções do que o limite, enviar um alerta resumido
            if len(deteccoes) > max_alertas:
                mensagem_resumo = (
                    f"<b>⚠️ RESUMO DE ALERTAS</b>: Foram detectados um total de {len(deteccoes)} objetos cortantes "
                    f"no vídeo <code>{video.filename}</code>. Mostrando {max_alertas} detecções representativas."
                )
                enviar_alerta_telegram(
                    chat_id=chat_id_telegram,
                    token=TOKEN_TELEGRAM,
                    mensagem=mensagem_resumo
                )
            
            # Adicionar resumo à resposta
            resposta["alerta_telegram"] = f"{alertas_enviados} de {len(deteccoes_selecionadas)} alertas enviados com sucesso via Telegram."
            if falhas_envio > 0:
                resposta["falhas_telegram"] = f"{falhas_envio} alertas falharam ao enviar."
                
        elif alertar_telegram and not objeto_detectado:
            # Enviar mensagem de que nenhum objeto foi detectado
            mensagem = gerar_mensagem_padrao(video.filename, False)
            sucesso = enviar_alerta_telegram(
                chat_id=chat_id_telegram, 
                token=TOKEN_TELEGRAM, 
                mensagem=mensagem
            )
            
            if sucesso:
                resposta["alerta_telegram"] = "Mensagem de 'nenhuma detecção' enviada com sucesso."
            else:
                resposta["alerta_telegram"] = "Falha ao enviar mensagem via Telegram."

        if gerar_video and video_processado:
            resposta["video_processado"] = video_processado

        return resposta
    except Exception as e:
        import traceback
        stack_trace = traceback.format_exc()
        logger.error(f"Erro ao analisar vídeo: {str(e)}\n{stack_trace}")
        return JSONResponse(
            status_code=500, 
            content={"erro": str(e), "detalhes": stack_trace}
        )