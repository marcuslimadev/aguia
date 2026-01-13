"""
Criptografia DPAPI para credenciais sensíveis
"""
import logging
import base64
from typing import Optional
import os

logger = logging.getLogger(__name__)


class DpapiSecurity:
    """Gerenciador de criptografia DPAPI para Windows"""

    def __init__(self):
        """Inicializa gerenciador DPAPI"""
        self.is_available = self._check_dpapi_availability()

    def _check_dpapi_availability(self) -> bool:
        """Verifica se DPAPI está disponível"""
        try:
            import ctypes
            from ctypes import wintypes

            # Tentar importar funções DPAPI
            crypt32 = ctypes.windll.crypt32
            self.crypt32 = crypt32
            self.wintypes = wintypes

            logger.info("✓ DPAPI disponível")
            return True

        except (ImportError, AttributeError, OSError):
            logger.warning("DPAPI não disponível (não é Windows ou não tem permissões)")
            return False

    def encrypt_credential(self, credential: str, entropy: Optional[str] = None) -> Optional[str]:
        """
        Criptografa credencial usando DPAPI

        Args:
            credential: Credencial a criptografar
            entropy: Entropia adicional (opcional)

        Returns:
            Credencial criptografada em base64 ou None
        """
        if not self.is_available:
            logger.warning("DPAPI não disponível, retornando credencial em plaintext")
            return credential

        try:
            import ctypes
            from ctypes import wintypes

            # Preparar dados
            data_bytes = credential.encode('utf-8')

            # Estrutura DATA_BLOB
            class DataBlob(ctypes.Structure):
                _fields_ = [
                    ('cbData', wintypes.DWORD),
                    ('pbData', ctypes.POINTER(wintypes.BYTE))
                ]

            # Criar blob de entrada
            input_blob = DataBlob()
            input_blob.cbData = len(data_bytes)
            input_blob.pbData = ctypes.cast(
                ctypes.create_string_buffer(data_bytes),
                ctypes.POINTER(wintypes.BYTE)
            )

            # Criar blob de saída
            output_blob = DataBlob()

            # Chamar CryptProtectData
            result = self.crypt32.CryptProtectData(
                ctypes.byref(input_blob),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(output_blob)
            )

            if not result:
                logger.error("Erro ao criptografar com DPAPI")
                return None

            # Converter para base64
            encrypted_bytes = ctypes.string_at(
                output_blob.pbData,
                output_blob.cbData
            )

            encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')

            logger.debug("✓ Credencial criptografada com DPAPI")
            return encrypted_b64

        except Exception as e:
            logger.error(f"Erro ao criptografar credencial: {e}")
            return None

    def decrypt_credential(self, encrypted_credential: str) -> Optional[str]:
        """
        Descriptografa credencial usando DPAPI

        Args:
            encrypted_credential: Credencial criptografada em base64

        Returns:
            Credencial descriptografada ou None
        """
        if not self.is_available:
            logger.warning("DPAPI não disponível, retornando credencial como está")
            return encrypted_credential

        try:
            import ctypes
            from ctypes import wintypes

            # Decodificar base64
            encrypted_bytes = base64.b64decode(encrypted_credential)

            # Estrutura DATA_BLOB
            class DataBlob(ctypes.Structure):
                _fields_ = [
                    ('cbData', wintypes.DWORD),
                    ('pbData', ctypes.POINTER(wintypes.BYTE))
                ]

            # Criar blob de entrada
            input_blob = DataBlob()
            input_blob.cbData = len(encrypted_bytes)
            input_blob.pbData = ctypes.cast(
                ctypes.create_string_buffer(encrypted_bytes),
                ctypes.POINTER(wintypes.BYTE)
            )

            # Criar blob de saída
            output_blob = DataBlob()

            # Chamar CryptUnprotectData
            result = self.crypt32.CryptUnprotectData(
                ctypes.byref(input_blob),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(output_blob)
            )

            if not result:
                logger.error("Erro ao descriptografar com DPAPI")
                return None

            # Converter para string
            decrypted_bytes = ctypes.string_at(
                output_blob.pbData,
                output_blob.cbData
            )

            decrypted_str = decrypted_bytes.decode('utf-8')

            logger.debug("✓ Credencial descriptografada com DPAPI")
            return decrypted_str

        except Exception as e:
            logger.error(f"Erro ao descriptografar credencial: {e}")
            return None

    def encrypt_file(self, file_path: str) -> bool:
        """
        Criptografa arquivo usando DPAPI

        Args:
            file_path: Caminho do arquivo

        Returns:
            True se sucesso
        """
        if not self.is_available:
            logger.warning("DPAPI não disponível")
            return False

        try:
            import ctypes
            from ctypes import wintypes

            # Ler arquivo
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Estrutura DATA_BLOB
            class DataBlob(ctypes.Structure):
                _fields_ = [
                    ('cbData', wintypes.DWORD),
                    ('pbData', ctypes.POINTER(wintypes.BYTE))
                ]

            # Criar blob de entrada
            input_blob = DataBlob()
            input_blob.cbData = len(file_data)
            input_blob.pbData = ctypes.cast(
                ctypes.create_string_buffer(file_data),
                ctypes.POINTER(wintypes.BYTE)
            )

            # Criar blob de saída
            output_blob = DataBlob()

            # Chamar CryptProtectData
            result = self.crypt32.CryptProtectData(
                ctypes.byref(input_blob),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(output_blob)
            )

            if not result:
                logger.error(f"Erro ao criptografar arquivo: {file_path}")
                return False

            # Escrever arquivo criptografado
            encrypted_data = ctypes.string_at(
                output_blob.pbData,
                output_blob.cbData
            )

            with open(file_path, 'wb') as f:
                f.write(encrypted_data)

            logger.info(f"✓ Arquivo criptografado: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao criptografar arquivo: {e}")
            return False

    def decrypt_file(self, file_path: str) -> bool:
        """
        Descriptografa arquivo usando DPAPI

        Args:
            file_path: Caminho do arquivo

        Returns:
            True se sucesso
        """
        if not self.is_available:
            logger.warning("DPAPI não disponível")
            return False

        try:
            import ctypes
            from ctypes import wintypes

            # Ler arquivo
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()

            # Estrutura DATA_BLOB
            class DataBlob(ctypes.Structure):
                _fields_ = [
                    ('cbData', wintypes.DWORD),
                    ('pbData', ctypes.POINTER(wintypes.BYTE))
                ]

            # Criar blob de entrada
            input_blob = DataBlob()
            input_blob.cbData = len(encrypted_data)
            input_blob.pbData = ctypes.cast(
                ctypes.create_string_buffer(encrypted_data),
                ctypes.POINTER(wintypes.BYTE)
            )

            # Criar blob de saída
            output_blob = DataBlob()

            # Chamar CryptUnprotectData
            result = self.crypt32.CryptUnprotectData(
                ctypes.byref(input_blob),
                None,
                None,
                None,
                None,
                0,
                ctypes.byref(output_blob)
            )

            if not result:
                logger.error(f"Erro ao descriptografar arquivo: {file_path}")
                return False

            # Escrever arquivo descriptografado
            decrypted_data = ctypes.string_at(
                output_blob.pbData,
                output_blob.cbData
            )

            with open(file_path, 'wb') as f:
                f.write(decrypted_data)

            logger.info(f"✓ Arquivo descriptografado: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao descriptografar arquivo: {e}")
            return False


class CredentialManager:
    """Gerenciador de credenciais com DPAPI"""

    def __init__(self, db_manager):
        """
        Inicializa gerenciador de credenciais

        Args:
            db_manager: Gerenciador de banco de dados
        """
        self.db = db_manager
        self.dpapi = DpapiSecurity()

    def store_credential(
        self,
        credential_type: str,
        identifier: str,
        username: str,
        password: str
    ) -> bool:
        """
        Armazena credencial criptografada

        Args:
            credential_type: Tipo (rtsp, smtp, etc)
            identifier: Identificador (URL, hostname, etc)
            username: Usuário
            password: Senha

        Returns:
            True se sucesso
        """
        try:
            # Criptografar senha
            encrypted_password = self.dpapi.encrypt_credential(password)

            if not encrypted_password:
                encrypted_password = password  # Fallback

            # Armazenar no banco
            query = """
                INSERT OR REPLACE INTO credentials
                (credential_type, identifier, username, password_encrypted, created_at)
                VALUES (?, ?, ?, ?, ?)
            """

            from datetime import datetime

            self.db.execute_update(
                query,
                (
                    credential_type,
                    identifier,
                    username,
                    encrypted_password,
                    datetime.now().isoformat()
                )
            )

            logger.info(f"✓ Credencial armazenada: {credential_type}/{identifier}")
            return True

        except Exception as e:
            logger.error(f"Erro ao armazenar credencial: {e}")
            return False

    def get_credential(
        self,
        credential_type: str,
        identifier: str
    ) -> Optional[dict]:
        """
        Obtém credencial descriptografada

        Args:
            credential_type: Tipo
            identifier: Identificador

        Returns:
            Dicionário com username/password ou None
        """
        try:
            query = """
                SELECT username, password_encrypted
                FROM credentials
                WHERE credential_type = ? AND identifier = ?
            """

            result = self.db.execute_query(query, (credential_type, identifier))

            if not result:
                return None

            username, encrypted_password = result[0]

            # Descriptografar senha
            password = self.dpapi.decrypt_credential(encrypted_password)

            if not password:
                password = encrypted_password  # Fallback

            return {
                'username': username,
                'password': password
            }

        except Exception as e:
            logger.error(f"Erro ao obter credencial: {e}")
            return None

    def delete_credential(self, credential_type: str, identifier: str) -> bool:
        """Deleta credencial"""
        try:
            query = """
                DELETE FROM credentials
                WHERE credential_type = ? AND identifier = ?
            """

            self.db.execute_update(query, (credential_type, identifier))

            logger.info(f"✓ Credencial deletada: {credential_type}/{identifier}")
            return True

        except Exception as e:
            logger.error(f"Erro ao deletar credencial: {e}")
            return False
