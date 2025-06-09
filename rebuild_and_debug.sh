#!/bin/bash

echo "🔧 Document OCR API - Rebuild & Debug Script"
echo "============================================"

# 1. Parar containers existentes
echo "🛑 Stopping existing containers..."
docker-compose down -v

# 2. Rebuild com cache limpo
echo "🔨 Building with no cache..."
docker-compose build --no-cache

# 3. Iniciar containers
echo "🚀 Starting containers..."
docker-compose up -d

# 4. Aguardar inicialização
echo "⏳ Waiting for services to start..."
sleep 20

# 5. Verificar status dos containers
echo "📊 Container status:"
docker-compose ps

# 6. Verificar logs do Ollama
echo ""
echo "🤖 Ollama logs (last 20 lines):"
docker-compose logs --tail=20 document-ocr-api | grep -E "(ollama|Ollama|OLLAMA)" || echo "No Ollama logs found"

# 7. Testar conectividade Ollama
echo ""
echo "🔗 Testing Ollama connectivity:"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is responding"
    curl -s http://localhost:11434/api/tags | head -5
else
    echo "❌ Ollama is not responding"
    echo "Container logs:"
    docker-compose logs --tail=50 document-ocr-api
fi

# 8. Testar API principal
echo ""
echo "🌐 Testing main API:"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Main API is responding"
    curl -s http://localhost:8000/health
else
    echo "❌ Main API is not responding"
fi

echo ""
echo "✅ Rebuild complete! Use the following commands to debug further:"
echo "📋 View all logs:       docker-compose logs -f"
echo "🤖 View Ollama logs:    docker-compose logs -f document-ocr-api | grep ollama"
echo "🐛 Enter container:     docker exec -it \$(docker-compose ps -q) bash"
echo "🔄 Restart services:    docker-compose restart" 