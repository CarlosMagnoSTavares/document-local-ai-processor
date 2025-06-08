#!/bin/bash

echo "🚀 Starting Document OCR LLM API..."

# Create necessary directories
mkdir -p /var/log/supervisor
mkdir -p /app/logs
mkdir -p /app/uploads
mkdir -p /app/temp

# Copy .env.example to .env if .env doesn't exist
if [ ! -f /app/.env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp /app/.env.example /app/.env
fi

# Start Ollama in background and pull the model
echo "🤖 Starting Ollama and pulling model..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
sleep 10

# Pull the default model
echo "📥 Pulling gemma3:1b model..."
ollama pull gemma3:1b

# Stop Ollama (supervisor will restart it)
kill $OLLAMA_PID || true

# Wait a moment
sleep 5

# Initialize database
echo "🗄️ Initializing database..."
cd /app
python3 -c "from database import init_database_sync; init_database_sync()"

# Start all services with supervisor
echo "🎛️ Starting all services with supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf 