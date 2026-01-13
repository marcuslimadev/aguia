"""
Gerenciador de banco de dados SQLite
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerencia todas as operações de banco de dados"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection = None
        self.init_database()

    def connect(self):
        """Conecta ao banco de dados"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Conectado ao banco de dados: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def disconnect(self):
        """Desconecta do banco de dados"""
        if self.connection:
            self.connection.close()
            logger.info("Desconectado do banco de dados")

    def init_database(self):
        """Inicializa o esquema do banco de dados"""
        self.connect()
        cursor = self.connection.cursor()

        # Tabela de Usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._ensure_column("users", "email_verified", "BOOLEAN DEFAULT 1")

        # Tabela de Câmeras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                rtsp_url TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Tabela de Zonas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                zone_type TEXT NOT NULL,
                coordinates TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (camera_id) REFERENCES cameras(id)
            )
        """)

        # Tabela de Regras
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                action TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (zone_id) REFERENCES zones(id)
            )
        """)

        # Tabela de Alertas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                camera_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                snapshot_path TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT 0,
                FOREIGN KEY (rule_id) REFERENCES rules(id),
                FOREIGN KEY (camera_id) REFERENCES cameras(id)
            )
        """)

        # Tabela de Configurações de Email
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                smtp_server TEXT NOT NULL,
                smtp_port INTEGER NOT NULL,
                sender_email TEXT NOT NULL,
                sender_password TEXT NOT NULL,
                recipient_emails TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Tabela de Licenças
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                license_key TEXT UNIQUE NOT NULL,
                camera_limit INTEGER NOT NULL,
                expiration_date TIMESTAMP NOT NULL,
                is_trial BOOLEAN DEFAULT 0,
                activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Tabela de Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela de Verificação de Email
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_verification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                verified BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Tabela de Eventos Temporais
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id INTEGER NOT NULL,
                zone_id INTEGER,
                event_type TEXT NOT NULL,
                track_id INTEGER NOT NULL,
                confidence REAL NOT NULL,
                severity TEXT NOT NULL,
                metadata TEXT,
                evidence_frames TEXT,
                validated BOOLEAN DEFAULT 0,
                validator_score REAL DEFAULT 0.0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (camera_id) REFERENCES cameras(id),
                FOREIGN KEY (zone_id) REFERENCES zones(id)
            )
        """)

        # Tabela de Feedback do Usuário
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                is_real BOOLEAN NOT NULL,
                event_type TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events(id)
            )
        """)

        # Tabela de Fila de Email
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                attachment_path TEXT,
                attempts INTEGER DEFAULT 0,
                next_retry_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP,
                error_message TEXT
            )
        """)
        # Tabela de verificação de email
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # Tabela de Credenciais Criptografadas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credential_type TEXT NOT NULL,
                identifier TEXT NOT NULL,
                username TEXT NOT NULL,
                password_encrypted TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(credential_type, identifier)
            )
        """)
        self.connection.commit()
        logger.info("Banco de dados inicializado com sucesso")

    def _ensure_column(self, table: str, column: str, definition: str):
        """Adiciona coluna caso não exista."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table})")
            existing = [row[1] for row in cursor.fetchall()]
            if column not in existing:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                self.connection.commit()
        except sqlite3.Error as e:
            logger.error(f"Erro ao adicionar coluna {column} em {table}: {e}")

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Executa uma query SELECT"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Erro ao executar query: {e}")
            raise

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Executa uma query INSERT/UPDATE/DELETE"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Erro ao executar update: {e}")
            self.connection.rollback()
            raise

    # Operações de Câmeras
    def add_camera(self, user_id: int, name: str, rtsp_url: str) -> int:
        """Adiciona uma nova câmera"""
        query = """
            INSERT INTO cameras (user_id, name, rtsp_url)
            VALUES (?, ?, ?)
        """
        return self.execute_update(query, (user_id, name, rtsp_url))

    def get_cameras(self, user_id: int) -> List[sqlite3.Row]:
        """Obtém todas as câmeras do usuário"""
        query = "SELECT * FROM cameras WHERE user_id = ? AND enabled = 1"
        return self.execute_query(query, (user_id,))

    def get_camera(self, camera_id: int) -> Optional[sqlite3.Row]:
        """Obtém uma câmera específica"""
        query = "SELECT * FROM cameras WHERE id = ?"
        result = self.execute_query(query, (camera_id,))
        return result[0] if result else None


    # Operacoes de Usuarios
    def get_user_by_email(self, email: str) -> Optional[sqlite3.Row]:
        """Obtem usuario pelo email"""
        query = "SELECT * FROM users WHERE email = ?"
        result = self.execute_query(query, (email,))
        return result[0] if result else None

    def set_user_verified(self, user_id: int):
        """Marca email do usuario como verificado"""
        query = "UPDATE users SET email_verified = 1 WHERE id = ?"
        self.execute_update(query, (user_id,))

    def add_email_verification(self, user_id: int, code_hash: str, expires_at: datetime):
        """Registra um codigo de verificacao"""
        query = """
            INSERT INTO email_verifications (user_id, code_hash, expires_at)
            VALUES (?, ?, ?)
        """
        self.execute_update(query, (user_id, code_hash, expires_at))

    def get_latest_email_verification(self, user_id: int) -> Optional[sqlite3.Row]:
        """Obtem o ultimo codigo de verificacao"""
        query = """
            SELECT * FROM email_verifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def update_camera(self, camera_id: int, name: str = None, rtsp_url: str = None):
        """Atualiza uma câmera"""
        updates = []
        params = []
        if name:
            updates.append("name = ?")
            params.append(name)
        if rtsp_url:
            updates.append("rtsp_url = ?")
            params.append(rtsp_url)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(camera_id)
            query = f"UPDATE cameras SET {', '.join(updates)} WHERE id = ?"
            self.execute_update(query, tuple(params))

    def delete_camera(self, camera_id: int):
        """Deleta uma câmera"""
        query = "UPDATE cameras SET enabled = 0 WHERE id = ?"
        self.execute_update(query, (camera_id,))

    # Operações de Alertas
    def add_alert(self, rule_id: int, camera_id: int, event_type: str,
                  severity: str, description: str = None, snapshot_path: str = None) -> int:
        """Adiciona um novo alerta"""
        query = """
            INSERT INTO alerts (rule_id, camera_id, event_type, severity, description, snapshot_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (rule_id, camera_id, event_type, severity, description, snapshot_path))

    def get_alerts(self, user_id: int, limit: int = 100) -> List[sqlite3.Row]:
        """Obtém alertas do usuário"""
        query = """
            SELECT a.* FROM alerts a
            JOIN rules r ON a.rule_id = r.id
            JOIN zones z ON r.zone_id = z.id
            JOIN cameras c ON z.camera_id = c.id
            WHERE c.user_id = ?
            ORDER BY a.timestamp DESC
            LIMIT ?
        """
        return self.execute_query(query, (user_id, limit))

    def acknowledge_alert(self, alert_id: int):
        """Marca um alerta como reconhecido"""
        query = "UPDATE alerts SET acknowledged = 1 WHERE id = ?"
        self.execute_update(query, (alert_id,))

    # Operações de Licenças
    def add_license(self, user_id: int, license_key: str, camera_limit: int,
                    expiration_date: datetime, is_trial: bool = False) -> int:
        """Adiciona uma licença"""
        query = """
            INSERT INTO licenses (user_id, license_key, camera_limit, expiration_date, is_trial)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (user_id, license_key, camera_limit, expiration_date, is_trial))

    def get_license(self, user_id: int) -> Optional[sqlite3.Row]:
        """Obtém a licença ativa do usuário"""
        query = """
            SELECT * FROM licenses
            WHERE user_id = ? AND expiration_date > CURRENT_TIMESTAMP
            ORDER BY expiration_date DESC
            LIMIT 1
        """
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def is_license_valid(self, user_id: int) -> bool:
        """Verifica se a licença do usuário é válida"""
        license = self.get_license(user_id)
        return license is not None

    def get_camera_limit(self, user_id: int) -> int:
        """Obtém o limite de câmeras do usuário"""
        license = self.get_license(user_id)
        return license['camera_limit'] if license else 0

    # Operações de Configurações de Email
    def set_email_settings(self, user_id: int, smtp_server: str, smtp_port: int,
                          sender_email: str, sender_password: str, recipient_emails: str):
        """Define as configurações de email"""
        query = """
            INSERT OR REPLACE INTO email_settings
            (user_id, smtp_server, smtp_port, sender_email, sender_password, recipient_emails)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self.execute_update(query, (user_id, smtp_server, smtp_port, sender_email, sender_password, recipient_emails))

    def get_email_settings(self, user_id: int) -> Optional[sqlite3.Row]:
        """Obtém as configurações de email do usuário"""
        query = "SELECT * FROM email_settings WHERE user_id = ? AND enabled = 1"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def log_event(self, level: str, message: str):
        """Registra um evento no log"""
        query = "INSERT INTO logs (level, message) VALUES (?, ?)"
        self.execute_update(query, (level, message))

    # Operações de Eventos Temporais
    def add_event(self, camera_id: int, zone_id: Optional[int], event_type: str,
                  track_id: int, confidence: float, severity: str,
                  metadata: str = None, evidence_frames: str = None) -> int:
        """Adiciona um evento temporal"""
        query = """
            INSERT INTO events
            (camera_id, zone_id, event_type, track_id, confidence, severity, metadata, evidence_frames)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_update(query, (
            camera_id, zone_id, event_type, track_id, confidence,
            severity, metadata, evidence_frames
        ))

    def get_events(self, camera_id: Optional[int] = None,
                   event_type: Optional[str] = None,
                   validated_only: bool = False,
                   limit: int = 100) -> List[sqlite3.Row]:
        """Obtém eventos temporais"""
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if camera_id is not None:
            query += " AND camera_id = ?"
            params.append(camera_id)

        if event_type is not None:
            query += " AND event_type = ?"
            params.append(event_type)

        if validated_only:
            query += " AND validated = 1"

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        return self.execute_query(query, tuple(params))

    def update_event_validation(self, event_id: int, validator_score: float):
        """Atualiza validação de um evento"""
        query = """
            UPDATE events
            SET validated = 1, validator_score = ?
            WHERE id = ?
        """
        self.execute_update(query, (validator_score, event_id))

    def get_recent_events_by_type(self, camera_id: int, event_type: str,
                                   minutes: int = 5) -> List[sqlite3.Row]:
        """Obtém eventos recentes por tipo (para cooldown)"""
        query = """
            SELECT * FROM events
            WHERE camera_id = ?
            AND event_type = ?
            AND timestamp > datetime('now', ?)
            ORDER BY timestamp DESC
        """
        offset = f'-{minutes} minutes'
        return self.execute_query(query, (camera_id, event_type, offset))

    # Operações de Feedback do Usuário
    def add_user_feedback(self, event_id: int, is_real: bool, event_type: str,
                          notes: Optional[str] = None) -> int:
        """Adiciona feedback do usuário sobre um evento"""
        query = """
            INSERT INTO user_feedback (event_id, is_real, event_type, notes)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_update(query, (event_id, is_real, event_type, notes))

    def get_feedback_stats(self, event_type: str) -> Optional[Dict]:
        """Obtém estatísticas de feedback por tipo de evento"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_real = 1 THEN 1 ELSE 0 END) as true_positives,
                SUM(CASE WHEN is_real = 0 THEN 1 ELSE 0 END) as false_positives
            FROM user_feedback
            WHERE event_type = ?
        """
        result = self.execute_query(query, (event_type,))
        
        if result and result[0]:
            row = result[0]
            total = row[0] or 0
            tp = row[1] or 0
            fp = row[2] or 0
            
            return {
                'total': total,
                'true_positives': tp,
                'false_positives': fp,
                'false_positive_rate': fp / total if total > 0 else 0.0
            }
        
        return None
    # Email Verification Methods
    def create_email_verification(self, user_id: int, email: str, code: str) -> int:
        """Cria código de verificação para email"""
        from datetime import datetime, timedelta
        from config.config import EMAIL_VERIFICATION_TTL_MINUTES
        
        expires_at = datetime.now() + timedelta(minutes=EMAIL_VERIFICATION_TTL_MINUTES)
        
        query = """
            INSERT INTO email_verification (user_id, email, code, expires_at)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_update(query, (user_id, email, code, expires_at))
    
    def verify_email_code(self, user_id: int, code: str) -> bool:
        """Verifica código de email e atualiza email do usuário se válido"""
        from datetime import datetime
        
        # Buscar código válido não expirado
        query = """
            SELECT id, email FROM email_verification
            WHERE user_id = ? AND code = ? AND verified = 0
            AND expires_at > ?
            ORDER BY created_at DESC LIMIT 1
        """
        result = self.execute_query(query, (user_id, code, datetime.now()))
        
        if not result:
            return False
        
        verification_id, new_email = result[0][0], result[0][1]
        
        # Marcar como verificado
        update_query = """
            UPDATE email_verification SET verified = 1
            WHERE id = ?
        """
        self.execute_update(update_query, (verification_id,))
        
        # Atualizar email do usuário
        user_query = """
            UPDATE users SET email = ?, email_verified = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        self.execute_update(user_query, (new_email, user_id))
        
        return True
    
    def get_user_email(self, user_id: int) -> Optional[str]:
        """Retorna email do usuário"""
        query = "SELECT email FROM users WHERE id = ?"
        result = self.execute_query(query, (user_id,))
        return result[0][0] if result else None
    
    def update_user_profile(self, user_id: int, **kwargs) -> bool:
        """Atualiza dados do perfil do usuário (exceto email que precisa verificação)"""
        allowed_fields = ['username']  # Adicionar outros campos conforme necessário
        
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        try:
            self.execute_update(query, tuple(values))
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False