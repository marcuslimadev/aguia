"""
Internacionalização (i18n) para múltiplos idiomas
"""
import logging
import json
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class I18nManager:
    """Gerenciador de internacionalização"""

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'pt-BR': 'Português (Brasil)',
        'es-ES': 'Español (España)',
        'de-DE': 'Deutsch (Deutschland)'
    }

    def __init__(self, language: str = 'en'):
        """
        Inicializa gerenciador i18n

        Args:
            language: Código de idioma (en, pt-BR, es-ES, de-DE)
        """
        self.language = language
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()

    def load_translations(self):
        """Carrega traduções de arquivos"""
        try:
            translations_dir = Path(__file__).parent.parent.parent / 'translations'

            if not translations_dir.exists():
                logger.warning(f"Diretório de traduções não encontrado: {translations_dir}")
                self._load_default_translations()
                return

            # Carregar arquivo de idioma
            lang_file = translations_dir / f"{self.language}.json"

            if not lang_file.exists():
                logger.warning(f"Arquivo de idioma não encontrado: {lang_file}")
                self._load_default_translations()
                return

            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)

            logger.info(f"✓ Traduções carregadas: {self.language}")

        except Exception as e:
            logger.error(f"Erro ao carregar traduções: {e}")
            self._load_default_translations()

    def _load_default_translations(self):
        """Carrega traduções padrão (inglês)"""
        self.translations = self._get_default_strings()

    def translate(self, key: str, default: Optional[str] = None) -> str:
        """
        Traduz chave

        Args:
            key: Chave de tradução (ex: 'ui.button.ok')
            default: Valor padrão se não encontrado

        Returns:
            String traduzida
        """
        try:
            # Navegar pela estrutura aninhada
            parts = key.split('.')
            value = self.translations

            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return default or key

            return value if value else (default or key)

        except Exception as e:
            logger.debug(f"Erro ao traduzir {key}: {e}")
            return default or key

    def set_language(self, language: str):
        """Muda idioma"""
        if language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Idioma não suportado: {language}")
            return False

        self.language = language
        self.load_translations()
        logger.info(f"Idioma alterado para: {language}")
        return True

    def get_supported_languages(self) -> Dict[str, str]:
        """Retorna idiomas suportados"""
        return self.SUPPORTED_LANGUAGES

    def get_current_language(self) -> str:
        """Retorna idioma atual"""
        return self.language

    @staticmethod
    def _get_default_strings() -> Dict:
        """Retorna strings padrão em inglês"""
        return {
            'ui': {
                'button': {
                    'ok': 'OK',
                    'cancel': 'Cancel',
                    'save': 'Save',
                    'delete': 'Delete',
                    'edit': 'Edit',
                    'add': 'Add',
                    'refresh': 'Refresh',
                    'export': 'Export',
                    'import': 'Import',
                    'close': 'Close'
                },
                'menu': {
                    'file': 'File',
                    'edit': 'Edit',
                    'view': 'View',
                    'help': 'Help',
                    'settings': 'Settings',
                    'exit': 'Exit'
                },
                'label': {
                    'username': 'Username',
                    'password': 'Password',
                    'email': 'Email',
                    'camera': 'Camera',
                    'zone': 'Zone',
                    'alert': 'Alert',
                    'timestamp': 'Timestamp',
                    'status': 'Status',
                    'confidence': 'Confidence'
                }
            },
            'messages': {
                'success': 'Operation completed successfully',
                'error': 'An error occurred',
                'warning': 'Warning',
                'info': 'Information',
                'confirm': 'Are you sure?',
                'loading': 'Loading...',
                'saving': 'Saving...',
                'deleting': 'Deleting...'
            },
            'errors': {
                'connection_failed': 'Connection failed',
                'invalid_credentials': 'Invalid credentials',
                'camera_offline': 'Camera is offline',
                'no_cameras': 'No cameras configured',
                'invalid_input': 'Invalid input',
                'database_error': 'Database error'
            },
            'alerts': {
                'intrusion': 'Intrusion Detected',
                'loitering': 'Loitering Detected',
                'theft': 'Theft Detected',
                'crowd_anomaly': 'Crowd Anomaly',
                'fire_smoke': 'Fire/Smoke Detected',
                'vandalism': 'Vandalism Detected'
            },
            'pages': {
                'login': 'Login',
                'dashboard': 'Dashboard',
                'cameras': 'Cameras',
                'zones': 'Zones',
                'alerts': 'Alerts',
                'history': 'History',
                'feedback': 'Feedback',
                'diagnostics': 'Diagnostics',
                'settings': 'Settings'
            }
        }


# Instância global
_i18n_instance: Optional[I18nManager] = None


def get_i18n() -> I18nManager:
    """Obtém instância global de i18n"""
    global _i18n_instance

    if _i18n_instance is None:
        _i18n_instance = I18nManager()

    return _i18n_instance


def _(key: str, default: Optional[str] = None) -> str:
    """Função de conveniência para tradução"""
    return get_i18n().translate(key, default)


def set_language(language: str) -> bool:
    """Define idioma global"""
    return get_i18n().set_language(language)


def get_language() -> str:
    """Obtém idioma atual"""
    return get_i18n().get_current_language()
