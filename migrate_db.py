import sqlite3
import os

def migrate_database():
    """Adiciona o campo full_prompt_sent à tabela documents se não existir"""
    
    if not os.path.exists('documents.db'):
        print("Banco de dados não encontrado. Será criado na próxima execução da aplicação.")
        return
    
    conn = sqlite3.connect('documents.db')
    cursor = conn.cursor()
    
    try:
        # Verificar se o campo já existe
        cursor.execute('PRAGMA table_info(documents)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'full_prompt_sent' in column_names:
            print("✅ Campo 'full_prompt_sent' já existe no banco de dados")
        else:
            print("🔄 Adicionando campo 'full_prompt_sent' ao banco de dados...")
            cursor.execute('ALTER TABLE documents ADD COLUMN full_prompt_sent TEXT')
            conn.commit()
            print("✅ Campo 'full_prompt_sent' adicionado com sucesso")
        
        # Verificar quantos documentos existem
        cursor.execute('SELECT COUNT(*) FROM documents')
        count = cursor.fetchone()[0]
        print(f"📊 Total de documentos no banco: {count}")
        
        if count > 0:
            cursor.execute('SELECT id, filename, status FROM documents ORDER BY id DESC LIMIT 5')
            docs = cursor.fetchall()
            print("📋 Últimos 5 documentos:")
            for doc in docs:
                print(f"  - ID: {doc[0]}, Arquivo: {doc[1]}, Status: {doc[2]}")
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 