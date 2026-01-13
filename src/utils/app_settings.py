"""
Simple JSON-backed application settings.
"""
import json
from pathlib import Path
from typing import Any, Dict

from config.config import APP_CONFIG_DIR, DEFAULT_APP_DATA_DIR


class AppSettings:
    """Stores user-configurable app settings."""

    DEFAULTS: Dict[str, Any] = {
        "silent_mode": False,
        "enable_tray": True,
        "auto_start_engine": True,
        "require_email_verification": True,
        "smtp_server": "smtp.titan.email",
        "smtp_port": 587,
        "smtp_username": "alert@socimob.com",
        "smtp_password": "MundoMelhor@10",
        "smtp_from": "alert@socimob.com",
        "smtp_use_tls": True,
        "data_dir": str(DEFAULT_APP_DATA_DIR)
    }

    def __init__(self, path: Path):
        self.path = path
        self.data = dict(self.DEFAULTS)

    @classmethod
    def load(cls) -> "AppSettings":
        path = APP_CONFIG_DIR / "settings.json"
        settings = cls(path)
        if path.exists():
            try:
                settings.data.update(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                # Keep defaults if settings file is corrupted.
                settings.data = dict(cls.DEFAULTS)
        return settings

    def save(self):
        self.path.write_text(
            json.dumps(self.data, indent=2, sort_keys=True),
            encoding="utf-8"
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
