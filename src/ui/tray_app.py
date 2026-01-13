"""
Tray application for background execution.
"""
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, Signal, QObject

logger = logging.getLogger(__name__)


class TrayAppSignals(QObject):
    """Signals for tray app communication."""
    show_window = Signal()
    hide_window = Signal()
    quit_app = Signal()
    engine_status_changed = Signal(bool)


class TrayApp:
    """Tray application for background execution."""

    def __init__(self, main_window, engine_manager):
        self.main_window = main_window
        self.engine_manager = engine_manager
        self.signals = TrayAppSignals()

        self.tray_icon = None
        self.tray_menu = None
        self.engine_running = False

        self._setup_tray()
        self._setup_signals()

    def _setup_tray(self):
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
            if icon_path.exists():
                icon = QIcon(str(icon_path))
            else:
                icon = self._create_default_icon()

            self.tray_icon = QSystemTrayIcon()
            self.tray_icon.setIcon(icon)

            self.tray_menu = QMenu()

            show_action = QAction("Show", self.tray_menu)
            show_action.triggered.connect(self._on_show)
            self.tray_menu.addAction(show_action)

            hide_action = QAction("Hide", self.tray_menu)
            hide_action.triggered.connect(self._on_hide)
            self.tray_menu.addAction(hide_action)

            self.tray_menu.addSeparator()

            self.engine_status_action = QAction("Engine: Starting...", self.tray_menu)
            self.engine_status_action.setEnabled(False)
            self.tray_menu.addAction(self.engine_status_action)

            start_engine_action = QAction("Start Engine", self.tray_menu)
            start_engine_action.triggered.connect(self._on_start_engine)
            self.tray_menu.addAction(start_engine_action)

            stop_engine_action = QAction("Stop Engine", self.tray_menu)
            stop_engine_action.triggered.connect(self._on_stop_engine)
            self.tray_menu.addAction(stop_engine_action)

            self.tray_menu.addSeparator()

            exit_action = QAction("Exit", self.tray_menu)
            exit_action.triggered.connect(self._on_exit)
            self.tray_menu.addAction(exit_action)

            self.tray_icon.setContextMenu(self.tray_menu)
            self.tray_icon.activated.connect(self._on_tray_activated)
            self.tray_icon.show()

            logger.info("Tray app configured")

        except Exception as e:
            logger.error(f"Failed to configure tray app: {e}")

    def _setup_signals(self):
        self.signals.show_window.connect(self._on_show)
        self.signals.hide_window.connect(self._on_hide)
        self.signals.quit_app.connect(self._on_exit)
        self.signals.engine_status_changed.connect(self._on_engine_status_changed)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.main_window.isVisible():
                self._on_hide()
            else:
                self._on_show()

    def _on_show(self):
        self.main_window.showNormal()
        self.main_window.activateWindow()
        logger.info("Main window shown")

    def _on_hide(self):
        self.main_window.hide()
        logger.info("Main window hidden")

    def _on_exit(self):
        logger.info("Exiting application...")
        self.engine_manager.stop()
        self.main_window.allow_close = True
        self.signals.quit_app.emit()

    def _on_engine_status_changed(self, is_running: bool):
        self.engine_running = is_running
        status_text = "Engine: Running" if is_running else "Engine: Stopped"
        self.engine_status_action.setText(status_text)

    def _on_start_engine(self):
        if not self.engine_manager.is_running:
            self.engine_manager.start()
        self.set_engine_status(self.engine_manager.is_running)

    def _on_stop_engine(self):
        if self.engine_manager.is_running:
            self.engine_manager.stop()
        self.set_engine_status(self.engine_manager.is_running)

    def _create_default_icon(self) -> QIcon:
        from PySide6.QtGui import QPixmap, QColor, QPainter

        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(33, 150, 243))

        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(painter.font())
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "AI")
        painter.end()

        return QIcon(pixmap)

    def set_engine_status(self, is_running: bool):
        self.signals.engine_status_changed.emit(is_running)

    def show_notification(self, title: str, message: str, duration: int = 5000):
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, duration=duration)
            logger.info(f"Notification: {title} - {message}")


class EngineManager:
    """Processing engine manager."""

    def __init__(self, db_manager, alert_manager, camera_manager):
        self.db = db_manager
        self.alert_manager = alert_manager
        self.camera_manager = camera_manager

        self.is_running = False
        self.watchdog_timer = None
        self.health_check_interval = 30
        self.status_callback = None

    def start(self) -> bool:
        try:
            if self.is_running:
                return True
            logger.info("Starting processing engine...")

            self.camera_manager.start_all_processors()
            self._start_watchdog()

            self.is_running = True
            if self.status_callback:
                self.status_callback(self.is_running)
            logger.info("Engine started")
            return True

        except Exception as e:
            logger.error(f"Failed to start engine: {e}")
            return False

    def stop(self):
        try:
            logger.info("Stopping processing engine...")

            self.camera_manager.stop_all_processors()
            self._stop_watchdog()

            self.is_running = False
            if self.status_callback:
                self.status_callback(self.is_running)
            logger.info("Engine stopped")

        except Exception as e:
            logger.error(f"Failed to stop engine: {e}")

    def _start_watchdog(self):
        from PySide6.QtCore import QTimer

        self.watchdog_timer = QTimer()
        self.watchdog_timer.timeout.connect(self._check_health)
        self.watchdog_timer.start(self.health_check_interval * 1000)

        logger.info("Watchdog started")

    def _stop_watchdog(self):
        if self.watchdog_timer:
            self.watchdog_timer.stop()
            logger.info("Watchdog stopped")

    def _check_health(self):
        try:
            status = self.camera_manager.get_all_camera_status()
            offline_cameras = sum(
                1 for s in status.values()
                if s.get('status') == 'offline'
            )

            if offline_cameras > 0:
                logger.warning(f"Offline cameras: {offline_cameras}/{len(status)}")

        except Exception as e:
            logger.error(f"Health check failed: {e}")

    def get_status(self) -> dict:
        return {
            'is_running': self.is_running,
            'cameras': self.camera_manager.get_all_camera_status(),
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
