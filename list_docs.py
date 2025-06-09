import sqlite3

conn = sqlite3.connect('documents.db')
cursor = conn.cursor()

cursor.execute('SELECT id, filename, status FROM documents ORDER BY id')
docs = cursor.fetchall()

print('Documentos existentes:')
for row in docs:
    print(f'ID: {row[0]}, Arquivo: {row[1]}, Status: {row[2]}')

conn.close() 