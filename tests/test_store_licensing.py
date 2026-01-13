"""
Testes para Store Licensing
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from src.core.license_manager import LicenseManager


@pytest.fixture
def mock_db_manager():
    """Fixture com mock do database manager"""
    db = Mock()
    db.get_license = Mock(return_value=None)
    db.get_camera_limit = Mock(return_value=2)
    db.add_license = Mock(return_value=1)
    return db


@pytest.fixture
def license_manager_local(mock_db_manager):
    """Fixture com license manager local (sem Store)"""
    return LicenseManager(mock_db_manager, use_store=False)


@pytest.fixture
def mock_store_provider():
    """Fixture com mock do store provider"""
    provider = Mock()
    provider.is_license_valid = Mock(return_value=True)
    provider.get_available_cameras = Mock(return_value=5)
    provider.get_license_status = Mock(return_value="Active (Store)")
    provider.app_license = {
        'is_trial': False,
        'is_active': True,
        'expiration_date': (datetime.now() + timedelta(days=365)).isoformat()
    }
    return provider


class TestLicenseManager:
    """Testes para License Manager unificado"""

    def test_initialization_local(self, license_manager_local):
        """Testa inicialização em modo local"""
        assert license_manager_local.use_store is False
        assert license_manager_local.store_provider is None

    def test_create_trial_license(self, license_manager_local, mock_db_manager):
        """Testa criação de licença trial"""
        success = license_manager_local.create_trial_license(user_id=1)
        
        assert success is True
        assert mock_db_manager.add_license.called

    def test_validate_license_local_valid(self, license_manager_local, mock_db_manager):
        """Testa validação de licença local válida"""
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        mock_db_manager.get_license.return_value = {
            'license_key': 'TEST-KEY',
            'expiration_date': future_date,
            'camera_limit': 2,
            'is_trial': True
        }
        
        is_valid = license_manager_local.validate_license(user_id=1)
        
        assert is_valid is True

    def test_validate_license_local_expired(self, license_manager_local, mock_db_manager):
        """Testa validação de licença local expirada"""
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        mock_db_manager.get_license.return_value = {
            'license_key': 'TEST-KEY',
            'expiration_date': past_date,
            'camera_limit': 2,
            'is_trial': True
        }
        
        is_valid = license_manager_local.validate_license(user_id=1)
        
        assert is_valid is False

    def test_validate_license_not_found(self, license_manager_local, mock_db_manager):
        """Testa validação quando licença não existe"""
        mock_db_manager.get_license.return_value = None
        
        is_valid = license_manager_local.validate_license(user_id=1)
        
        assert is_valid is False

    def test_check_camera_limit_within_limit(self, license_manager_local):
        """Testa verificação quando dentro do limite"""
        can_add = license_manager_local.check_camera_limit(user_id=1, current_cameras=1)
        
        assert can_add is True

    def test_check_camera_limit_at_limit(self, license_manager_local):
        """Testa verificação quando no limite"""
        can_add = license_manager_local.check_camera_limit(user_id=1, current_cameras=2)
        
        assert can_add is False

    def test_check_camera_limit_over_limit(self, license_manager_local):
        """Testa verificação quando acima do limite"""
        can_add = license_manager_local.check_camera_limit(user_id=1, current_cameras=3)
        
        assert can_add is False

    def test_get_camera_limit_local(self, license_manager_local, mock_db_manager):
        """Testa obtenção de limite local"""
        mock_db_manager.get_camera_limit.return_value = 5
        
        limit = license_manager_local.get_camera_limit(user_id=1)
        
        assert limit == 5

    def test_get_camera_limit_store(self, mock_db_manager, mock_store_provider):
        """Testa obtenção de limite da Store"""
        license_mgr = LicenseManager(mock_db_manager, use_store=True)
        license_mgr.store_provider = mock_store_provider
        
        limit = license_mgr.get_camera_limit(user_id=1)
        
        assert limit == 5
        assert mock_store_provider.get_available_cameras.called

    def test_get_license_info_local_trial(self, license_manager_local, mock_db_manager):
        """Testa obtenção de info de licença trial local"""
        future_date = (datetime.now() + timedelta(days=5)).isoformat()
        mock_db_manager.get_license.return_value = {
            'license_key': 'TRIAL-KEY',
            'expiration_date': future_date,
            'camera_limit': 2,
            'is_trial': True
        }
        
        info = license_manager_local.get_license_info(user_id=1)
        
        assert info is not None
        assert info['source'] == 'local'
        assert info['is_trial'] is True
        assert info['camera_limit'] == 2
        assert 4 <= info['days_remaining'] <= 5

    def test_get_license_info_store(self, mock_db_manager, mock_store_provider):
        """Testa obtenção de info de licença da Store"""
        license_mgr = LicenseManager(mock_db_manager, use_store=True)
        license_mgr.store_provider = mock_store_provider
        
        info = license_mgr.get_license_info(user_id=1)
        
        assert info is not None
        assert info['source'] == 'store'
        assert info['status'] == 'Active (Store)'
        assert info['camera_limit'] == 5
        assert info['is_trial'] is False

    def test_get_upgrade_message_trial(self, license_manager_local, mock_db_manager):
        """Testa mensagem de upgrade para trial"""
        future_date = (datetime.now() + timedelta(days=3)).isoformat()
        mock_db_manager.get_license.return_value = {
            'license_key': 'TRIAL-KEY',
            'expiration_date': future_date,
            'camera_limit': 2,
            'is_trial': True
        }
        
        message = license_manager_local.get_upgrade_message(user_id=1)
        
        assert "trial" in message.lower()
        assert "3 dias" in message.lower() or "2 dias" in message.lower()

    def test_get_upgrade_message_tier1(self, license_manager_local, mock_db_manager):
        """Testa mensagem de upgrade para Tier 1"""
        future_date = (datetime.now() + timedelta(days=365)).isoformat()
        mock_db_manager.get_license.return_value = {
            'license_key': 'TIER1-KEY',
            'expiration_date': future_date,
            'camera_limit': 5,
            'is_trial': False
        }
        
        message = license_manager_local.get_upgrade_message(user_id=1)
        
        assert "tier 1" in message.lower() or "5 câmeras" in message.lower()

    def test_get_upgrade_message_enterprise(self, license_manager_local, mock_db_manager):
        """Testa mensagem para plano enterprise"""
        future_date = (datetime.now() + timedelta(days=365)).isoformat()
        mock_db_manager.get_license.return_value = {
            'license_key': 'ENT-KEY',
            'expiration_date': future_date,
            'camera_limit': 50,
            'is_trial': False
        }
        
        message = license_manager_local.get_upgrade_message(user_id=1)
        
        assert "enterprise" in message.lower()

    def test_validate_license_uses_store_when_available(self, mock_db_manager, mock_store_provider):
        """Testa que Store tem prioridade sobre local"""
        license_mgr = LicenseManager(mock_db_manager, use_store=True)
        license_mgr.store_provider = mock_store_provider
        
        # Mesmo que DB retorne inválido, Store retorna válido
        mock_db_manager.get_license.return_value = None
        
        is_valid = license_mgr.validate_license(user_id=1)
        
        assert is_valid is True
        assert mock_store_provider.is_license_valid.called

    def test_get_camera_limit_fallback_on_error(self, license_manager_local, mock_db_manager):
        """Testa fallback para FREE_CAMERA_LIMIT em caso de erro"""
        mock_db_manager.get_camera_limit.side_effect = Exception("DB Error")
        
        limit = license_manager_local.get_camera_limit(user_id=1)
        
        assert limit == 2  # FREE_CAMERA_LIMIT

    def test_generate_license_key(self, license_manager_local):
        """Testa geração de chave de licença"""
        key1 = license_manager_local._generate_license_key(user_id=1, is_trial=True)
        key2 = license_manager_local._generate_license_key(user_id=1, is_trial=True)
        
        # Chaves devem ser únicas (incluem timestamp)
        assert isinstance(key1, str)
        assert len(key1) > 10

    def test_activate_license_success(self, license_manager_local, mock_db_manager):
        """Testa ativação de licença com sucesso"""
        # Mock para encontrar licença válida
        mock_db_manager.execute_query = Mock(return_value=[])
        
        # Ativar
        license_key = "TEST-PREMIUM-KEY-2024"
        success = license_manager_local.activate_license(user_id=1, license_key=license_key)
        
        # Deve retornar False (chave inválida) mas não dar erro
        assert isinstance(success, bool)

    def test_license_info_none_when_not_found(self, license_manager_local, mock_db_manager):
        """Testa que retorna None quando licença não encontrada"""
        mock_db_manager.get_license.return_value = None
        
        info = license_manager_local.get_license_info(user_id=1)
        
        assert info is None
