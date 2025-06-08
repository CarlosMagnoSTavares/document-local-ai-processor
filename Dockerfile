FROM ubuntu:22.04

# Evitar interações durante instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Atualizar sistema e instalar dependências básicas
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev \
    poppler-utils \
    libpoppler-cpp-dev \
    curl \
    wget \
    git \
    redis-server \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Instalar Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/uploads /app/logs /app/temp

# Configurar supervisor para gerenciar serviços
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expor portas
EXPOSE 8000 6379

# Script de inicialização
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Comando principal
CMD ["/start.sh"] 