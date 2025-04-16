# Dockerfile
FROM python:3.10-slim

# Diretório de trabalho
WORKDIR /app

# Copiar tudo para dentro do container
COPY . .

# Instalar dependências
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expor porta da API
EXPOSE 8000

# Comando para rodar a API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
