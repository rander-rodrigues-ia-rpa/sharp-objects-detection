import requests
import time
import logging
import os
from requests.exceptions import RequestException

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='telegram_alerts.log'
)
logger = logging.getLogger(__name__)

def enviar_alerta_telegram(chat_id, token, mensagem, foto_path=None, max_retries=3, delay=2):
    """
    Envia um alerta para o Telegram com retentativas em caso de falha.
    
    Args:
        chat_id: ID do chat do Telegram
        token: Token do bot do Telegram
        mensagem: Mensagem a ser enviada
        foto_path: Caminho para a imagem (opcional)
        max_retries: Número máximo de tentativas
        delay: Tempo de espera entre tentativas
    
    Returns:
        bool: True se o envio foi bem-sucedido, False caso contrário
    """
    for attempt in range(max_retries):
        try:
            # Verificar se o chat_id é válido
            if not chat_id:
                logger.error("Chat ID inválido")
                return False
            
            # Enviar a mensagem
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            parametros = {
                'chat_id': chat_id,
                'text': mensagem,
                'parse_mode': 'HTML'  # Permite formatação básica
            }
            response_msg = requests.post(url, params=parametros, timeout=30)
            response_msg.raise_for_status()  # Levanta exceção para status codes 4XX/5XX
            
            # Verificar resposta do Telegram para mensagem
            if not response_msg.json().get('ok'):
                logger.error(f"Erro ao enviar mensagem: {response_msg.json()}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                return False
            
            # Enviar a foto se houver
            if foto_path and os.path.exists(foto_path):
                try:
                    url = f"https://api.telegram.org/bot{token}/sendPhoto"
                    with open(foto_path, 'rb') as photo:
                        files = {'photo': photo}
                        parametros = {'chat_id': chat_id}
                        response_photo = requests.post(url, params=parametros, files=files, timeout=60)
                        response_photo.raise_for_status()
                        
                        # Verificar resposta do Telegram para foto
                        if not response_photo.json().get('ok'):
                            logger.warning(f"Erro ao enviar foto: {response_photo.json()}")
                            # Continuar mesmo se a foto falhar
                except Exception as e:
                    logger.warning(f"Erro ao enviar foto: {str(e)}")
                    # Continuar mesmo se a foto falhar
            elif foto_path and not os.path.exists(foto_path):
                logger.warning(f"Arquivo de imagem não encontrado: {foto_path}")
                # Continuar mesmo se a foto não existir
            
            logger.info(f"Alerta enviado com sucesso para {chat_id}")
            return True
            
        except RequestException as e:
            logger.warning(f"Tentativa {attempt+1}/{max_retries} falhou: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)  # Esperar antes de tentar novamente
            else:
                logger.error(f"Falha ao enviar alerta após {max_retries} tentativas")
                return False
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar alerta: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                return False

def gerar_mensagem_padrao(video_nome, objeto_detectado, confianca=None, frame_num=None):
    """
    Gera uma mensagem formatada para o alerta do Telegram.
    
    Args:
        video_nome: Nome do vídeo analisado
        objeto_detectado: Se foi detectado um objeto
        confianca: Percentual de confiança da detecção
        frame_num: Número do frame onde o objeto foi detectado
    
    Returns:
        str: Mensagem formatada
    """
    if objeto_detectado:
        confianca_str = f" (Confiança: {confianca*100:.1f}%)" if confianca is not None else ""
        frame_str = f" - Frame #{frame_num}" if frame_num is not None else ""
        return f"<b>⚠️ ALERTA</b>: Objeto cortante detectado!\n\nVídeo: <code>{video_nome}</code>{frame_str}{confianca_str}"
    else:
        return f"✅ Sem objetos cortantes detectados no vídeo: <code>{video_nome}</code>"