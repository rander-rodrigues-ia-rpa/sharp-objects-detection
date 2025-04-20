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

if 'usuario_telegram' not in st.session_state:
    st.session_state.usuario_telegram = None

if 'telegram_interacao_completa' not in st.session_state:
    st.session_state.telegram_interacao_completa = False  # Flag para controle da interação com o bot

# Inicializando o limiar de confiança com valor padrão
if 'limiar_confianca' not in st.session_state:
    st.session_state.limiar_confianca = 0.25  # Valor inicial do limiar de confiança

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
        
        if st.button("Continuar para métodos de alerta"):
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

# Etapa 2: Seleção do método de alerta
elif st.session_state.current_step == 2:
    st.markdown("<h2>Etapa 2: Método de Alerta</h2>", unsafe_allow_html=True)
    
    alerta_tipo = st.radio("Escolha como deseja receber o alerta:", ["Apenas Gerar Vídeo", "Telegram", "E-mail"])
    
    if alerta_tipo == "Telegram":
        usuario_telegram = st.text_input("Nome de usuário no Telegram (sem @):")
        st.session_state.usuario_telegram = usuario_telegram
        
        if usuario_telegram:
            # Exibir a mensagem de orientação sobre o Telegram
            st.markdown("""
            <div style="background-color: #cce5ff; padding: 15px; border-radius: 5px; border: 2px solid #007bff;">
                <strong style="color: #0056b3;">Atenção!</strong> Abra seu Telegram e encontre o seguinte usuário: 
                <strong style="color: #007bff;">sharpobjectdetectionBot</strong>. 
                Diga "Olá" para esse usuário para iniciar uma conversa com o Bot.
            </div>
            """, unsafe_allow_html=True)
            
            # Perguntar se já fez a interação com o bot
            interacao_completa = st.radio("Você já deu um olá para o sharpobjectdetectionBot?", ("Não", "Sim"))
            if interacao_completa == "Sim":
                st.session_state.telegram_interacao_completa = True
            else:
                st.session_state.telegram_interacao_completa = False

        # Avançar para a próxima etapa somente se a interação foi completada
        if st.session_state.telegram_interacao_completa and st.button("Continuar ➡️"):
            st.session_state.alerta_tipo = alerta_tipo        
            avançar_etapa()  # Avançar para a etapa 3

    elif alerta_tipo == "E-mail":
        destinatario_email = st.text_input("Destinatário do e-mail:")
        st.session_state.destinatario_email = destinatario_email
    
    # Avançar para a próxima etapa
    if alerta_tipo != "Telegram" and st.button("Continuar ➡️"):
        st.session_state.alerta_tipo = alerta_tipo        
        avançar_etapa()  # Avançar para a etapa 3

# Etapa 3: Processamento e resultados
elif st.session_state.current_step == 3:
    st.markdown("<h2>Etapa 3: Processamento e Resultados</h2>", unsafe_allow_html=True)
    
    # Mostrar o status do processamento (se o vídeo foi analisado)
    if not st.session_state.process_complete:
        
        # Adicionar a opção de selecionar o limiar de confiança antes de iniciar o processamento
        st.session_state.limiar_confianca = st.slider(
            "Limiar de Confiança", 
            min_value=0.1, 
            max_value=1.0, 
            value=st.session_state.limiar_confianca, 
            step=0.05,
            help="Quanto maior o valor, mais precisa será a detecção."
        )
        
        if st.button("Iniciar Processamento"):
            with st.spinner("Processando o vídeo..."):
                try:
                    # Ajuste para garantir que os parâmetros sejam passados corretamente
                    params = {
                        "alertar_telegram": st.session_state.alerta_tipo == "Telegram",
                        "alertar_email": st.session_state.alerta_tipo == "E-mail",
                        "usuario_telegram": st.session_state.usuario_telegram if st.session_state.alerta_tipo == "Telegram" else "",
                        "gerar_video": st.session_state.alerta_tipo == "Apenas Gerar Vídeo",
                        "destinatario_email": st.session_state.destinatario_email if st.session_state.alerta_tipo == "E-mail" else "",
                        "limiar_confianca": st.session_state.limiar_confianca  # Passando o limiar de confiança para a API
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
    
    # Se o processamento foi concluído, mostrar os resultados
    if st.session_state.process_complete:
        resultados = st.session_state.resultados
        if resultados.get("objeto_detectado", False):
            st.markdown("**Objetos cortantes detectados! Alertas enviados com sucesso**")
        else:
            st.markdown("**Nenhum objeto cortante detectado.**")
        
        # Exibir o caminho do vídeo processado (se estiver disponível)
        if 'video_processado' in resultados:
            st.markdown(f"**Vídeo processado gerado!**")
            video_path = resultados['video_processado']
            
            # Botão de download para o vídeo processado
            with open(video_path, "rb") as video_file:
                st.download_button(
                    label="📥 Baixar Vídeo Processado",
                    data=video_file,
                    file_name=os.path.basename(video_path),
                    mime="video/mp4"
                )
    
        # Reiniciar a aplicação para nova análise
        st.session_state.current_step = 1
