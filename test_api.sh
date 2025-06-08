#!/bin/bash

# Configuration
API_URL="http://localhost:8000"
API_KEY="your-super-secret-api-key-here"
TEST_FILE="teste.jpg"

echo "🧪 Testing Document OCR LLM API"
echo "================================"

# Test 1: Health Check
echo ""
echo "1️⃣ Testing health endpoint..."
curl -X GET "$API_URL/health" | jq .

# Test 2: Root endpoint
echo ""
echo "2️⃣ Testing root endpoint..."
curl -X GET "$API_URL/" | jq .

# Test 3: Upload document
echo ""
echo "3️⃣ Testing document upload..."
if [ -f "$TEST_FILE" ]; then
    UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/upload" \
        -H "Key: $API_KEY" \
        -H "Prompt: Verifique qual CNPJ existe nesse documento" \
        -H "Format-Response: [{\"CNPJ\": \"\"}]" \
        -H "Model: gemma3:1b" \
        -H "Example: [{\"CNPJ\": \"XX.XXX.XXX/0001-XX\"}]" \
        -F "file=@$TEST_FILE")
    
    echo "$UPLOAD_RESPONSE" | jq .
    
    # Extract document ID for further tests
    DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.document_id')
    echo "📄 Document ID: $DOCUMENT_ID"
else
    echo "❌ Test file '$TEST_FILE' not found!"
    exit 1
fi

# Test 4: Check queue status
echo ""
echo "4️⃣ Testing queue status..."
curl -s -X GET "$API_URL/queue" \
    -H "Key: $API_KEY" | jq .

# Test 5: Get document response (may be processing)
echo ""
echo "5️⃣ Testing document response..."
if [ "$DOCUMENT_ID" != "null" ] && [ "$DOCUMENT_ID" != "" ]; then
    curl -s -X GET "$API_URL/response/$DOCUMENT_ID" \
        -H "Key: $API_KEY" | jq .
fi

# Test 6: Test with invalid API key
echo ""
echo "6️⃣ Testing invalid API key..."
curl -s -X GET "$API_URL/queue" \
    -H "Key: invalid-key" | jq .

echo ""
echo "✅ Testing completed!"
echo ""
echo "💡 Tips:"
echo "- Wait a few moments and check the response again: curl -H 'Key: $API_KEY' '$API_URL/response/$DOCUMENT_ID'"
echo "- Check queue status: curl -H 'Key: $API_KEY' '$API_URL/queue'"
echo "- Check logs: docker logs <container_name>" 