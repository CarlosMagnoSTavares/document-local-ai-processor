#!/usr/bin/env python3
"""
Script para corrigir os problemas identificados pelo debug:
1. Adicionar campo full_prompt_sent se não existir
2. Corrigir documentos existentes onde extracted_text está vazio
"""

import sqlite3
import os
import sys

def fix_database():
    """Corrige problemas no banco de dados"""
    
    db_path = 'documents.db'
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 Verificando estrutura do banco...")
        
        # Verificar se o campo full_prompt_sent existe
        cursor.execute('PRAGMA table_info(documents)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Adicionar campo full_prompt_sent se não existir
        if 'full_prompt_sent' not in column_names:
            print("🔧 Adicionando campo full_prompt_sent...")
            cursor.execute('ALTER TABLE documents ADD COLUMN full_prompt_sent TEXT')
            conn.commit()
            print("✅ Campo full_prompt_sent adicionado")
        else:
            print("✅ Campo full_prompt_sent já existe")
        
        # Verificar documentos com extracted_text vazio
        cursor.execute("""
            SELECT id, filename, status, extracted_text, file_path 
            FROM documents 
            WHERE status = 'COMPLETED' AND (extracted_text IS NULL OR extracted_text = '')
        """)
        
        empty_docs = cursor.fetchall()
        print(f"📊 Encontrados {len(empty_docs)} documentos com extracted_text vazio")
        
        # Para cada documento com texto vazio, tentar reextrair
        fixed_count = 0
        for doc in empty_docs:
            doc_id, filename, status, extracted_text, file_path = doc
            print(f"🔧 Tentando corrigir documento ID {doc_id}: {filename}")
            
            # Tentar extrair o texto novamente
            try:
                # Importar as funções de extração
                sys.path.append('/app')
                from utils import extract_text_from_file
                
                if file_path and os.path.exists(file_path):
                    # Determinar tipo do arquivo
                    file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
                    
                    # Extrair texto
                    new_extracted_text = extract_text_from_file(file_path, file_extension)
                    
                    if new_extracted_text and new_extracted_text.strip():
                        # Atualizar no banco
                        cursor.execute(
                            "UPDATE documents SET extracted_text = ? WHERE id = ?",
                            (new_extracted_text, doc_id)
                        )
                        conn.commit()
                        print(f"✅ Documento {doc_id} corrigido - {len(new_extracted_text)} caracteres extraídos")
                        fixed_count += 1
                    else:
                        print(f"⚠️ Documento {doc_id} - Não foi possível extrair texto")
                else:
                    print(f"⚠️ Documento {doc_id} - Arquivo não encontrado: {file_path}")
                    
            except Exception as e:
                print(f"❌ Erro ao processar documento {doc_id}: {e}")
        
        print(f"\n📈 Resumo:")
        print(f"   - Documentos processados: {len(empty_docs)}")
        print(f"   - Documentos corrigidos: {fixed_count}")
        
        # Verificar documentos que ainda têm full_prompt_sent vazio
        cursor.execute("""
            SELECT COUNT(*) FROM documents 
            WHERE status = 'COMPLETED' AND (full_prompt_sent IS NULL OR full_prompt_sent = '')
        """)
        empty_prompts = cursor.fetchone()[0]
        
        if empty_prompts > 0:
            print(f"⚠️ {empty_prompts} documentos têm full_prompt_sent vazio")
            print("   Isso será corrigido automaticamente em novos processamentos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a correção: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando correção dos problemas identificados pelo debug...")
    success = fix_database()
    
    if success:
        print("✅ Correção concluída com sucesso!")
    else:
        print("❌ Falha na correção")
        sys.exit(1) 