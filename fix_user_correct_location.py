"""
Fix usuario marcus no banco correto (AppData Local EdgeAI)
"""
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# LOCALIZAÇÃO CORRETA DO BANCO (conforme log da aplicação)
DB_PATH = Path.home() / "AppData" / "Local" / "EdgeAI" / "database.db"

# Certificar que o diretório existe
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Credenciais
USERNAME = "marcus"
PASSWORD = "526341"
SALT = "edge_security_ai_salt_2024"

# Gerar hash PBKDF2
password_hash = hashlib.pbkdf2_hmac('sha256', PASSWORD.encode(), SALT.encode(), 100000).hex()

print(f"Banco: {DB_PATH}")
print(f"Existe: {DB_PATH.exists()}")

# Conectar ao banco
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Criar tabelas se não existirem
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    license_key TEXT UNIQUE NOT NULL,
    camera_limit INTEGER NOT NULL,
    expiration_date TIMESTAMP NOT NULL,
    is_trial BOOLEAN DEFAULT 0,
    activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")

# Verificar se usuario existe
cursor.execute("SELECT id FROM users WHERE username = ?", (USERNAME,))
user = cursor.fetchone()

if user:
    # Atualizar senha
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", 
                   (password_hash, USERNAME))
    user_id = user[0]
    print(f"[OK] Senha atualizada para usuario existente '{USERNAME}'")
else:
    # Criar novo usuario
    cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                   (USERNAME, password_hash, "marcus@aguia.com"))
    user_id = cursor.lastrowid
    print(f"[OK] Usuario '{USERNAME}' criado")
    
    # Criar licença trial
    expiry = datetime.now() + timedelta(days=7)
    license_key = f"TRIAL-{USERNAME.upper()}-{datetime.now().strftime('%Y%m%d')}"
    cursor.execute("""
        INSERT INTO licenses (user_id, license_key, camera_limit, expiration_date, is_trial)
        VALUES (?, ?, 2, ?, 1)
    """, (user_id, license_key, expiry))
    print("[OK] Licenca trial criada (7 dias, 2 cameras)")

conn.commit()
conn.close()

print(f"\n[OK] Senha do usuario '{USERNAME}' resetada para: {PASSWORD}")
print("Voce pode fazer login agora!")
