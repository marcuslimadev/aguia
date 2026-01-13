"""
Gerenciador unificado de licenças (Local + Microsoft Store)
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib
import json
from config.config import (
    TRIAL_DURATION_DAYS,
    FREE_CAMERA_LIMIT,
    PREMIUM_CAMERA_LIMIT_TIER1,
    PREMIUM_CAMERA_LIMIT_TIER2,
    PREMIUM_CAMERA_LIMIT_TIER3,
    IS_STORE_BUILD
)

logger = logging.getLogger(__name__)


class LicenseManager:
    """Gerencia licenças unificando Store e local"""

    def __init__(self, db_manager, use_store: bool = None):
        self.db = db_manager
        self.use_store = use_store if use_store is not None else IS_STORE_BUILD
        self.store_provider = None
        
        # Inicializar Store provider se necessário
        if self.use_store:
            try:
                from src.core.store_licensing import StoreLicenseProvider
                self.store_provider = StoreLicenseProvider(is_store_build=True)
                logger.info("✓ Store licensing ativado")
            except Exception as e:
                logger.warning(f"Store licensing não disponível: {e}, usando local")
                self.use_store = False

    def create_trial_license(self, user_id: int) -> bool:
        """Cria uma licença trial"""
        try:
            from config.config import TRIAL_DURATION_DAYS, TRIAL_CAMERA_LIMIT

            expiration_date = datetime.now() + timedelta(days=TRIAL_DURATION_DAYS)
            license_key = self._generate_license_key(user_id, is_trial=True)

            self.db.add_license(
                user_id=user_id,
                license_key=license_key,
                camera_limit=TRIAL_CAMERA_LIMIT,
                expiration_date=expiration_date,
                is_trial=True
            )

            logger.info(f"Licença trial criada para usuário {user_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar licença trial: {e}")
            return False

    def validate_license(self, user_id: int) -> bool:
        """Valida a licença do usuário (Store ou local)"""
        try:
            # Store licensing tem prioridade
            if self.use_store and self.store_provider:
                return self.store_provider.is_license_valid()
            
            # Fallback para licença local
            license = self.db.get_license(user_id)
            if not license:
                logger.warning(f"Licença não encontrada para usuário {user_id}")
                return False

            if datetime.fromisoformat(license['expiration_date']) < datetime.now():
                logger.warning(f"Licença expirada para usuário {user_id}")
                return False

            logger.info(f"Licença válida para usuário {user_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao validar licença: {e}")
            return False

    def check_camera_limit(self, user_id: int, current_cameras: int) -> bool:
        """Verifica se o usuário pode adicionar mais câmeras"""
        try:
            limit = self.get_camera_limit(user_id)
            
            if current_cameras >= limit:
                logger.warning(
                    f"Limite de câmeras atingido para usuário {user_id}: "
                    f"{current_cameras}/{limit}"
                )
                return False

            logger.info(f"Usuário {user_id} pode adicionar mais câmeras ({current_cameras}/{limit})")
            return True

        except Exception as e:
            logger.error(f"Erro ao verificar limite de câmeras: {e}")
            return False
    
    def get_camera_limit(self, user_id: int) -> int:
        """Obtém limite de câmeras (Store ou local)"""
        try:
            # Store licensing tem prioridade
            if self.use_store and self.store_provider:
                return self.store_provider.get_available_cameras()
            
            # Fallback para limite local
            return self.db.get_camera_limit(user_id)
            
        except Exception as e:
            logger.error(f"Erro ao obter limite de câmeras: {e}")
            return FREE_CAMERA_LIMIT  # Retornar limite free como fallback

    def get_license_info(self, user_id: int) -> Optional[Dict]:
        """Obtém informações da licença (Store ou local)"""
        try:
            # Store licensing
            if self.use_store and self.store_provider:
                return {
                    'source': 'store',
                    'status': self.store_provider.get_license_status(),
                    'camera_limit': self.store_provider.get_available_cameras(),
                    'is_valid': self.store_provider.is_license_valid(),
                    'is_trial': self.store_provider.app_license.get('is_trial', False) if self.store_provider.app_license else True,
                    'expiration_date': self.store_provider.app_license.get('expiration_date') if self.store_provider.app_license else None
                }
            
            # Licença local
            license = self.db.get_license(user_id)
            if not license:
                return None

            expiration = datetime.fromisoformat(license['expiration_date'])
            days_remaining = (expiration - datetime.now()).days

            return {
                'source': 'local',
                'license_key': license['license_key'],
                'camera_limit': license['camera_limit'],
                'expiration_date': license['expiration_date'],
                'days_remaining': max(0, days_remaining),
                'is_trial': bool(license['is_trial']),
                'is_valid': days_remaining > 0,
                'status': 'Trial (Local)' if license['is_trial'] else 'Active (Local)'
            }

        except Exception as e:
            logger.error(f"Erro ao obter informações de licença: {e}")
            return None
    
    def get_upgrade_message(self, user_id: int) -> str:
        """Retorna mensagem de upgrade se necessário"""
        info = self.get_license_info(user_id)
        
        if not info:
            return "Ative uma licença para continuar usando o sistema."
        
        if info.get('is_trial'):
            days = info.get('days_remaining', 0)
            return f"Versão trial ({days} dias restantes). Upgrade para acesso ilimitado."
        
        current_limit = info.get('camera_limit', FREE_CAMERA_LIMIT)
        
        if current_limit <= FREE_CAMERA_LIMIT:
            return "Upgrade para adicionar mais câmeras e recursos premium."
        elif current_limit < PREMIUM_CAMERA_LIMIT_TIER2:
            return f"Plano Tier 1 ({current_limit} câmeras). Upgrade para Tier 2 ({PREMIUM_CAMERA_LIMIT_TIER2} câmeras)."
        elif current_limit < PREMIUM_CAMERA_LIMIT_TIER3:
            return f"Plano Tier 2 ({current_limit} câmeras). Upgrade para Tier 3 ({PREMIUM_CAMERA_LIMIT_TIER3} câmeras)."
        
        return "Plano Enterprise ativo."

    def _generate_license_key(self, user_id: int, is_trial: bool = False) -> str:
        """Gera uma chave de licença"""
        timestamp = datetime.now().isoformat()
        trial_str = "TRIAL" if is_trial else "COMMERCIAL"

        data = f"{user_id}-{timestamp}-{trial_str}"
        hash_obj = hashlib.sha256(data.encode())
        license_key = f"{trial_str}-{hash_obj.hexdigest()[:16].upper()}"

        return license_key

    def verify_license_key(self, license_key: str) -> bool:
        """Verifica se uma chave de licença é válida"""
        try:
            # Verificar formato básico
            if not license_key or len(license_key) < 20:
                return False

            # Aqui você implementaria verificação com servidor de licenças
            # Por enquanto, apenas verificar se existe no banco de dados
            query = "SELECT * FROM licenses WHERE license_key = ?"
            result = self.db.execute_query(query, (license_key,))

            return len(result) > 0

        except Exception as e:
            logger.error(f"Erro ao verificar chave de licença: {e}")
            return False

    def activate_license(self, user_id: int, license_key: str, camera_limit: int) -> bool:
        """Ativa uma licença comercial"""
        try:
            if not self.verify_license_key(license_key):
                logger.warning(f"Chave de licença inválida: {license_key}")
                return False

            # Definir data de expiração (1 ano)
            expiration_date = datetime.now() + timedelta(days=365)

            self.db.add_license(
                user_id=user_id,
                license_key=license_key,
                camera_limit=camera_limit,
                expiration_date=expiration_date,
                is_trial=False
            )

            logger.info(f"Licença ativada para usuário {user_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao ativar licença: {e}")
            return False

    def renew_license(self, user_id: int, duration_months: int = 12) -> bool:
        """Renova uma licença existente"""
        try:
            license = self.db.get_license(user_id)
            if not license:
                logger.warning(f"Licença não encontrada para usuário {user_id}")
                return False

            # Calcular nova data de expiração
            current_expiration = datetime.fromisoformat(license['expiration_date'])
            new_expiration = current_expiration + timedelta(days=duration_months * 30)

            # Atualizar licença
            query = "UPDATE licenses SET expiration_date = ? WHERE user_id = ?"
            self.db.execute_update(query, (new_expiration.isoformat(), user_id))

            logger.info(f"Licença renovada para usuário {user_id}")
            return True

        except Exception as e:
            logger.error(f"Erro ao renovar licença: {e}")
            return False

    def get_license_status(self, user_id: int) -> str:
        """Retorna o status da licença"""
        license_info = self.get_license_info(user_id)

        if not license_info:
            return "No License"

        if not license_info['is_valid']:
            return "Expired"

        if license_info['is_trial']:
            return f"Trial ({license_info['days_remaining']} days)"

        return f"Active ({license_info['days_remaining']} days)"
