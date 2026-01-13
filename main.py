"""
Edge Property Security AI - Main Application
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox

from config.config import APP_NAME, APP_VERSION, APP_DATA_DIR
from src.core import DatabaseManager, AuthManager, CameraManager
from src.core.alert_manager import AlertManager
from src.ui.tray_app import TrayApp, EngineManager
from src.utils import setup_logger
from src.utils.app_settings import AppSettings
from src.ui import MainWindow

logger = setup_logger(__name__)


def check_system_requirements():
    try:
        import cv2
        import numpy as np
        import onnxruntime
        logger.info("[OK] All essential dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False


def main():
    logger.info(f"{'='*60}")
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Data directory: {APP_DATA_DIR}")
    logger.info(f"{'='*60}")

    app_settings = AppSettings.load()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    if app_settings.get("enable_tray", True):
        app.setQuitOnLastWindowClosed(False)

    try:
        if not check_system_requirements():
            QMessageBox.critical(
                None,
                "Missing Dependencies",
                "Some required dependencies are missing. Install with: pip install -r requirements.txt"
            )
            sys.exit(1)

        logger.info("Initializing components...")
        db_manager = DatabaseManager(APP_DATA_DIR / "database.db")
        auth_manager = AuthManager(db_manager, app_settings)
        alert_manager = AlertManager(db_manager)
        camera_manager = CameraManager(db_manager, alert_manager)
        engine_manager = EngineManager(db_manager, alert_manager, camera_manager)

        logger.info("[OK] Components initialized")

        logger.info("Creating UI...")
        window = MainWindow(
            auth_manager,
            db_manager,
            alert_manager,
            camera_manager,
            engine_manager,
            app_settings
        )
        engine_manager.status_callback = window._update_engine_status

        tray_app = None
        if app_settings.get("enable_tray", True):
            tray_app = TrayApp(window, engine_manager)
            window.set_tray_app(tray_app)
            tray_app.signals.quit_app.connect(app.quit)

        if app_settings.get("silent_mode", False) and app_settings.get("enable_tray", True):
            window.hide()
        else:
            window.show()

        logger.info("[OK] Application started")
        logger.info(f"{'='*60}")

        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Startup Error",
            f"Failed to start application: {str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
