#!/bin/bash

echo "🧪 Document OCR LLM API - Complete Test Suite v1.5"
echo "=================================================="

# Configuration
BASE_URL="http://localhost:8000"
API_KEY="myelin-ocr-llm-2024-super-secret-key"
GEMINI_API_KEY="AIzaSyAxKbQ3ZryF5fYoppqFxIHe2fl6g10c67g"
DEBUG_MODE="1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test
run_test() {
    local test_name="$1"
    local expected_code="$2"
    local curl_command="$3"
    
    echo -e "\n${BLUE}🧪 Test: $test_name${NC}"
    echo "Command: $curl_command"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Execute curl and capture response
    response=$(eval "$curl_command" 2>/dev/null)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC} - $test_name"
        echo "Response: $response" | head -5
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # Extract document_id if present
        if [[ "$response" == *"document_id"* ]]; then
            DOCUMENT_ID=$(echo "$response" | grep -o '"document_id"[^,]*' | grep -o '[0-9]*' | head -1)
            if [[ -n "$DOCUMENT_ID" ]]; then
                echo "📄 Document ID extracted: $DOCUMENT_ID"
            fi
        fi
    else
        echo -e "${RED}❌ FAILED${NC} - $test_name"
        echo "Error: Command failed or server not responding"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Start testing
echo -e "\n${YELLOW}🔧 Starting systematic API testing...${NC}"

# 1. Status & Information Tests
echo -e "\n${BLUE}=== 1. STATUS & INFORMATION TESTS ===${NC}"

run_test "Health Check" 200 \
    "curl -s -w '%{http_code}' $BASE_URL/health"

run_test "API Information" 200 \
    "curl -s -w '%{http_code}' $BASE_URL/"

# 2. Model Management Tests
echo -e "\n${BLUE}=== 2. MODEL MANAGEMENT TESTS ===${NC}"

run_test "List Ollama Models" 200 \
    "curl -s -w '%{http_code}' -H 'Key: $API_KEY' $BASE_URL/models/list"

run_test "List Gemini Models" 200 \
    "curl -s -w '%{http_code}' -H 'Key: $API_KEY' -H 'Gemini-API-Key: $GEMINI_API_KEY' $BASE_URL/models/gemini"

# 3. Upload Tests (need sample files)
echo -e "\n${BLUE}=== 3. SMART UPLOAD TESTS ===${NC}"

# Create a simple test file
echo "Test document content for OCR processing" > test_document.txt

# Test Ollama Upload
run_test "Ollama Upload (TXT)" 200 \
    "curl -s -w '%{http_code}' -X POST \
    -H 'Key: $API_KEY' \
    -H 'Prompt: Extract all information from this document' \
    -H 'Format-Response: [{\"content\": \"\"}]' \
    -H 'Model: gemma3:1b' \
    -H 'AI-Provider: ollama' \
    -H 'debug: $DEBUG_MODE' \
    -F 'file=@test_document.txt' \
    $BASE_URL/upload"

# Test Gemini Upload  
run_test "Gemini Upload (TXT)" 200 \
    "curl -s -w '%{http_code}' -X POST \
    -H 'Key: $API_KEY' \
    -H 'Prompt: Extract all information from this document' \
    -H 'Format-Response: [{\"content\": \"\"}]' \
    -H 'Model: gemini-2.0-flash' \
    -H 'AI-Provider: gemini' \
    -H 'Gemini-API-Key: $GEMINI_API_KEY' \
    -H 'debug: $DEBUG_MODE' \
    -F 'file=@test_document.txt' \
    $BASE_URL/upload"

# 4. Queue Status Tests
echo -e "\n${BLUE}=== 4. MONITOR PROCESSING TESTS ===${NC}"

run_test "Queue Status" 200 \
    "curl -s -w '%{http_code}' -H 'Key: $API_KEY' $BASE_URL/queue"

run_test "Queue Status with Debug" 200 \
    "curl -s -w '%{http_code}' -H 'Key: $API_KEY' -H 'debug: $DEBUG_MODE' $BASE_URL/queue"

# 5. Results Tests (if we have a document_id)
if [[ -n "$DOCUMENT_ID" ]]; then
    echo -e "\n${BLUE}=== 5. GET RESULTS TESTS ===${NC}"
    
    run_test "Get Document Response" 200 \
        "curl -s -w '%{http_code}' -H 'Key: $API_KEY' $BASE_URL/response/$DOCUMENT_ID"
    
    run_test "Get Document Response with Debug" 200 \
        "curl -s -w '%{http_code}' -H 'Key: $API_KEY' -H 'debug: $DEBUG_MODE' $BASE_URL/response/$DOCUMENT_ID"
        
    # 6. Debug & Diagnostics Tests
    echo -e "\n${BLUE}=== 6. DEBUG & DIAGNOSTICS TESTS ===${NC}"
    
    run_test "Comprehensive Document Debug" 200 \
        "curl -s -w '%{http_code}' -H 'Key: $API_KEY' $BASE_URL/debug/document/$DOCUMENT_ID"
else
    echo -e "\n${YELLOW}⚠️ Skipping results tests - no document_id available${NC}"
fi

# 7. Compute Configuration Tests
echo -e "\n${BLUE}=== 7. COMPUTE CONFIGURATION TESTS ===${NC}"

run_test "Get Current Compute Mode" 200 \
    "curl -s -w '%{http_code}' -H 'Key: $API_KEY' $BASE_URL/config/compute"

run_test "Set CPU Mode" 200 \
    "curl -s -w '%{http_code}' -X POST -H 'Key: $API_KEY' -H 'Compute-Mode: cpu' $BASE_URL/config/compute"

# 8. Error Testing
echo -e "\n${BLUE}=== 8. ERROR TESTING ===${NC}"

run_test "Invalid API Key" 401 \
    "curl -s -w '%{http_code}' -H 'Key: invalid-key' $BASE_URL/queue"

run_test "Missing Gemini API Key" 400 \
    "curl -s -w '%{http_code}' -X POST \
    -H 'Key: $API_KEY' \
    -H 'Prompt: Test' \
    -H 'Format-Response: {}' \
    -H 'Model: gemini-2.0-flash' \
    -H 'AI-Provider: gemini' \
    -F 'file=@test_document.txt' \
    $BASE_URL/upload"

# Cleanup
rm -f test_document.txt

# Final Results
echo -e "\n${BLUE}=== FINAL TEST RESULTS ===${NC}"
echo -e "📊 Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}✅ Passed: $PASSED_TESTS${NC}"
echo -e "${RED}❌ Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! API is working correctly.${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️ Some tests failed. Check the system and retry.${NC}"
    echo -e "\n${YELLOW}💡 Quick fixes:${NC}"
    echo "1. Check if Docker is running: docker-compose ps"
    echo "2. Restart services: docker-compose restart"
    echo "3. Check logs: docker-compose logs -f"
    echo "4. Use debug script: ./rebuild_and_debug.sh"
    exit 1
fi 