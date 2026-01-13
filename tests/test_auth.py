"""
Testes para o módulo de autenticação
"""
import pytest
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.auth import PasswordManager, AuthManager
from src.core.database import DatabaseManager
from config.config import APP_DATA_DIR


class TestPasswordManager:
    \"\"\"Testes para gerenciador de senhas\"\"\"

    def test_hash_password(self):
        \"\"\"Testa hash de senha\"\"\"
        password = \"test_password_123\"
        hashed = PasswordManager.hash_password(password)

        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password

    def test_verify_password(self):
        \"\"\"Testa verificação de senha\"\"\"
        password = \"test_password_123\"
        hashed = PasswordManager.hash_password(password)

        assert PasswordManager.verify_password(password, hashed) is True
        assert PasswordManager.verify_password(\"wrong_password\", hashed) is False

    def test_password_consistency(self):
        \"\"\"Testa consistência de hash\"\"\"
        password = \"test_password_123\"
        hash1 = PasswordManager.hash_password(password)
        hash2 = PasswordManager.hash_password(password)

        assert hash1 == hash2


class TestAuthManager:
    \"\"\"Testes para gerenciador de autenticação\"\"\"

    @pytest.fixture
    def db_manager(self):
        \"\"\"Cria gerenciador de banco de dados para testes\"\"\"
        db_path = APP_DATA_DIR / \"test_database.db\"
        if db_path.exists():
            db_path.unlink()

        return DatabaseManager(db_path)

    @pytest.fixture
    def auth_manager(self, db_manager):
        \"\"\"Cria gerenciador de autenticação para testes\"\"\"
        return AuthManager(db_manager)

    def test_register_user(self, auth_manager):
        \"\"\"Testa registro de usuário\"\"\"
        result = auth_manager.register_user(
            \"testuser\",
            \"password123\",
            \"test@example.com\"
        )
        assert result is True

    def test_register_user_invalid_username(self, auth_manager):
        \"\"\"Testa registro com nome de usuário inválido\"\"\"
        result = auth_manager.register_user(
            \"ab\",  # Muito curto
            \"password123\",
            \"test@example.com\"
        )
        assert result is False

    def test_register_user_invalid_password(self, auth_manager):
        \"\"\"Testa registro com senha inválida\"\"\"
        result = auth_manager.register_user(
            \"testuser\",
            \"short\",  # Muito curta
            \"test@example.com\"
        )
        assert result is False

    def test_login(self, auth_manager):
        \"\"\"Testa login de usuário\"\"\"
        # Registrar usuário
        auth_manager.register_user(
            \"testuser\",
            \"password123\",
            \"test@example.com\"
        )

        # Fazer login
        result = auth_manager.login(\"testuser\", \"password123\")
        assert result is True
        assert auth_manager.is_logged_in() is True

    def test_login_invalid_password(self, auth_manager):
        \"\"\"Testa login com senha incorreta\"\"\"
        # Registrar usuário
        auth_manager.register_user(
            \"testuser\",
            \"password123\",
            \"test@example.com\"
        )

        # Tentar login com senha errada
        result = auth_manager.login(\"testuser\", \"wrongpassword\")
        assert result is False

    def test_logout(self, auth_manager):
        \"\"\"Testa logout de usuário\"\"\"
        # Registrar e fazer login
        auth_manager.register_user(
            \"testuser\",
            \"password123\",
            \"test@example.com\"
        )
        auth_manager.login(\"testuser\", \"password123\")

        # Fazer logout
        auth_manager.logout()
        assert auth_manager.is_logged_in() is False


if __name__ == \"__main__\":
    pytest.main([__file__, \"-v\"])
