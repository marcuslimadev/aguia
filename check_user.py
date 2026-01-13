"""
Script para verificar e gerenciar usuarios do banco de dados
"""
import os
import sqlite3
from pathlib import Path

# Caminho do banco de dados
if os.name == 'nt':  # Windows
    db_path = Path("C:/ProgramData/EdgeAI/database.db")
else:
    db_path = Path.home() / ".edgeai" / "database.db"

# Tentar path alternativo se nao encontrar
if not db_path.exists():
    db_path = Path(os.path.expanduser("~")) / "AppData" / "Local" / "EdgeAI" / "database.db"

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
    
    # Verificar se usuario 'marcus' existe
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = 'marcus'")
    marcus = cursor.fetchone()
    
    if marcus:
        print(f"\n[ENCONTRADO] Usuario 'marcus' existe (ID: {marcus[0]})")
        print(f"Hash armazenado: {marcus[2][:50]}...")
        
        # Testar hash da senha '526341'
        import hashlib
        salt = "edge_security_ai_salt_2024"
        test_hash = hashlib.pbkdf2_hmac(
            'sha256',
            '526341'.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        print(f"Hash esperado:   {test_hash[:50]}...")
        
        if test_hash == marcus[2]:
            print("[OK] Senha '526341' esta correta!")
        else:
            print("[ERRO] Hash nao corresponde. Senha pode ter sido alterada.")
            
            # Oferecer reset de senha
            resposta = input("\nDeseja resetar senha para '526341'? (sim/nao): ").strip().lower()
            if resposta == "sim":
                cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'marcus'", (test_hash,))
                conn.commit()
                print("[OK] Senha resetada com sucesso!")
    else:
        print("\n[NAO ENCONTRADO] Usuario 'marcus' nao existe.")
        print("Voce precisa criar a conta pelo sistema.")
    
    conn.close()
else:
    print(f"Banco de dados nao encontrado em: {db_path}")
    print("Execute o aplicativo primeiro para criar o banco.\n")
