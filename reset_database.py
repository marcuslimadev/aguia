"""
Script para resetar banco de dados de testes
"""
import os
import sqlite3
from pathlib import Path

# Caminho do banco de dados
if os.name == 'nt':  # Windows
    db_path = Path("C:/ProgramData/EdgeAI/database.db")
else:
    db_path = Path.home() / ".edgeai" / "database.db"

if db_path.exists():
    print(f"Banco encontrado: {db_path}")
    
    # Conectar e listar usuarios
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n=== USUARIOS CADASTRADOS ===")
    cursor.execute("SELECT id, username, email, created_at FROM users")
    users = cursor.fetchall()
    
    if users:
        for user in users:
            print(f"ID: {user[0]} | Usuario: {user[1]} | Email: {user[2]} | Criado: {user[3]}")
    else:
        print("Nenhum usuario encontrado.")
    
    print("\n" + "="*50)
    resposta = input("\nDeseja DELETAR TODOS os usuarios? (sim/nao): ").strip().lower()
    
    if resposta == "sim":
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM licenses")
        cursor.execute("DELETE FROM cameras")
        cursor.execute("DELETE FROM alerts")
        cursor.execute("DELETE FROM alert_history")
        conn.commit()
        print("\n[OK] Banco de dados resetado com sucesso!")
        print("Todos os usuarios, cameras e alertas foram removidos.\n")
    else:
        print("\n[CANCELADO] Nenhuma alteracao foi feita.\n")
    
    conn.close()
else:
    print(f"Banco de dados nao encontrado em: {db_path}")
    print("Execute o aplicativo primeiro para criar o banco.\n")
