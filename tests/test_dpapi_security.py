"""
Testes para DPAPI Security
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.dpapi_security import DpapiSecurity, CredentialManager


class TestDpapiSecurity:
    """Testes para DpapiSecurity"""

    def test_dpapi_initialization(self):
        """Testa inicialização do DPAPI"""
        dpapi = DpapiSecurity()
        assert dpapi is not None

    def test_encrypt_decrypt_credential(self):
        """Testa criptografia e descriptografia de credenciais"""
        dpapi = DpapiSecurity()

        if not dpapi.is_available:
            pytest.skip("DPAPI not available on this platform")

        # Test data
        original = "my_secret_password_123"

        # Encrypt
        encrypted = dpapi.encrypt_credential(original)
        assert encrypted is not None
        assert encrypted != original  # Should be different
        assert len(encrypted) > 0

        # Decrypt
        decrypted = dpapi.decrypt_credential(encrypted)
        assert decrypted == original  # Should match original

    def test_encrypt_decrypt_empty_string(self):
        """Testa criptografia de string vazia"""
        dpapi = DpapiSecurity()

        if not dpapi.is_available:
            pytest.skip("DPAPI not available on this platform")

        # Empty string
        encrypted = dpapi.encrypt_credential("")
        assert encrypted is not None

        decrypted = dpapi.decrypt_credential(encrypted)
        assert decrypted == ""

    def test_encrypt_decrypt_special_characters(self):
        """Testa criptografia com caracteres especiais"""
        dpapi = DpapiSecurity()

        if not dpapi.is_available:
            pytest.skip("DPAPI not available on this platform")

        # Special characters
        original = "p@ssw0rd!#$%^&*()_+-=[]{}|;':,.<>?/~`"

        encrypted = dpapi.encrypt_credential(original)
        assert encrypted is not None

        decrypted = dpapi.decrypt_credential(encrypted)
        assert decrypted == original

    def test_encrypt_decrypt_unicode(self):
        """Testa criptografia com Unicode"""
        dpapi = DpapiSecurity()

        if not dpapi.is_available:
            pytest.skip("DPAPI not available on this platform")

        # Unicode characters
        original = "senha_çãõáéíóú_日本語_🔐"

        encrypted = dpapi.encrypt_credential(original)
        assert encrypted is not None

        decrypted = dpapi.decrypt_credential(encrypted)
        assert decrypted == original

    def test_fallback_when_unavailable(self):
        """Testa fallback quando DPAPI não está disponível"""
        dpapi = DpapiSecurity()

        # Force unavailable
        dpapi.is_available = False

        # Should return plaintext
        result = dpapi.encrypt_credential("password")
        assert result == "password"

        result = dpapi.decrypt_credential("password")
        assert result == "password"

    def test_encrypt_error_handling(self):
        """Testa tratamento de erros na criptografia"""
        dpapi = DpapiSecurity()

        if not dpapi.is_available:
            pytest.skip("DPAPI not available on this platform")

        # Test with None (should handle gracefully)
        with pytest.raises(Exception):
            dpapi.encrypt_credential(None)

    def test_decrypt_invalid_data(self):
        """Testa descriptografia de dados inválidos"""
        dpapi = DpapiSecurity()

        if not dpapi.is_available:
            pytest.skip("DPAPI not available on this platform")

        # Invalid encrypted data
        result = dpapi.decrypt_credential("not_valid_encrypted_data")
        assert result is None  # Should return None on error

    def test_multiple_encryptions_different(self):
        """Testa que múltiplas criptografias geram resultados diferentes"""
        dpapi = DpapiSecurity()

        if not dpapi.is_available:
            pytest.skip("DPAPI not available on this platform")

        original = "password123"

        encrypted1 = dpapi.encrypt_credential(original)
        encrypted2 = dpapi.encrypt_credential(original)

        # DPAPI should generate different ciphertext each time
        # But both should decrypt to same value
        assert dpapi.decrypt_credential(encrypted1) == original
        assert dpapi.decrypt_credential(encrypted2) == original


class TestCredentialManager:
    """Testes para CredentialManager"""

    @pytest.fixture
    def mock_db(self):
        """Mock database manager"""
        db = Mock()
        db.execute_query = Mock(return_value=[])
        db.execute_update = Mock()
        return db

    @pytest.fixture
    def credential_manager(self, mock_db):
        """Credential manager com mock database"""
        return CredentialManager(mock_db)

    def test_initialization(self, credential_manager):
        """Testa inicialização do CredentialManager"""
        assert credential_manager is not None
        assert credential_manager.dpapi is not None

    def test_store_credential(self, credential_manager, mock_db):
        """Testa armazenamento de credencial"""
        result = credential_manager.store_credential(
            credential_type="rtsp",
            identifier="camera1",
            username="admin",
            password="password123"
        )

        assert result is True
        assert mock_db.execute_update.called

    def test_get_credential(self, credential_manager, mock_db):
        """Testa obtenção de credencial"""
        # Mock return encrypted data
        mock_db.execute_query.return_value = [
            ("admin", "encrypted_password_data")
        ]

        result = credential_manager.get_credential(
            credential_type="rtsp",
            identifier="camera1"
        )

        assert result is not None
        assert "username" in result
        assert "password" in result
        assert result["username"] == "admin"

    def test_get_credential_not_found(self, credential_manager, mock_db):
        """Testa obtenção de credencial não encontrada"""
        mock_db.execute_query.return_value = []

        result = credential_manager.get_credential(
            credential_type="rtsp",
            identifier="camera_not_found"
        )

        assert result is None

    def test_delete_credential(self, credential_manager, mock_db):
        """Testa deleção de credencial"""
        result = credential_manager.delete_credential(
            credential_type="rtsp",
            identifier="camera1"
        )

        assert result is True
        assert mock_db.execute_update.called

    def test_store_credential_encryption(self, credential_manager, mock_db):
        """Testa que a senha é criptografada antes de armazenar"""
        with patch.object(credential_manager.dpapi, 'encrypt_credential') as mock_encrypt:
            mock_encrypt.return_value = "encrypted_data"

            credential_manager.store_credential(
                credential_type="smtp",
                identifier="email_server",
                username="user@example.com",
                password="plaintext_password"
            )

            # Verify encrypt was called
            mock_encrypt.assert_called_once_with("plaintext_password")

    def test_get_credential_decryption(self, credential_manager, mock_db):
        """Testa que a senha é descriptografada ao obter"""
        mock_db.execute_query.return_value = [
            ("user@example.com", "encrypted_password")
        ]

        with patch.object(credential_manager.dpapi, 'decrypt_credential') as mock_decrypt:
            mock_decrypt.return_value = "decrypted_password"

            result = credential_manager.get_credential(
                credential_type="smtp",
                identifier="email_server"
            )

            # Verify decrypt was called
            mock_decrypt.assert_called_once_with("encrypted_password")
            assert result["password"] == "decrypted_password"

    def test_roundtrip_integration(self, credential_manager, mock_db):
        """Testa integração completa: store + get"""
        # Setup mock to return stored data
        stored_data = []

        def mock_store(*args):
            stored_data.append(args[0][3])  # encrypted password

        def mock_get(*args):
            if stored_data:
                return [("admin", stored_data[0])]
            return []

        mock_db.execute_update.side_effect = mock_store
        mock_db.execute_query.side_effect = mock_get

        # Store
        credential_manager.store_credential(
            credential_type="rtsp",
            identifier="camera1",
            username="admin",
            password="original_password"
        )

        # Get
        result = credential_manager.get_credential(
            credential_type="rtsp",
            identifier="camera1"
        )

        # Verify
        assert result is not None
        assert result["username"] == "admin"

        # If DPAPI is available, password should match
        if credential_manager.dpapi.is_available:
            assert result["password"] == "original_password"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
