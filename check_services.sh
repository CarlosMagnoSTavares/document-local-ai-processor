#!/bin/bash

echo "🔍 Document OCR API - Service Check"
echo "=================================="

# 1. Verificar se containers estão rodando
echo "📦 Container Status:"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    echo "❌ docker-compose not found"
fi
echo ""

# 2. Verificar API principal
echo "🌐 Main API Health Check:"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Main API is responding"
    curl -s http://localhost:8000/health | jq '.' 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "❌ Main API is not responding on port 8000"
fi
echo ""

# 3. Verificar Ollama
echo "🤖 Ollama Service Check:"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is responding"
    echo "📋 Available models:"
    curl -s http://localhost:11434/api/tags | jq '.models[] | .name' 2>/dev/null || curl -s http://localhost:11434/api/tags
else
    echo "❌ Ollama is not responding on port 11434"
    echo "🔧 Try: docker-compose restart"
fi
echo ""

# 4. Verificar Redis
echo "🔴 Redis Service Check:"
if command -v redis-cli &> /dev/null; then
    if redis-cli -p 6379 ping > /dev/null 2>&1; then
        echo "✅ Redis is responding"
    else
        echo "❌ Redis is not responding on port 6379"
    fi
else
    # Verificar via container se possível
    if curl -s http://localhost:6379 > /dev/null 2>&1; then
        echo "✅ Redis port is open"
    else
        echo "❓ Redis status unknown (redis-cli not available)"
    fi
fi
echo ""

# 5. Logs recentes
echo "📋 Recent Logs (last 10 lines):"
if command -v docker-compose &> /dev/null; then
    docker-compose logs --tail=10 document-ocr-api | tail -10
else
    echo "❌ Cannot access logs - docker-compose not found"
fi

echo ""
echo "🔧 Quick Commands:"
echo "  📊 Full status:     docker-compose ps"
echo "  📋 All logs:        docker-compose logs -f"
echo "  🔄 Restart:         docker-compose restart"
echo "  🛠️ Rebuild:         ./rebuild_and_debug.sh" 