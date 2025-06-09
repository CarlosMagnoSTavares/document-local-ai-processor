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
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_DEBUG=1
export OLLAMA_ORIGINS=*

ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready with retry logic
echo "⏳ Waiting for Ollama to be ready..."
RETRY_COUNT=0
MAX_RETRIES=30
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Ollama failed to start after $MAX_RETRIES attempts"
        break
    fi
    echo "🔄 Attempt $((RETRY_COUNT + 1))/$MAX_RETRIES - Waiting for Ollama..."
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is ready!"
    
    # Pull the default model
    echo "📥 Pulling gemma3:1b model..."
    if ! ollama pull gemma3:1b; then
        echo "⚠️ Failed to pull gemma3:1b, trying qwen2:0.5b..."
        ollama pull qwen2:0.5b
    fi
else
    echo "⚠️ Ollama may not be fully ready, continuing with startup..."
fi

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