#!/usr/bin/env python3
"""
🧠 COMPREHENSIVE API TEST SUITE - Document OCR LLM API
=======================================================

This script tests all API endpoints from the Postman collection with verbose mode.
Based on the complete collection v1.5 with all 8 test sections.

Test Sections:
1. Status & Information
2. Model Management (Ollama + Gemini)
3. Smart Upload (Multi-Provider)
4. Monitor Processing
5. Get Results (with Debug)
6. Debug & Diagnostics
7. Compute Configuration
8. Error Testing

Usage:
    python comprehensive_api_test.py

Requirements:
    - API running on localhost:8000
    - Test PDF file: iso-14001 Antiga.pdf
    - Valid API keys configured
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "myelin-ocr-llm-2024-super-secret-key"
GEMINI_API_KEY = "AIzaSyAxKbQ3ZryF5fYoppqFxIHe2fl6g10c67g"
TEST_PDF_FILE = "iso-14001 Antiga.pdf"

# Global variables for test state
document_id = None
last_uploaded_filename = None
last_ai_provider = None
ollama_model = "gemma3:1b"
gemini_model = "gemini-2.0-flash"

class TestResults:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.results = []
    
    def add_result(self, test_name: str, success: bool, details: str = ""):
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
    
    def print_summary(self):
        print("\n" + "="*80)
        print("🧠 COMPREHENSIVE API TEST RESULTS SUMMARY")
        print("="*80)
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print("="*80)
        
        if self.failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print(f"\n📝 Detailed results saved to test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

# Initialize test results
test_results = TestResults()

def make_request(method: str, endpoint: str, headers: Dict[str, str] = None, 
                data: Dict[str, Any] = None, files: Dict[str, Any] = None, 
                timeout: int = 30) -> requests.Response:
    """Make HTTP request with proper error handling and verbose logging"""
    url = f"{BASE_URL}{endpoint}"
    
    # Default headers
    default_headers = {"Key": API_KEY}
    if headers:
        default_headers.update(headers)
    
    print(f"\n🔄 {method} {url}")
    print(f"📋 Headers: {json.dumps(default_headers, indent=2)}")
    
    if data:
        print(f"📦 Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=default_headers,
            json=data,
            files=files,
            timeout=timeout
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"📝 Response Body: {json.dumps(response_json, indent=2)}")
        except:
            print(f"📝 Response Body (text): {response.text[:500]}...")
        
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        raise

def test_health_check():
    """Test 1.1: Health Check"""
    try:
        response = make_request("GET", "/health", headers={})
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                test_results.add_result("Health Check", True, "API is healthy")
            else:
                test_results.add_result("Health Check", False, f"Unexpected status: {data.get('status')}")
        else:
            test_results.add_result("Health Check", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Health Check", False, f"Exception: {str(e)}")

def test_api_info():
    """Test 1.2: API Information"""
    try:
        response = make_request("GET", "/", headers={})
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "endpoints" in data:
                test_results.add_result("API Information", True, "API info retrieved successfully")
            else:
                test_results.add_result("API Information", False, "Missing expected fields in response")
        else:
            test_results.add_result("API Information", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("API Information", False, f"Exception: {str(e)}")

def test_list_ollama_models():
    """Test 2.1: List Ollama Models"""
    global ollama_model
    
    try:
        response = make_request("GET", "/models/list")
        
        if response.status_code == 200:
            data = response.json()
            if "models" in data and isinstance(data["models"], list):
                if len(data["models"]) > 0:
                    ollama_model = data["models"][0].get("name", ollama_model)
                    test_results.add_result("List Ollama Models", True, f"Found {len(data['models'])} models")
                else:
                    test_results.add_result("List Ollama Models", True, "No models found but API working")
            else:
                test_results.add_result("List Ollama Models", False, "Invalid response format")
        else:
            test_results.add_result("List Ollama Models", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("List Ollama Models", False, f"Exception: {str(e)}")

def test_list_gemini_models():
    """Test 2.2: List Gemini Models"""
    global gemini_model
    
    try:
        response = make_request("GET", "/models/gemini")
        
        if response.status_code == 200:
            data = response.json()
            if "models" in data and isinstance(data["models"], list):
                if len(data["models"]) > 0:
                    # Look for recommended model or use first one
                    recommended = next((m for m in data["models"] if m.get("name") == "gemini-2.0-flash"), None)
                    if recommended:
                        gemini_model = recommended["name"]
                    else:
                        gemini_model = data["models"][0].get("name", gemini_model)
                    test_results.add_result("List Gemini Models", True, f"Found {len(data['models'])} models")
                else:
                    test_results.add_result("List Gemini Models", True, "No models found but API working")
            else:
                test_results.add_result("List Gemini Models", False, "Invalid response format")
        else:
            test_results.add_result("List Gemini Models", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("List Gemini Models", False, f"Exception: {str(e)}")

def test_upload_ollama():
    """Test 3.1: Smart Upload with Ollama"""
    global document_id, last_uploaded_filename, last_ai_provider
    
    if not os.path.exists(TEST_PDF_FILE):
        test_results.add_result("Upload Ollama", False, f"Test file not found: {TEST_PDF_FILE}")
        return
    
    try:
        headers = {
            "Prompt": "Verifique qual CNPJ existe nesse documento e extraia todas as informações da empresa",
            "Format-Response": '[{"CNPJ": "", "empresa": "", "endereco": ""}]',
            "Model": ollama_model,
            "AI-Provider": "ollama",
            "Example": '[{"CNPJ": "12.345.678/0001-90", "empresa": "Empresa Exemplo LTDA", "endereco": "Rua das Flores, 123"}]'
        }
        
        with open(TEST_PDF_FILE, 'rb') as f:
            files = {"file": (TEST_PDF_FILE, f, "application/pdf")}
            response = make_request("POST", "/upload", headers=headers, files=files)
        
        if response.status_code == 200:
            data = response.json()
            if "document_id" in data:
                document_id = data["document_id"]
                last_uploaded_filename = data.get("filename", "")
                last_ai_provider = data.get("ai_provider", "")
                test_results.add_result("Upload Ollama", True, f"Document uploaded with ID: {document_id}")
            else:
                test_results.add_result("Upload Ollama", False, "Missing document_id in response")
        else:
            test_results.add_result("Upload Ollama", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Upload Ollama", False, f"Exception: {str(e)}")

def test_upload_gemini():
    """Test 3.2: Smart Upload with Gemini"""
    if not os.path.exists(TEST_PDF_FILE):
        test_results.add_result("Upload Gemini", False, f"Test file not found: {TEST_PDF_FILE}")
        return
    
    try:
        headers = {
            "Prompt": "Verifique qual CNPJ existe nesse documento e extraia todas as informações da empresa",
            "Format-Response": '[{"Dia da Leitura": ""}]',
            "Model": gemini_model,
            "AI-Provider": "gemini",

            "Example": '[{"Dia da Leitura": "31/12/9999"}]'
        }
        
        with open(TEST_PDF_FILE, 'rb') as f:
            files = {"file": (TEST_PDF_FILE, f, "application/pdf")}
            response = make_request("POST", "/upload", headers=headers, files=files)
        
        if response.status_code == 200:
            data = response.json()
            if "document_id" in data:
                test_results.add_result("Upload Gemini", True, f"Document uploaded with ID: {data['document_id']}")
            else:
                test_results.add_result("Upload Gemini", False, "Missing document_id in response")
        else:
            test_results.add_result("Upload Gemini", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Upload Gemini", False, f"Exception: {str(e)}")

def test_queue_status():
    """Test 4.1: Get Queue Status"""
    try:
        response = make_request("GET", "/queue")
        
        if response.status_code == 200:
            data = response.json()
            if "queue" in data and "total_documents" in data:
                test_results.add_result("Queue Status", True, f"Queue has {data['total_documents']} documents")
            else:
                test_results.add_result("Queue Status", False, "Invalid response format")
        else:
            test_results.add_result("Queue Status", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Queue Status", False, f"Exception: {str(e)}")

def test_queue_status_debug():
    """Test 4.2: Get Queue Status with Debug"""
    try:
        headers = {"debug": "1"}
        response = make_request("GET", "/queue", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "queue" in data:
                test_results.add_result("Queue Status Debug", True, "Debug queue status retrieved")
            else:
                test_results.add_result("Queue Status Debug", False, "Invalid response format")
        else:
            test_results.add_result("Queue Status Debug", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Queue Status Debug", False, f"Exception: {str(e)}")

def test_get_document_response():
    """Test 5.1: Get Document Response"""
    if not document_id:
        test_results.add_result("Get Document Response", False, "No document_id available")
        return
    
    try:
        response = make_request("GET", f"/response/{document_id}")
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                test_results.add_result("Get Document Response", True, "Document response retrieved")
            else:
                test_results.add_result("Get Document Response", False, "Invalid response format")
        elif response.status_code == 404:
            test_results.add_result("Get Document Response", False, "Document not found")
        else:
            test_results.add_result("Get Document Response", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Get Document Response", False, f"Exception: {str(e)}")

def test_get_document_response_debug():
    """Test 5.2: Get Document Response with Debug"""
    if not document_id:
        test_results.add_result("Get Document Response Debug", False, "No document_id available")
        return
    
    try:
        headers = {"debug": "1"}
        response = make_request("GET", f"/response/{document_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "debug_info" in data:
                test_results.add_result("Get Document Response Debug", True, "Debug response retrieved")
            else:
                test_results.add_result("Get Document Response Debug", False, "Missing debug_info in response")
        elif response.status_code == 404:
            test_results.add_result("Get Document Response Debug", False, "Document not found")
        else:
            test_results.add_result("Get Document Response Debug", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Get Document Response Debug", False, f"Exception: {str(e)}")

def test_debug_document():
    """Test 6.1: Comprehensive Document Debug"""
    if not document_id:
        test_results.add_result("Debug Document", False, "No document_id available")
        return
    
    try:
        response = make_request("GET", f"/debug/document/{document_id}")
        
        if response.status_code == 200:
            data = response.json()
            test_results.add_result("Debug Document", True, "Document debug completed")
        elif response.status_code == 404:
            test_results.add_result("Debug Document", False, "Document not found")
        else:
            test_results.add_result("Debug Document", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Debug Document", False, f"Exception: {str(e)}")

def test_get_compute_mode():
    """Test 7.1: Get Current Compute Mode"""
    try:
        response = make_request("GET", "/config/compute")
        
        if response.status_code == 200:
            data = response.json()
            if "compute_mode" in data:
                test_results.add_result("Get Compute Mode", True, f"Current mode: {data['compute_mode']}")
            else:
                test_results.add_result("Get Compute Mode", False, "Missing compute_mode in response")
        else:
            test_results.add_result("Get Compute Mode", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Get Compute Mode", False, f"Exception: {str(e)}")

def test_set_compute_mode():
    """Test 7.2: Set Compute Mode"""
    try:
        headers = {"Compute-Mode": "cpu"}
        response = make_request("POST", "/config/compute", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "compute_mode" in data:
                test_results.add_result("Set Compute Mode", True, f"Mode set to: {data['compute_mode']}")
            else:
                test_results.add_result("Set Compute Mode", False, "Missing compute_mode in response")
        else:
            test_results.add_result("Set Compute Mode", False, f"HTTP {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Set Compute Mode", False, f"Exception: {str(e)}")

def test_invalid_api_key():
    """Test 8.1: Invalid API Key"""
    try:
        headers = {"Key": "invalid-key"}
        response = make_request("GET", "/queue", headers=headers)
        
        if response.status_code == 401:
            test_results.add_result("Invalid API Key", True, "Correctly rejected invalid key")
        else:
            test_results.add_result("Invalid API Key", False, f"Expected 401, got {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Invalid API Key", False, f"Exception: {str(e)}")

def test_gemini_key_from_env():
    """Test 8.2: Gemini API Key from Environment"""
    try:
        # Test that Gemini models endpoint works with environment variable
        response = make_request("GET", "/models/gemini")
        
        if response.status_code == 200:
            test_results.add_result("Gemini Key from Env", True, "Environment API key working correctly")
        elif response.status_code == 400:
            test_results.add_result("Gemini Key from Env", False, "GEMINI_API_KEY not configured in environment")
        else:
            test_results.add_result("Gemini Key from Env", False, f"Unexpected status {response.status_code}")
            
    except Exception as e:
        test_results.add_result("Gemini Key from Env", False, f"Exception: {str(e)}")

def main():
    """Run comprehensive API tests"""
    print("🧠 COMPREHENSIVE API TEST SUITE - Document OCR LLM API")
    print("="*80)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🔑 API Key: {API_KEY}")
    print(f"🌟 Gemini Key: {GEMINI_API_KEY[:20]}...")
    print(f"📄 Test File: {TEST_PDF_FILE}")
    print("="*80)
    
    # Check if test file exists
    if not os.path.exists(TEST_PDF_FILE):
        print(f"❌ Test file not found: {TEST_PDF_FILE}")
        print("Please ensure the test PDF file is in the current directory.")
        sys.exit(1)
    
    print("\n📊 1. STATUS & INFORMATION")
    print("-" * 40)
    test_health_check()
    test_api_info()
    
    print("\n🤖 2. MODEL MANAGEMENT")
    print("-" * 40)
    test_list_ollama_models()
    test_list_gemini_models()
    
    print("\n📤 3. SMART UPLOAD (MULTI-PROVIDER)")
    print("-" * 40)
    test_upload_ollama()
    
    # Wait a bit for processing
    print("\n⏳ Waiting 5 seconds for processing...")
    time.sleep(5)
    
    test_upload_gemini()
    
    print("\n📋 4. MONITOR PROCESSING")
    print("-" * 40)
    test_queue_status()
    test_queue_status_debug()
    
    print("\n📄 5. GET RESULTS")
    print("-" * 40)
    test_get_document_response()
    test_get_document_response_debug()
    
    print("\n🔧 6. DEBUG & DIAGNOSTICS")
    print("-" * 40)
    test_debug_document()
    
    print("\n⚙️ 7. COMPUTE CONFIGURATION")
    print("-" * 40)
    test_get_compute_mode()
    test_set_compute_mode()
    
    print("\n❌ 8. ERROR TESTING")
    print("-" * 40)
    test_invalid_api_key()
    test_gemini_key_from_env()
    
    # Print final results
    test_results.print_summary()
    
    # Save detailed results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"test_results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "summary": {
                "total_tests": test_results.total_tests,
                "passed_tests": test_results.passed_tests,
                "failed_tests": test_results.failed_tests,
                "success_rate": test_results.passed_tests/test_results.total_tests*100
            },
            "test_configuration": {
                "base_url": BASE_URL,
                "api_key": API_KEY,
                "gemini_api_key": GEMINI_API_KEY[:20] + "...",
                "test_file": TEST_PDF_FILE,
                "ollama_model": ollama_model,
                "gemini_model": gemini_model
            },
            "results": test_results.results
        }, f, indent=2)
    
    print(f"📁 Results saved to: {results_file}")
    
    # Exit with appropriate code
    if test_results.failed_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 