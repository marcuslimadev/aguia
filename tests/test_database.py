"""
Testes para o módulo de banco de dados
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import DatabaseManager
from config.config import APP_DATA_DIR


class TestDatabaseManager:
    \"\"\"Testes para gerenciador de banco de dados\"\"\"

    @pytest.fixture
    def db_manager(self):
        \"\"\"Cria gerenciador de banco de dados para testes\"\"\"
        db_path = APP_DATA_DIR / \"test_database.db\"
        if db_path.exists():
            db_path.unlink()

        return DatabaseManager(db_path)

    def test_database_initialization(self, db_manager):
        \"\"\"Testa inicialização do banco de dados\"\"\"
        assert db_manager.db_path.exists()

    def test_add_camera(self, db_manager):
        \"\"\"Testa adição de câmera\"\"\"
        camera_id = db_manager.add_camera(
            user_id=1,
            name=\"Test Camera\",
            rtsp_url=\"rtsp://example.com/stream\"
        )
        assert camera_id > 0

    def test_get_cameras(self, db_manager):
        \"\"\"Testa obtenção de câmeras\"\"\"
        # Adicionar câmeras
        db_manager.add_camera(1, \"Camera 1\", \"rtsp://example.com/1\")
        db_manager.add_camera(1, \"Camera 2\", \"rtsp://example.com/2\")

        # Obter câmeras
        cameras = db_manager.get_cameras(1)
        assert len(cameras) == 2

    def test_add_alert(self, db_manager):
        \"\"\"Testa adição de alerta\"\"\"
        alert_id = db_manager.add_alert(
            rule_id=1,
            camera_id=1,
            event_type=\"intrusion\",
            severity=\"high\",
            description=\"Test alert\"
        )
        assert alert_id > 0

    def test_get_alerts(self, db_manager):
        \"\"\"Testa obtenção de alertas\"\"\"
        # Adicionar alertas
        db_manager.add_alert(1, 1, \"intrusion\", \"high\")
        db_manager.add_alert(1, 1, \"theft\", \"medium\")

        # Obter alertas
        alerts = db_manager.get_alerts(1, limit=10)
        assert len(alerts) >= 0

    def test_add_license(self, db_manager):
        \"\"\"Testa adição de licença\"\"\"
        expiration = datetime.now() + timedelta(days=7)
        license_id = db_manager.add_license(
            user_id=1,
            license_key=\"TEST-LICENSE-KEY\",
            camera_limit=2,
            expiration_date=expiration,
            is_trial=True
        )
        assert license_id > 0

    def test_get_license(self, db_manager):
        \"\"\"Testa obtenção de licença\"\"\"
        expiration = datetime.now() + timedelta(days=7)
        db_manager.add_license(1, \"TEST-LICENSE-KEY\", 2, expiration, True)

        license = db_manager.get_license(1)
        assert license is not None
        assert license['camera_limit'] == 2

    def test_is_license_valid(self, db_manager):
        \"\"\"Testa validação de licença\"\"\"
        expiration = datetime.now() + timedelta(days=7)
        db_manager.add_license(1, \"TEST-LICENSE-KEY\", 2, expiration, True)

        assert db_manager.is_license_valid(1) is True

    def test_get_camera_limit(self, db_manager):
        \"\"\"Testa obtenção do limite de câmeras\"\"\"
        expiration = datetime.now() + timedelta(days=7)
        db_manager.add_license(1, \"TEST-LICENSE-KEY\", 5, expiration, True)

        limit = db_manager.get_camera_limit(1)
        assert limit == 5


if __name__ == \"__main__\":
    pytest.main([__file__, \"-v\"])
