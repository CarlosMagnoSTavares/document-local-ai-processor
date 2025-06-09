#!/usr/bin/env python3
"""
Script de correção para problemas de extração de texto
Este script identifica documentos com status COMPLETED mas sem texto extraído
e tenta reprocessá-los.
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Adicionar o diretório atual ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_consistency():
    """Verifica inconsistências no banco de dados"""
    print("🔍 Verificando consistência do banco de dados...")
    
    try:
        conn = sqlite3.connect('documents.db')
        cursor = conn.cursor()
        
        # Buscar documentos com status COMPLETED mas sem texto extraído
        cursor.execute("""
            SELECT id, filename, status, extracted_text, file_path, file_type
            FROM documents 
            WHERE status = 'COMPLETED' 
            AND (extracted_text IS NULL OR extracted_text = '' OR extracted_text = 'Texto ainda não extraído')
        """)
        
        problematic_docs = cursor.fetchall()
        
        if problematic_docs:
            print(f"❌ ENCONTRADOS {len(problematic_docs)} DOCUMENTOS COM PROBLEMAS:")
            for doc in problematic_docs:
                doc_id, filename, status, extracted_text, file_path, file_type = doc
                print(f"  - ID: {doc_id}, Arquivo: {filename}, Status: {status}")
                print(f"    Texto extraído: '{extracted_text}'")
                print(f"    Caminho: {file_path}")
                print(f"    Tipo: {file_type}")
                print()
        else:
            print("✅ Nenhum documento com problemas encontrado")
        
        # Verificar documentos em processamento há muito tempo
        cursor.execute("""
            SELECT id, filename, status, created_at, updated_at
            FROM documents 
            WHERE status IN ('UPLOADED', 'TEXT_EXTRACTED', 'PROMPT_PROCESSED')
            AND datetime(created_at) < datetime('now', '-1 hour')
        """)
        
        stuck_docs = cursor.fetchall()
        
        if stuck_docs:
            print(f"⚠️ ENCONTRADOS {len(stuck_docs)} DOCUMENTOS PRESOS NO PROCESSAMENTO:")
            for doc in stuck_docs:
                doc_id, filename, status, created_at, updated_at = doc
                print(f"  - ID: {doc_id}, Arquivo: {filename}, Status: {status}")
                print(f"    Criado: {created_at}, Atualizado: {updated_at}")
                print()
        
        conn.close()
        return problematic_docs, stuck_docs
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco de dados: {e}")
        return [], []

def test_file_extraction():
    """Testa extração de arquivos existentes"""
    print("🧪 Testando extração de arquivos...")
    
    try:
        from utils import extract_text_from_file
        
        # Verificar diretório de uploads
        upload_dir = "uploads"
        if not os.path.exists(upload_dir):
            print(f"❌ Diretório de uploads não encontrado: {upload_dir}")
            return
        
        files = os.listdir(upload_dir)
        if not files:
            print("ℹ️ Nenhum arquivo encontrado no diretório de uploads")
            return
        
        print(f"📁 Encontrados {len(files)} arquivos no diretório uploads:")
        
        for file in files[:3]:  # Testar apenas os primeiros 3 arquivos
            file_path = os.path.join(upload_dir, file)
            file_ext = file.split('.')[-1].lower() if '.' in file else 'unknown'
            
            print(f"\n🔍 Testando: {file}")
            print(f"   Tipo: {file_ext}")
            print(f"   Tamanho: {os.path.getsize(file_path)} bytes")
            
            try:
                extracted_text = extract_text_from_file(file_path, file_ext)
                print(f"   ✅ Extração bem-sucedida: {len(extracted_text)} caracteres")
                if extracted_text:
                    print(f"   📄 Preview: {extracted_text[:100]}...")
                else:
                    print("   ⚠️ Texto extraído está vazio")
            except Exception as e:
                print(f"   ❌ Erro na extração: {e}")
    
    except ImportError as e:
        print(f"❌ Erro ao importar módulos: {e}")
        print("   Certifique-se de que todas as dependências estão instaladas")
    except Exception as e:
        print(f"❌ Erro no teste de extração: {e}")

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    print("🔧 Verificando dependências...")
    
    dependencies = [
        ('PIL', 'Pillow'),
        ('pytesseract', 'pytesseract'),
        ('PyPDF2', 'PyPDF2'),
        ('docx', 'python-docx'),
        ('openpyxl', 'openpyxl'),
    ]
    
    missing_deps = []
    
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - NÃO INSTALADO")
            missing_deps.append(package)
    
    if missing_deps:
        print(f"\n❌ Dependências faltando: {', '.join(missing_deps)}")
        print("   Execute: pip install " + " ".join(missing_deps))
    else:
        print("✅ Todas as dependências estão instaladas")
    
    # Verificar tesseract especificamente
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("   ✅ Tesseract OCR está funcionando")
    except Exception as e:
        print(f"   ❌ Problema com Tesseract OCR: {e}")
        print("   Instale o Tesseract: https://github.com/tesseract-ocr/tesseract")

def fix_problematic_documents():
    """Tenta corrigir documentos problemáticos"""
    print("🔧 Tentando corrigir documentos problemáticos...")
    
    try:
        conn = sqlite3.connect('documents.db')
        cursor = conn.cursor()
        
        # Buscar documentos problemáticos
        cursor.execute("""
            SELECT id, filename, file_path, file_type
            FROM documents 
            WHERE status = 'COMPLETED' 
            AND (extracted_text IS NULL OR extracted_text = '' OR extracted_text = 'Texto ainda não extraído')
        """)
        
        problematic_docs = cursor.fetchall()
        
        if not problematic_docs:
            print("✅ Nenhum documento problemático encontrado")
            conn.close()
            return
        
        from utils import extract_text_from_file
        
        fixed_count = 0
        
        for doc in problematic_docs:
            doc_id, filename, file_path, file_type = doc
            
            print(f"\n🔧 Corrigindo documento ID {doc_id}: {filename}")
            
            if not file_path or not os.path.exists(file_path):
                print(f"   ❌ Arquivo não encontrado: {file_path}")
                continue
            
            try:
                # Tentar extrair texto novamente
                extracted_text = extract_text_from_file(file_path, file_type)
                
                if extracted_text and extracted_text.strip():
                    # Atualizar no banco de dados
                    cursor.execute("""
                        UPDATE documents 
                        SET extracted_text = ?, updated_at = ?
                        WHERE id = ?
                    """, (extracted_text, datetime.utcnow().isoformat(), doc_id))
                    
                    conn.commit()
                    fixed_count += 1
                    
                    print(f"   ✅ Corrigido! Extraídos {len(extracted_text)} caracteres")
                    print(f"   📄 Preview: {extracted_text[:100]}...")
                else:
                    print(f"   ⚠️ Extração retornou texto vazio")
                    
            except Exception as e:
                print(f"   ❌ Erro na correção: {e}")
        
        conn.close()
        
        if fixed_count > 0:
            print(f"\n🎉 {fixed_count} documentos corrigidos com sucesso!")
        else:
            print("\n⚠️ Nenhum documento pôde ser corrigido")
            
    except Exception as e:
        print(f"❌ Erro ao corrigir documentos: {e}")

def main():
    """Função principal"""
    print("=" * 60)
    print("🔧 SCRIPT DE CORREÇÃO - PROBLEMAS DE EXTRAÇÃO DE TEXTO")
    print("=" * 60)
    print()
    
    # 1. Verificar dependências
    check_dependencies()
    print()
    
    # 2. Verificar consistência do banco
    problematic_docs, stuck_docs = check_database_consistency()
    print()
    
    # 3. Testar extração de arquivos
    test_file_extraction()
    print()
    
    # 4. Tentar corrigir documentos problemáticos
    if problematic_docs:
        response = input("🤔 Deseja tentar corrigir os documentos problemáticos? (s/n): ")
        if response.lower() in ['s', 'sim', 'y', 'yes']:
            fix_problematic_documents()
    
    print("\n" + "=" * 60)
    print("✅ DIAGNÓSTICO COMPLETO")
    print("=" * 60)

if __name__ == "__main__":
    main() 