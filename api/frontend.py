import streamlit as st
import os
import requests
import json
import logging

# Configuração do Logger
logging.basicConfig(
    level=logging.DEBUG,  # Defina o nível de log para DEBUG, INFO, WARNING, ERROR ou CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log para o console
        logging.FileHandler("app.log")  # Log também em um arquivo
    ]
)

logger = logging.getLogger()

# Configuração da URL da API
API_URL = "http://localhost:8000"  # Ajuste para a URL correta da sua API FastAPI

# Inicialização de estados da sessão
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

if 'video_path' not in st.session_state:
    st.session_state.video_path = None

if 'process_complete' not in st.session_state:
    st.session_state.process_complete = False

if 'resultados' not in st.session_state:
    st.session_state.resultados = None

# Controle de botão para evitar duplo clique
if 'botao_ativo' not in st.session_state:
    st.session_state.botao_ativo = True  # Definir inicialmente o botão como "ativo"

# Função para avançar para a próxima etapa
def avançar_etapa():
    st.session_state.current_step += 1
    logger.info(f"Avançando para a etapa {st.session_state.current_step}")

# Função para voltar à etapa anterior
def voltar_etapa():
    st.session_state.current_step -= 1
    logger.info(f"Voltando para a etapa {st.session_state.current_step}")

# Função para interagir com a API e analisar o vídeo
def analisar_video_api(video_path, params):
    try:
        logger.info(f"Analisando o vídeo: {video_path}")
        with open(video_path, "rb") as video_file:
            files = {"video": (os.path.basename(video_path), video_file)}
            response = requests.post(
                f"{API_URL}/analisar-video",
                files=files,
                data=params
            )
            return response.json()
    except Exception as e:
        logger.error(f"Erro ao processar o vídeo na API: {str(e)}")
        return {"erro": str(e)}

# Etapa 1: Upload de vídeo
if st.session_state.current_step == 1:
    st.markdown("<h2>Etapa 1: Upload do Vídeo</h2>", unsafe_allow_html=True)
    
    video_file = st.file_uploader("Faça upload do seu vídeo para análise", type=["mp4", "avi", "mov", "mkv"])
    
    if video_file is not None:
        st.video(video_file)  # Exibir prévia do vídeo
        
        if st.button("Continuar para métodos de alerta", disabled=not st.session_state.botao_ativo):
            # Desabilitar o botão para evitar duplo clique
            st.session_state.botao_ativo = False
            
            with st.spinner("Preparando o vídeo..."):
                try:
                    # Salvar o vídeo
                    temp_path = f"c:/temp/temp_videos/{video_file.name}"
                    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                    with open(temp_path, "wb") as f:
                        f.write(video_file.getbuffer())
                    st.session_state.video_path = temp_path
                    logger.info(f"Vídeo salvo em {temp_path}")
                    
                    # Avançar para a próxima etapa
                    avançar_etapa()
                except Exception as e:
                    logger.error(f"Erro ao salvar o vídeo: {str(e)}")
                    st.error("Erro ao salvar o vídeo.")
                finally:
                    # Reabilitar o botão após a execução
                    st.session_state.botao_ativo = True

# Etapa 2: Seleção do método de alerta
elif st.session_state.current_step == 2:
    st.markdown("<h2>Etapa 2: Método de Alerta</h2>", unsafe_allow_html=True)
    
    alerta_tipo = st.radio("Escolha como deseja receber o alerta:", ["Apenas Gerar Vídeo", "Telegram", "E-mail"])
    
    if alerta_tipo == "Telegram":
        usuario_telegram = st.text_input("Nome de usuário no Telegram (sem @):")
        st.session_state.usuario_telegram = usuario_telegram
    
    elif alerta_tipo == "E-mail":
        destinatario_email = st.text_input("Destinatário do e-mail:")
        st.session_state.destinatario_email = destinatario_email
    
    # Avançar para a próxima etapa
    if st.button("Continuar ➡️", disabled=not st.session_state.botao_ativo):
        st.session_state.alerta_tipo = alerta_tipo        
        avançar_etapa()  # Avançar para a etapa 3

# Etapa 3: Processamento e resultados
elif st.session_state.current_step == 3:
    st.markdown("<h2>Etapa 3: Processamento e Resultados</h2>", unsafe_allow_html=True)
    
    # Mostrar o status do processamento (se o vídeo foi analisado)
    if not st.session_state.process_complete:
        st.markdown("Processando o vídeo...")
        
        if st.button("Iniciar Processamento", disabled=not st.session_state.botao_ativo):
            # Desabilitar o botão para evitar duplo clique
            st.session_state.botao_ativo = False
            
            with st.spinner("Processando o vídeo..."):
                try:
                    # Ajuste para garantir que os parâmetros sejam passados corretamente
                    params = {
                        "alertar_telegram": st.session_state.alerta_tipo == "Telegram",
                        "alertar_email": st.session_state.alerta_tipo == "E-mail",
                        "usuario_telegram": st.session_state.usuario_telegram if st.session_state.alerta_tipo == "Telegram" else "",
                        "gerar_video": st.session_state.alerta_tipo == "Apenas Gerar Vídeo",
                        "destinatario_email": st.session_state.destinatario_email if st.session_state.alerta_tipo == "E-mail" else ""
                    }

                    logger.info(f"Parâmetros enviados para a API: {params}")

                    # Chama a função para analisar o vídeo na API
                    resultados = analisar_video_api(st.session_state.video_path, params)
                    st.session_state.resultados = resultados
                    st.session_state.process_complete = True
                    
                    # Avançar para a próxima etapa
                    avançar_etapa()

                except Exception as e:
                    logger.error(f"Erro ao processar o vídeo: {str(e)}")
                    st.error("Erro ao processar o vídeo.")
                finally:
                    # Reabilitar o botão após a execução
                    st.session_state.botao_ativo = True
    
    # Se o processamento foi concluído, mostrar os resultados
    if st.session_state.process_complete:
        resultados = st.session_state.resultados
        if resultados.get("objeto_detectado", False):
            st.markdown("**Objetos cortantes detectados! Alertas enviados com sucesso**")
        else:
            st.markdown("**Nenhum objeto cortante detectado.**")
        # Reiniciar a aplicação para nova análise
        st.session_state.current_step = 1
