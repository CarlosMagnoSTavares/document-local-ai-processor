import sqlite3

# Verificar estrutura da tabela
conn = sqlite3.connect('documents.db')
cursor = conn.cursor()

print("=== Estrutura da tabela documents ===")
cursor.execute('PRAGMA table_info(documents)')
columns = cursor.fetchall()
for row in columns:
    print(f"- {row[1]} ({row[2]})")

print("\n=== Dados do documento 10 ===")
cursor.execute("SELECT * FROM documents WHERE id = 10")
doc = cursor.fetchone()
if doc:
    # Pegar os nomes das colunas
    column_names = [description[0] for description in cursor.description]
    print("Colunas disponíveis:")
    for i, name in enumerate(column_names):
        print(f"  {name}: {doc[i]}")
else:
    print("Documento 10 não encontrado")

conn.close() 