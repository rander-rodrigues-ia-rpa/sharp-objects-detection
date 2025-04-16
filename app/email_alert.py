import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_email_alerta(destinatario, remetente, senha_remetente, video_nome):
    assunto = "Alerta: Objeto cortante detectado"
    corpo = f"Foi detectado um objeto cortante no vídeo: {video_nome}"

    mensagem = MIMEMultipart()
    mensagem['From'] = remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = assunto
    mensagem.attach(MIMEText(corpo, 'plain'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remetente, senha_remetente)
        servidor.sendmail(remetente, destinatario, mensagem.as_string())
        servidor.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False
