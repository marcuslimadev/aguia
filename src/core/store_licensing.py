"""
Provedor de licenças da Microsoft Store com Windows.Services.Store
"""
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class StoreLicenseProvider:
    """Provedor de licenças integrado com Microsoft Store"""

    # Add-on IDs para diferentes pacotes de câmeras
    ADDON_IDS = {
        '2_cameras_1month': 'EdgeAI-2Cam-1M',
        '2_cameras_3months': 'EdgeAI-2Cam-3M',
        '2_cameras_12months': 'EdgeAI-2Cam-12M',
        '5_cameras_1month': 'EdgeAI-5Cam-1M',
        '5_cameras_3months': 'EdgeAI-5Cam-3M',
        '5_cameras_12months': 'EdgeAI-5Cam-12M',
        '10_cameras_1month': 'EdgeAI-10Cam-1M',
        '10_cameras_3months': 'EdgeAI-10Cam-3M',
        '10_cameras_12months': 'EdgeAI-10Cam-12M',
    }

    def __init__(self, is_store_build: bool = False):
        """
        Inicializa provedor de licenças

        Args:
            is_store_build: True se rodando como MSIX da Store
        """
        self.is_store_build = is_store_build
        self.store_context = None
        self.app_license = None
        self.addon_licenses = {}

        if is_store_build:
            self._initialize_store_context()

    def _initialize_store_context(self):
        """Inicializa contexto da Store"""
        try:
            from winsdk.windows.services.store import StoreContext

            logger.info("Inicializando StoreContext...")
            self.store_context = StoreContext.get_default()

            if self.store_context is None:
                logger.warning("StoreContext não disponível (não é MSIX da Store)")
                self.is_store_build = False

        except ImportError:
            logger.warning(
                "winsdk não instalado. Use: pip install winsdk\n"
                "Para desenvolvimento, use fallback local."
            )
            self.is_store_build = False

        except Exception as e:
            logger.error(f"Erro ao inicializar StoreContext: {e}")
            self.is_store_build = False

    async def get_app_license(self) -> Optional[Dict]:
        """
        Obtém licença do aplicativo

        Returns:
            Dicionário com informações de licença ou None
        """
        if not self.is_store_build or self.store_context is None:
            return self._get_trial_license()

        try:
            app_license = await self.store_context.get_app_license_async()

            if app_license is None:
                logger.warning("Licença do app não encontrada")
                return self._get_trial_license()

            license_info = {
                'is_trial': app_license.is_trial,
                'is_active': app_license.is_active,
                'expiration_date': app_license.expiration_date.isoformat() if app_license.expiration_date else None,
                'type': 'trial' if app_license.is_trial else 'full'
            }

            logger.info(f"Licença do app obtida: {license_info['type']}")
            self.app_license = license_info
            return license_info

        except Exception as e:
            logger.error(f"Erro ao obter licença do app: {e}")
            return self._get_trial_license()

    async def get_addon_licenses(self) -> Dict[str, Dict]:
        """
        Obtém licenças de add-ons (pacotes de câmeras)

        Returns:
            Dicionário com informações de add-ons
        """
        if not self.is_store_build or self.store_context is None:
            return self._get_trial_addons()

        try:
            addon_licenses = {}

            for addon_key, addon_id in self.ADDON_IDS.items():
                try:
                    addon_license = await self.store_context.get_addon_license_async(addon_id)

                    if addon_license and addon_license.is_active:
                        addon_info = {
                            'addon_id': addon_id,
                            'is_active': addon_license.is_active,
                            'expiration_date': addon_license.expiration_date.isoformat() if addon_license.expiration_date else None,
                            'cameras': self._parse_camera_count(addon_key),
                            'duration_months': self._parse_duration(addon_key)
                        }
                        addon_licenses[addon_key] = addon_info

                except Exception as e:
                    logger.debug(f"Add-on {addon_id} não disponível: {e}")

            logger.info(f"Add-ons obtidos: {len(addon_licenses)}")
            self.addon_licenses = addon_licenses
            return addon_licenses

        except Exception as e:
            logger.error(f"Erro ao obter licenças de add-ons: {e}")
            return self._get_trial_addons()

    def get_available_cameras(self) -> int:
        """
        Calcula número de câmeras disponíveis

        Returns:
            Número de câmeras permitidas
        """
        if not self.is_store_build:
            return 2  # Trial local

        # Somar câmeras de todos os add-ons ativos
        total_cameras = 0

        for addon_info in self.addon_licenses.values():
            if addon_info.get('is_active'):
                total_cameras += addon_info.get('cameras', 0)

        # Mínimo 2 para trial
        return max(total_cameras, 2)

    def is_license_valid(self) -> bool:
        """Verifica se licença é válida"""
        if not self.is_store_build:
            return True  # Trial sempre válido

        if self.app_license is None:
            return False

        return self.app_license.get('is_active', False)

    def get_license_status(self) -> str:
        """Retorna status legível da licença"""
        if not self.is_store_build:
            return "Trial (Local)"

        if not self.is_license_valid():
            return "Expired"

        if self.app_license.get('is_trial'):
            return "Trial (Store)"

        return "Active (Store)"

    def _get_trial_license(self) -> Dict:
        """Retorna licença trial padrão"""
        expiration = datetime.now() + timedelta(days=7)

        return {
            'is_trial': True,
            'is_active': True,
            'expiration_date': expiration.isoformat(),
            'type': 'trial'
        }

    def _get_trial_addons(self) -> Dict:
        """Retorna add-ons trial padrão"""
        expiration = datetime.now() + timedelta(days=7)

        return {
            '2_cameras_1month': {
                'addon_id': self.ADDON_IDS['2_cameras_1month'],
                'is_active': True,
                'expiration_date': expiration.isoformat(),
                'cameras': 2,
                'duration_months': 1
            }
        }

    @staticmethod
    def _parse_camera_count(addon_key: str) -> int:
        """Extrai número de câmeras do addon key"""
        if '2_cameras' in addon_key:
            return 2
        elif '5_cameras' in addon_key:
            return 5
        elif '10_cameras' in addon_key:
            return 10
        return 2

    @staticmethod
    def _parse_duration(addon_key: str) -> int:
        """Extrai duração em meses do addon key"""
        if '1month' in addon_key:
            return 1
        elif '3months' in addon_key:
            return 3
        elif '12months' in addon_key:
            return 12
        return 1


class LicenseGate:
    """Portão de licença para gating de funcionalidades"""

    def __init__(self, store_provider: StoreLicenseProvider):
        self.provider = store_provider

    async def check_camera_limit(self, current_count: int) -> bool:
        """Verifica se pode adicionar mais câmeras"""
        available = self.provider.get_available_cameras()
        return current_count < available

    async def check_feature_access(self, feature: str) -> bool:
        """Verifica acesso a feature específica"""
        features_by_tier = {
            'basic': ['live_view', 'alerts'],
            'pro': ['live_view', 'alerts', 'analytics', 'export'],
            'enterprise': ['*']  # Todas as features
        }

        # Por enquanto, todos têm acesso a features básicas
        return True

    def get_camera_limit_message(self) -> str:
        """Retorna mensagem de limite de câmeras"""
        available = self.provider.get_available_cameras()
        return f"Limite: {available} câmeras. Upgrade para mais."

    async def enforce_limits(self, current_cameras: int) -> bool:
        """Enforça limites de licença"""
        if not await self.check_camera_limit(current_cameras):
            logger.warning(
                f"Limite de câmeras atingido: {current_cameras} "
                f"(máximo: {self.provider.get_available_cameras()})"
            )
            return False

        return True


class AsyncLicenseManager:
    """Gerenciador de licenças com suporte async"""

    def __init__(self, is_store_build: bool = False):
        self.provider = StoreLicenseProvider(is_store_build)
        self.gate = LicenseGate(self.provider)
        self.last_check = None

    async def refresh(self):
        """Atualiza informações de licença"""
        try:
            await self.provider.get_app_license()
            await self.provider.get_addon_licenses()
            self.last_check = datetime.now()
            logger.info("Licenças atualizadas")

        except Exception as e:
            logger.error(f"Erro ao atualizar licenças: {e}")

    async def is_valid(self) -> bool:
        """Verifica se licença é válida"""
        await self.refresh()
        return self.provider.is_license_valid()

    async def get_status(self) -> Dict:
        """Obtém status completo de licença"""
        await self.refresh()

        return {
            'status': self.provider.get_license_status(),
            'cameras_available': self.provider.get_available_cameras(),
            'is_valid': self.provider.is_license_valid(),
            'last_check': self.last_check.isoformat() if self.last_check else None
        }
