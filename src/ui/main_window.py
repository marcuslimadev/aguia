"""
Janela principal da aplicação
"""
import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QMessageBox, QStatusBar, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont

from config.config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT
from config.ui_theme import get_app_stylesheet
from src.ui.pages.login_page import LoginPage
from src.ui.pages.dashboard_page import DashboardPage
from src.ui.pages.cameras_page import CamerasPage, SettingsPage
from src.ui.pages.alerts_history_page import AlertsHistoryPage
from src.ui.pages.diagnostics_page import DiagnosticsPage
from src.ui.pages.live_view_page import LiveViewPage
# from src.ui.pages.zones_page import ZonesPage  # TODO: Implementar
# from src.ui.pages.settings_page import SettingsPage  # TODO: Implementar

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Janela principal da aplicação"""

    def __init__(self, auth_manager, db_manager, alert_manager, camera_manager, engine_manager, app_settings):
        super().__init__()
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.alert_manager = alert_manager
        self.camera_manager = camera_manager
        self.engine_manager = engine_manager
        self.app_settings = app_settings
        self.tray_app = None
        self.allow_close = False

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Criar interface
        self.setup_ui()
        self.apply_stylesheet()

        # Timer para verificar alertas
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.check_alerts)
        self.alert_timer.start(5000)  # Verificar a cada 5 segundos

        logger.info("Janela principal inicializada")

    def setup_ui(self):
        """Configura a interface do usuario"""
        # Widget central
        central_widget = QWidget()
        central_widget.setObjectName("AppRoot")
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.nav_frame = QFrame()
        self.nav_frame.setObjectName("Sidebar")
        nav_container = QVBoxLayout()
        nav_container.setContentsMargins(20, 20, 20, 20)
        nav_container.setSpacing(12)

        brand = QLabel(APP_NAME)
        brand.setObjectName("BrandLabel")
        nav_container.addWidget(brand)

        nav_container.addSpacing(8)
        nav_layout = QVBoxLayout()
        self.nav_buttons = {}
        self.nav_labels = {}

        pages_info = [
            ("Dashboard", "dashboard"),
            ("Live", "live"),
            ("Cameras", "cameras"),
            # ("Zones", "zones"),  # TODO: Implementar
            ("Alerts", "alerts"),
            ("Diagnostics", "diagnostics"),
            ("Settings", "settings"),
            ("Logout", "logout"),
        ]

        for label, page_id in pages_info:
            btn = QPushButton(label)
            if page_id == "logout":
                btn.setCheckable(False)
                btn.setObjectName("NavButtonDanger")
            else:
                btn.setCheckable(True)
                btn.setObjectName("NavButton")
            btn.clicked.connect(lambda checked, p=page_id: self.navigate_to_page(p))
            nav_layout.addWidget(btn)
            self.nav_buttons[page_id] = btn
            self.nav_labels[page_id] = label

        nav_container.addLayout(nav_layout)
        nav_container.addStretch()
        self.nav_frame.setLayout(nav_container)
        main_layout.addWidget(self.nav_frame)

        # Content area
        content_frame = QFrame()
        content_frame.setObjectName("ContentFrame")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(16)

        self.top_bar = QFrame()
        self.top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(8)

        self.page_title = QLabel("Login")
        self.page_title.setObjectName("PageTitle")
        top_layout.addWidget(self.page_title)

        top_layout.addStretch()

        self.user_label = QLabel("Not logged in")
        self.user_label.setObjectName("UserLabel")
        top_layout.addWidget(self.user_label)

        self.top_bar.setLayout(top_layout)
        content_layout.addWidget(self.top_bar)

        # Stacked widget para paginas
        self.stacked_widget = QStackedWidget()

        # Pagina de login
        self.login_page = LoginPage(self.auth_manager, self.db_manager)
        self.login_page.login_successful.connect(self.on_login_success)
        self.stacked_widget.addWidget(self.login_page)

        # Pagina de dashboard
        self.dashboard_page = DashboardPage(self.db_manager, self.alert_manager)
        self.stacked_widget.addWidget(self.dashboard_page)

        # Pagina de live view
        self.live_view_page = LiveViewPage(
            self.db_manager,
            self.auth_manager,
            self.camera_manager,
            self.engine_manager
        )
        self.stacked_widget.addWidget(self.live_view_page)

        # Pagina de cameras
        self.cameras_page = CamerasPage(
            self.db_manager,
            self.auth_manager,
            self.camera_manager,
            self.engine_manager
        )
        self.stacked_widget.addWidget(self.cameras_page)

        # Pagina de alertas
        self.alerts_page = AlertsHistoryPage(self.db_manager, self.camera_manager)
        self.stacked_widget.addWidget(self.alerts_page)

        # Pagina de diagnosticos
        self.diagnostics_page = DiagnosticsPage(
            self.db_manager,
            self.camera_manager,
            self.alert_manager
        )
        self.stacked_widget.addWidget(self.diagnostics_page)

        # Pagina de configuracoes
        self.settings_page = SettingsPage(
            self.db_manager,
            self.auth_manager,
            self.app_settings,
            self
        )
        self.stacked_widget.addWidget(self.settings_page)

        content_layout.addWidget(self.stacked_widget, 1)
        content_frame.setLayout(content_layout)
        main_layout.addWidget(content_frame, 1)

        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        central_widget.setLayout(main_layout)

        # Mostrar pagina de login inicialmente
        self.show_login_page()

    def set_tray_app(self, tray_app):
        """Attach tray app for notifications."""
        self.tray_app = tray_app
        self._update_engine_status()

    def _update_engine_status(self):
        if self.tray_app:
            self.tray_app.set_engine_status(self.engine_manager.is_running)

    def _prepare_engine_for_user(self):
        user_id = self.auth_manager.get_user_id()
        if not user_id:
            return

        self.camera_manager.clear_processors()
        auto_start = self.app_settings.get("auto_start_engine", True)
        self.camera_manager.load_cameras_for_user(user_id, start_processors=auto_start)
        if auto_start:
            self.engine_manager.start()
        self._update_engine_status()

    def apply_stylesheet(self):
        """Aplica estilos CSS"""
        self.setStyleSheet(get_app_stylesheet())

    def _set_alert_indicator(self, count: int):
        alert_btn = self.nav_buttons.get("alerts")
        if not alert_btn:
            return

        if count > 0:
            alert_btn.setText(f"Alerts ({count})")
            alert_btn.setProperty("alert", True)
            self.status_bar.showMessage(f"!! {count} new alert(s)")
        else:
            alert_btn.setText(self.nav_labels.get("alerts", "Alerts"))
            alert_btn.setProperty("alert", False)

        alert_btn.style().unpolish(alert_btn)
        alert_btn.style().polish(alert_btn)
        alert_btn.update()

    def show_login_page(self):
        """Mostra a pagina de login"""
        self.stacked_widget.setCurrentWidget(self.login_page)
        self.page_title.setText("Login")
        self.user_label.setText("Not logged in")
        self.top_bar.hide()
        self.hide_navigation()

    def hide_navigation(self):
        """Esconde os botoes de navegacao"""
        self.nav_frame.hide()

    def show_navigation(self):
        """Mostra os botoes de navegacao"""
        self.nav_frame.show()
        self.top_bar.show()

    def on_login_success(self):
        """Callback quando login e bem-sucedido"""
        self.show_navigation()
        self.navigate_to_page("dashboard")
        self.status_bar.showMessage(f"Logged in as {self.auth_manager.current_user['username']}")
        self.user_label.setText(self.auth_manager.current_user['username'])
        user_id = self.auth_manager.get_user_id()
        if user_id:
            self.alert_manager.setup_email_notifier(user_id)
        self._prepare_engine_for_user()
        if self.app_settings.get("silent_mode", False) and self.app_settings.get("enable_tray", True):
            self.hide()

    def navigate_to_page(self, page_id: str):
        """Navega para uma pagina"""
        if page_id == "logout":
            self.auth_manager.logout()
            self.alert_timer.stop()
            self.engine_manager.stop()
            self.camera_manager.clear_processors()
            self._update_engine_status()
            self.show_login_page()
            self.hide_navigation()
            self.status_bar.showMessage("Logged out")
            self._set_alert_indicator(0)
            return

        for pid, btn in self.nav_buttons.items():
            btn.setChecked(pid == page_id)

        if page_id == "dashboard":
            self.stacked_widget.setCurrentWidget(self.dashboard_page)
            self.dashboard_page.refresh()
            self.page_title.setText("Dashboard")
        elif page_id == "live":
            self.stacked_widget.setCurrentWidget(self.live_view_page)
            self.live_view_page.refresh()
            self.page_title.setText("Live View")
        elif page_id == "cameras":
            self.stacked_widget.setCurrentWidget(self.cameras_page)
            self.cameras_page.refresh()
            self.page_title.setText("Cameras")
        elif page_id == "zones":
            self.stacked_widget.setCurrentWidget(self.zones_page)
            self.zones_page.refresh()
            self.page_title.setText("Zones")
        elif page_id == "alerts":
            self.stacked_widget.setCurrentWidget(self.alerts_page)
            self.alerts_page.refresh()
            self.page_title.setText("Alerts")
        elif page_id == "settings":
            self.stacked_widget.setCurrentWidget(self.settings_page)
            self.settings_page.refresh()
            self.page_title.setText("Settings")
        elif page_id == "diagnostics":
            self.stacked_widget.setCurrentWidget(self.diagnostics_page)
            self.diagnostics_page.refresh_diagnostics()
            self.page_title.setText("Diagnostics")

        self.status_bar.showMessage(f"Viewing {page_id.capitalize()}")

    def check_alerts(self):
        """Verifica alertas ativos"""
        if not self.auth_manager.is_logged_in():
            return

        alerts = self.alert_manager.get_active_alerts()
        if alerts:
            unacknowledged = [a for a in alerts if not a.acknowledged]
            if unacknowledged:
                self._set_alert_indicator(len(unacknowledged))
                return
        self._set_alert_indicator(0)

    def closeEvent(self, event):
        """Evento de fechamento da aplicacao"""
        if self.app_settings.get("enable_tray", True) and not self.allow_close:
            self.hide()
            event.ignore()
            return

        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.alert_timer.stop()
            self.engine_manager.stop()
            self.camera_manager.clear_processors()
            logger.info("Aplicacao fechada")
            event.accept()
        else:
            event.ignore()
