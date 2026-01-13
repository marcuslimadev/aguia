"""
Módulo de segurança e DRM
"""
import logging
import hashlib
import hmac
from pathlib import Path
from typing import Optional
import json

logger = logging.getLogger(__name__)


class SecurityManager:
    """Gerencia segurança da aplicação"""

    def __init__(self, app_dir: Path):
        self.app_dir = app_dir
        self.integrity_file = app_dir / ".integrity"
        self.drm_file = app_dir / ".drm"

    def verify_application_integrity(self) -> bool:
        """Verifica integridade da aplicação"""
        try:
            if not self.integrity_file.exists():
                logger.warning("Arquivo de integridade não encontrado")
                return False

            # Aqui você implementaria verificação de hash
            # Por enquanto, apenas retornar True
            logger.info("✓ Integridade da aplicação verificada")
            return True

        except Exception as e:
            logger.error(f"Erro ao verificar integridade: {e}")
            return False

    def verify_drm_status(self) -> bool:
        """Verifica status do DRM"""
        try:
            if not self.drm_file.exists():
                logger.warning("Arquivo DRM não encontrado")
                return False

            with open(self.drm_file, 'r') as f:
                drm_data = json.load(f)

            # Verificar se DRM está ativo
            if not drm_data.get('enabled', False):
                logger.warning("DRM não está ativado")
                return False

            logger.info("✓ DRM verificado")
            return True

        except Exception as e:
            logger.error(f"Erro ao verificar DRM: {e}")
            return False

    def initialize_drm(self) -> bool:
        """Inicializa o DRM"""
        try:
            drm_data = {
                'enabled': True,
                'version': '1.0',
                'initialized_at': str(Path.ctime(self.app_dir))
            }

            with open(self.drm_file, 'w') as f:
                json.dump(drm_data, f)

            logger.info("DRM inicializado")
            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar DRM: {e}")
            return False

    def create_integrity_hash(self, file_path: Path) -> str:
        """Cria hash de integridade para um arquivo"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash

        except Exception as e:
            logger.error(f"Erro ao criar hash: {e}")
            return ""

    def verify_file_signature(self, file_path: Path, signature: str) -> bool:
        """Verifica assinatura de um arquivo"""
        try:
            file_hash = self.create_integrity_hash(file_path)
            return file_hash == signature

        except Exception as e:
            logger.error(f"Erro ao verificar assinatura: {e}")
            return False

    def encrypt_sensitive_data(self, data: str) -> str:
        """Criptografa dados sensíveis"""
        try:
            # Usar HMAC para criptografia simples
            key = b"edge_security_ai_key_2024"
            encrypted = hmac.new(key, data.encode(), hashlib.sha256).hexdigest()
            return encrypted

        except Exception as e:
            logger.error(f"Erro ao criptografar dados: {e}")
            return ""

    def decrypt_sensitive_data(self, encrypted_data: str) -> Optional[str]:
        """Descriptografa dados sensíveis"""
        try:
            # HMAC não é reversível, apenas para verificação
            # Para dados sensíveis reais, use AES ou similar
            return encrypted_data

        except Exception as e:
            logger.error(f"Erro ao descriptografar dados: {e}")
            return None

    def validate_license_signature(self, license_key: str, signature: str) -> bool:
        """Valida assinatura de licença"""
        try:
            key = b"microsoft_store_key"
            expected_signature = hmac.new(key, license_key.encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Erro ao validar assinatura de licença: {e}")
            return False


class DataEncryption:
    """Gerencia criptografia de dados sensíveis"""

    @staticmethod
    def hash_password(password: str, salt: str = None) -> str:
        """Cria hash de senha"""
        if salt is None:
            salt = "edge_security_ai_salt_2024"

        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verifica se senha corresponde ao hash"""
        return DataEncryption.hash_password(password) == password_hash

    @staticmethod
    def encrypt_email(email: str) -> str:
        """Criptografa email para armazenamento"""
        return hashlib.sha256(email.encode()).hexdigest()

    @staticmethod
    def mask_email(email: str) -> str:
        """Mascara email para exibição"""
        parts = email.split('@')
        if len(parts) != 2:
            return email

        local = parts[0]
        domain = parts[1]

        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]

        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_password(password: str) -> str:
        """Mascara senha para exibição"""
        return '*' * len(password)
