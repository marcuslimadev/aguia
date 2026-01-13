"""
Modulo de autenticacao e gerenciamento de usuarios
"""
import hashlib
import logging
import secrets
import smtplib
from typing import Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class PasswordManager:
    """Gerencia senhas com hash seguro"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Gera hash seguro da senha"""
        salt = "edge_security_ai_salt_2024"
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verifica se a senha corresponde ao hash"""
        return PasswordManager.hash_password(password) == password_hash


class AuthManager:
    """Gerencia autenticacao de usuarios"""

    def __init__(self, db_manager, app_settings=None):
        self.db = db_manager
        self.app_settings = app_settings
        self.current_user = None
        self.session_timeout = 3600  # 1 hora
        self.last_error = None
        self.last_registered_user_id = None

    def register_user(self, username: str, password: str, email: str = None) -> bool:
        """Registra um novo usuario"""
        try:
            self.last_error = None
            if not username or len(username) < 3:
                logger.warning("Nome de usuario invalido")
                self.last_error = "Invalid username"
                return False

            if not password or len(password) < 6:
                logger.warning("Senha muito curta")
                self.last_error = "Password too short"
                return False

            if not email or '@' not in email:
                logger.warning("Email invalido")
                self.last_error = "Invalid email"
                return False

            check_query = "SELECT id FROM users WHERE username = ?"
            existing = self.db.execute_query(check_query, (username,))
            if existing:
                logger.warning(f"Usuario ja existe: {username}")
                raise ValueError(f"Usuario '{username}' ja esta cadastrado")

            password_hash = PasswordManager.hash_password(password)
            require_verification = self._require_email_verification()
            smtp_config = self._get_smtp_config() if self.app_settings else None
            if require_verification and not smtp_config:
                self.last_error = "SMTP not configured"
                return False

            query = """
                INSERT INTO users (username, password_hash, email, email_verified)
                VALUES (?, ?, ?, ?)
            """
            user_id = self.db.execute_update(
                query,
                (username, password_hash, email, 0 if require_verification else 1)
            )
            logger.info(f"Usuario registrado: {username}")
            self.last_registered_user_id = user_id

            self._create_trial_license(user_id)

            if smtp_config:
                self.db.set_email_settings(
                    user_id=user_id,
                    smtp_server=smtp_config["server"],
                    smtp_port=smtp_config["port"],
                    sender_email=smtp_config["from_address"],
                    sender_password=smtp_config["password"],
                    recipient_emails=email
                )

            if require_verification:
                if not self.send_verification_code(email):
                    self.last_error = self.last_error or "Failed to send verification email"
                    return False

            return True

        except ValueError as ve:
            logger.error(f"Validacao falhou: {ve}")
            self.last_error = str(ve)
            raise
        except Exception as e:
            logger.error(f"Erro ao registrar usuario: {e}")
            self.last_error = "Registration failed"
            return False

    def login(self, username: str, password: str) -> bool:
        """Autentica um usuario"""
        try:
            self.last_error = None
            query = "SELECT * FROM users WHERE username = ?"
            result = self.db.execute_query(query, (username,))

            if not result:
                logger.warning(f"Usuario nao encontrado: {username}")
                self.last_error = "User not found"
                return False

            user = result[0]
            if not PasswordManager.verify_password(password, user['password_hash']):
                logger.warning(f"Senha incorreta para usuario: {username}")
                self.last_error = "Invalid password"
                return False

            email_verified = user['email_verified'] if 'email_verified' in user.keys() else 1
            if email_verified == 0 and self._require_email_verification():
                logger.warning(f"Email nao verificado para usuario: {username}")
                self.last_error = "Email not verified"
                return False

            if not self.db.is_license_valid(user['id']):
                logger.warning(f"Licenca expirada para usuario: {username}")
                self.last_error = "License expired"
                return False

            self.current_user = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'login_time': datetime.now()
            }
            logger.info(f"Usuario autenticado: {username}")
            return True

        except Exception as e:
            logger.error(f"Erro ao fazer login: {e}")
            self.last_error = "Login failed"
            return False

    def logout(self):
        """Faz logout do usuario"""
        if self.current_user:
            logger.info(f"Usuario desconectado: {self.current_user['username']}")
            self.current_user = None

    def is_logged_in(self) -> bool:
        """Verifica se ha usuario autenticado"""
        if not self.current_user:
            return False

        elapsed = (datetime.now() - self.current_user['login_time']).total_seconds()
        if elapsed > self.session_timeout:
            self.logout()
            return False

        return True

    def get_current_user(self) -> Optional[dict]:
        """Retorna o usuario atual"""
        if self.is_logged_in():
            return self.current_user
        return None

    def get_user_id(self) -> Optional[int]:
        """Retorna o ID do usuario atual"""
        user = self.get_current_user()
        return user['id'] if user else None

    def get_last_error(self) -> Optional[str]:
        """Retorna a ultima mensagem de erro"""
        return self.last_error

    def get_email_for_username(self, username: str) -> Optional[str]:
        """Obtém email associado ao username"""
        query = "SELECT email FROM users WHERE username = ?"
        result = self.db.execute_query(query, (username,))
        if result:
            return result[0]["email"]
        return None

    def send_verification_code(self, email: str) -> bool:
        """Gera e envia codigo de verificacao"""
        user = self.db.get_user_by_email(email)
        if not user:
            self.last_error = "Email not found"
            return False

        email_verified = user['email_verified'] if 'email_verified' in user.keys() else 1
        if email_verified == 1:
            self.last_error = "Email already verified"
            return False

        smtp_config = self._get_smtp_config()
        if not smtp_config:
            self.last_error = "SMTP not configured"
            return False

        code = f"{secrets.randbelow(1000000):06d}"
        code_hash = self._hash_code(code)
        expires_at = datetime.now() + timedelta(minutes=self._get_verification_ttl())

        self.db.add_email_verification(user['id'], code_hash, expires_at)
        if not self._send_verification_email(smtp_config, email, code):
            self.last_error = "Failed to send verification email"
            return False

        return True

    def verify_email_code(self, email: str, code: str) -> bool:
        """Valida codigo de verificacao"""
        user = self.db.get_user_by_email(email)
        if not user:
            self.last_error = "Email not found"
            return False

        record = self.db.get_latest_email_verification(user['id'])
        if not record:
            self.last_error = "No verification code found"
            return False

        expires_at = record['expires_at']
        if isinstance(expires_at, datetime):
            expiry = expires_at
        elif expires_at:
            expiry = datetime.fromisoformat(expires_at)
        else:
            expiry = None

        if expiry and expiry < datetime.now():
            self.last_error = "Verification code expired"
            return False

        if self._hash_code(code) != record['code_hash']:
            self.last_error = "Invalid verification code"
            return False

        self.db.set_user_verified(user['id'])
        return True

    def _create_trial_license(self, user_id: int):
        """Cria uma licenca trial para novo usuario"""
        try:
            from config.config import TRIAL_DURATION_DAYS, TRIAL_CAMERA_LIMIT
            expiration_date = datetime.now() + timedelta(days=TRIAL_DURATION_DAYS)
            license_key = f"TRIAL-{user_id}-{datetime.now().timestamp()}"

            self.db.add_license(
                user_id=user_id,
                license_key=license_key,
                camera_limit=TRIAL_CAMERA_LIMIT,
                expiration_date=expiration_date,
                is_trial=True
            )
            logger.info(f"Licenca trial criada para usuario {user_id}")
        except Exception as e:
            logger.error(f"Erro ao criar licenca trial: {e}")

    def change_password(self, current_password: str, new_password: str) -> bool:
        """Altera a senha do usuario"""
        try:
            if not self.is_logged_in():
                logger.warning("Usuario nao autenticado")
                return False

            user_id = self.current_user['id']
            query = "SELECT password_hash FROM users WHERE id = ?"
            result = self.db.execute_query(query, (user_id,))

            if not result:
                return False

            user = result[0]
            if not PasswordManager.verify_password(current_password, user['password_hash']):
                logger.warning("Senha atual incorreta")
                return False

            if len(new_password) < 6:
                logger.warning("Nova senha muito curta")
                return False

            new_hash = PasswordManager.hash_password(new_password)
            query = "UPDATE users SET password_hash = ? WHERE id = ?"
            self.db.execute_update(query, (new_hash, user_id))

            logger.info(f"Senha alterada para usuario {user_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao alterar senha: {e}")
            return False

    def reset_password(self, email: str, new_password: str) -> bool:
        """Reseta a senha do usuario (requer validacao de email)"""
        try:
            query = "SELECT id FROM users WHERE email = ?"
            result = self.db.execute_query(query, (email,))

            if not result:
                logger.warning(f"Email nao encontrado: {email}")
                return False

            user_id = result[0]['id']
            new_hash = PasswordManager.hash_password(new_password)
            query = "UPDATE users SET password_hash = ? WHERE id = ?"
            self.db.execute_update(query, (new_hash, user_id))

            logger.info(f"Senha resetada para email: {email}")
            return True

        except Exception as e:
            logger.error(f"Erro ao resetar senha: {e}")
            return False

    def _get_smtp_config(self) -> Optional[dict]:
        if not self.app_settings:
            return None

        server = self.app_settings.get("smtp_server", "")
        username = self.app_settings.get("smtp_username", "")
        password = self.app_settings.get("smtp_password", "")
        from_address = self.app_settings.get("smtp_from", "")
        port = int(self.app_settings.get("smtp_port", 587))
        use_tls = bool(self.app_settings.get("smtp_use_tls", True))

        if not server or not username or not password or not from_address:
            return None

        return {
            "server": server,
            "port": port,
            "username": username,
            "password": password,
            "from_address": from_address,
            "use_tls": use_tls
        }

    def _send_verification_email(self, smtp_config: dict, recipient: str, code: str) -> bool:
        try:
            msg = MIMEText(
                f"Your verification code is: {code}\\n\\n"
                f"This code expires in {self._get_verification_ttl()} minutes.",
                "plain",
                "utf-8"
            )
            msg["Subject"] = "Email verification code"
            msg["From"] = smtp_config["from_address"]
            msg["To"] = recipient

            if smtp_config.get("use_tls"):
                with smtplib.SMTP(smtp_config["server"], smtp_config["port"], timeout=10) as server:
                    server.starttls()
                    server.login(smtp_config["username"], smtp_config["password"])
                    server.sendmail(smtp_config["from_address"], [recipient], msg.as_string())
            else:
                with smtplib.SMTP_SSL(smtp_config["server"], smtp_config["port"], timeout=10) as server:
                    server.login(smtp_config["username"], smtp_config["password"])
                    server.sendmail(smtp_config["from_address"], [recipient], msg.as_string())
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar email de verificacao: {e}")
            return False

    def _hash_code(self, code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def _require_email_verification(self) -> bool:
        if self.app_settings is None:
            return False
        return bool(self.app_settings.get("require_email_verification", True))

    def _get_verification_ttl(self) -> int:
        try:
            from config.config import EMAIL_VERIFICATION_TTL_MINUTES
            return EMAIL_VERIFICATION_TTL_MINUTES
        except Exception:
            return 15
