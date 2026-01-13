"""Script rapido para resetar senha do usuario marcus"""
import sqlite3
import hashlib
from pathlib import Path
import os

# Encontrar banco
paths = [
    Path("C:/ProgramData/EdgeAI/database.db"),
    Path(os.path.expanduser("~")) / "AppData" / "Local" / "EdgeAI" / "database.db"
]

db_path = None
for p in paths:
    if p.exists():
        db_path = p
        break

if not db_path:
    print("ERRO: Banco nao encontrado!")
    exit(1)

print(f"Banco: {db_path}")

# Conectar
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Calcular hash correto
salt = "edge_security_ai_salt_2024"
password_hash = hashlib.pbkdf2_hmac(
    'sha256',
    '526341'.encode('utf-8'),
    salt.encode('utf-8'),
    100000
).hex()

# Verificar se usuario existe
cursor.execute("SELECT id, username FROM users WHERE username = 'marcus'")
user = cursor.fetchone()

if user:
    # Atualizar senha
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'marcus'", (password_hash,))
    conn.commit()
    print(f"\n[OK] Senha do usuario 'marcus' resetada para: 526341")
    print("Voce pode fazer login agora!")
else:
    # Criar usuario
    cursor.execute("""
        INSERT INTO users (username, password_hash, email, created_at)
        VALUES ('marcus', ?, '', datetime('now'))
    """, (password_hash,))
    user_id = cursor.lastrowid
    
    # Criar licenca trial
    from datetime import datetime, timedelta
    expiry = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        INSERT INTO licenses (user_id, license_key, license_type, camera_limit, expires_at, is_active, created_at)
        VALUES (?, 'TRIAL-MARCUS', 'trial', 2, ?, 1, datetime('now'))
    """, (user_id, expiry))
    
    conn.commit()
    print(f"\n[OK] Usuario 'marcus' criado!")
    print("Usuario: marcus")
    print("Senha: 526341")
    print("Trial: 7 dias, 2 cameras")

conn.close()
