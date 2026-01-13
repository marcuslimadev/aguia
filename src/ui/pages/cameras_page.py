"""
UI pages for cameras, zones, and settings.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QComboBox,
    QTextEdit, QTabWidget, QCheckBox
)
from PySide6.QtGui import QFont, QColor

logger = logging.getLogger(__name__)


class CamerasPage(QWidget):
    """Camera management page."""

    def __init__(self, db_manager, auth_manager, camera_manager, engine_manager):
        super().__init__()
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.camera_manager = camera_manager
        self.engine_manager = engine_manager
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Cameras")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("Camera Name:"))
        self.camera_name = QLineEdit()
        self.camera_name.setPlaceholderText("e.g., Front Door, Parking Lot")
        form_layout.addWidget(self.camera_name)

        form_layout.addWidget(QLabel("RTSP URL:"))
        self.rtsp_url = QLineEdit()
        self.rtsp_url.setPlaceholderText("e.g., rtsp://192.168.1.100:554/stream")
        form_layout.addWidget(self.rtsp_url)

        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Camera")
        add_btn.clicked.connect(self.add_camera)
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(test_btn)
        form_layout.addLayout(button_layout)

        main_layout.addLayout(form_layout)

        main_layout.addWidget(QLabel("Configured Cameras:"))
        self.cameras_table = QTableWidget()
        self.cameras_table.setColumnCount(5)
        self.cameras_table.setHorizontalHeaderLabels(
            ["ID", "Name", "RTSP URL", "Status", "Actions"]
        )
        self.cameras_table.setColumnWidth(2, 250)
        main_layout.addWidget(self.cameras_table)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def add_camera(self):
        name = self.camera_name.text().strip()
        rtsp_url = self.rtsp_url.text().strip()

        user_id = self.auth_manager.get_user_id()
        if not user_id:
            QMessageBox.warning(self, "Error", "You must be logged in to add cameras")
            return

        if not name or not rtsp_url:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return

        if not rtsp_url.startswith("rtsp://"):
            QMessageBox.warning(self, "Error", "RTSP URL must start with rtsp://")
            return

        try:
            camera_id = self.db_manager.add_camera(user_id, name, rtsp_url)
            self.camera_manager.add_camera_processor(
                camera_id,
                rtsp_url,
                start_processor=self.engine_manager.is_running
            )
            QMessageBox.information(self, "Success", "Camera added successfully!")
            self.camera_name.clear()
            self.rtsp_url.clear()
            self.refresh()
        except Exception as e:
            logger.error(f"Error adding camera: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add camera: {e}")

    def test_connection(self):
        rtsp_url = self.rtsp_url.text().strip()
        if not rtsp_url:
            QMessageBox.warning(self, "Error", "Please enter RTSP URL")
            return

        QMessageBox.information(self, "Testing", "Connection test would be performed here")

    def refresh(self):
        try:
            user_id = self.auth_manager.get_user_id()
            if not user_id:
                self.cameras_table.setRowCount(0)
                return

            cameras = self.db_manager.get_cameras(user_id)
            self.cameras_table.setRowCount(len(cameras))

            for row, camera in enumerate(cameras):
                camera_id = camera["id"]
                status = self.camera_manager.get_camera_status(camera_id)
                status_text = status.get("status", "offline") if status else "offline"

                self.cameras_table.setItem(row, 0, QTableWidgetItem(str(camera_id)))
                self.cameras_table.setItem(row, 1, QTableWidgetItem(camera["name"]))
                self.cameras_table.setItem(row, 2, QTableWidgetItem(camera["rtsp_url"]))
                self.cameras_table.setItem(row, 3, QTableWidgetItem(status_text.capitalize()))
                self.cameras_table.setItem(row, 4, QTableWidgetItem(""))
        except Exception as e:
            logger.error(f"Error refreshing cameras: {e}")


class ZonesPage(QWidget):
    """Zone management page (placeholder)."""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Zones")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Select Camera:"))
        self.camera_combo = QComboBox()
        form_layout.addWidget(self.camera_combo)
        main_layout.addLayout(form_layout)

        main_layout.addWidget(QLabel("Zone Name:"))
        self.zone_name = QLineEdit()
        self.zone_name.setPlaceholderText("e.g., Entrance, Restricted Area")
        main_layout.addWidget(self.zone_name)

        main_layout.addWidget(QLabel("Zone Type:"))
        self.zone_type = QComboBox()
        self.zone_type.addItems(["Detection", "Restricted", "Loitering"])
        main_layout.addWidget(self.zone_type)

        add_zone_btn = QPushButton("Add Zone")
        add_zone_btn.clicked.connect(self.add_zone)
        main_layout.addWidget(add_zone_btn)

        main_layout.addWidget(QLabel("Configured Zones:"))
        self.zones_table = QTableWidget()
        self.zones_table.setColumnCount(4)
        self.zones_table.setHorizontalHeaderLabels(["Camera", "Zone Name", "Type", "Actions"])
        main_layout.addWidget(self.zones_table)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def add_zone(self):
        name = self.zone_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter zone name")
            return

        QMessageBox.information(self, "Success", f"Zone '{name}' added successfully!")
        self.zone_name.clear()
        self.refresh()

    def refresh(self):
        pass


class AlertsPage(QWidget):
    """Alerts view (legacy placeholder)."""

    def __init__(self, db_manager, alert_manager):
        super().__init__()
        self.db_manager = db_manager
        self.alert_manager = alert_manager
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Alerts")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Severity:"))
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["All", "Low", "Medium", "High", "Critical"])
        filter_layout.addWidget(self.severity_combo)

        filter_layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Active", "Acknowledged"])
        filter_layout.addWidget(self.status_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(refresh_btn)
        filter_layout.addStretch()

        main_layout.addLayout(filter_layout)

        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(6)
        self.alerts_table.setHorizontalHeaderLabels(
            ["ID", "Event Type", "Severity", "Timestamp", "Status", "Actions"]
        )
        main_layout.addWidget(self.alerts_table)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def refresh(self):
        try:
            alerts = self.alert_manager.get_active_alerts()
            self.alerts_table.setRowCount(len(alerts))

            for row, alert in enumerate(alerts):
                self.alerts_table.setItem(row, 0, QTableWidgetItem(str(alert.alert_id)))
                self.alerts_table.setItem(row, 1, QTableWidgetItem(alert.event_type))

                severity_item = QTableWidgetItem(alert.severity)
                severity_colors = {
                    'low': QColor(255, 204, 0),
                    'medium': QColor(255, 152, 0),
                    'high': QColor(212, 0, 0),
                    'critical': QColor(111, 0, 0)
                }
                severity_item.setForeground(severity_colors.get(alert.severity, QColor(0, 91, 187)))
                self.alerts_table.setItem(row, 2, severity_item)

                self.alerts_table.setItem(row, 3, QTableWidgetItem(alert.timestamp.isoformat()))
                status = "Acknowledged" if alert.acknowledged else "Active"
                self.alerts_table.setItem(row, 4, QTableWidgetItem(status))

                ack_btn = QPushButton("Acknowledge")
                ack_btn.clicked.connect(lambda checked, aid=alert.alert_id: self.acknowledge_alert(aid))
                self.alerts_table.setCellWidget(row, 5, ack_btn)

        except Exception as e:
            logger.error(f"Error refreshing alerts: {e}")

    def acknowledge_alert(self, alert_id: int):
        try:
            self.alert_manager.acknowledge_alert(alert_id)
            QMessageBox.information(self, "Success", "Alert acknowledged!")
            self.refresh()
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")


class SettingsPage(QWidget):
    """Settings page for runtime and email settings."""

    def __init__(self, db_manager, auth_manager, app_settings, main_window):
        super().__init__()
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.app_settings = app_settings
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        tabs = QTabWidget()

        system_widget = self.create_system_settings()
        tabs.addTab(system_widget, "System")

        license_widget = self.create_license_settings()
        tabs.addTab(license_widget, "License")

        main_layout.addWidget(tabs)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def create_email_settings(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("SMTP Server:"))
        self.smtp_server = QLineEdit()
        self.smtp_server.setPlaceholderText("e.g., smtp.gmail.com")
        layout.addWidget(self.smtp_server)

        layout.addWidget(QLabel("SMTP Port:"))
        self.smtp_port = QSpinBox()
        self.smtp_port.setValue(587)
        self.smtp_port.setRange(1, 65535)
        layout.addWidget(self.smtp_port)

        layout.addWidget(QLabel("SMTP Username:"))
        self.smtp_username = QLineEdit()
        layout.addWidget(self.smtp_username)

        layout.addWidget(QLabel("Sender Email:"))
        self.sender_email = QLineEdit()
        layout.addWidget(self.sender_email)

        layout.addWidget(QLabel("Sender Password:"))
        self.sender_password = QLineEdit()
        self.sender_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.sender_password)

        self.use_tls_checkbox = QCheckBox("Use TLS")
        layout.addWidget(self.use_tls_checkbox)

        layout.addWidget(QLabel("Recipient Emails (comma-separated):"))
        self.recipient_emails = QTextEdit()
        self.recipient_emails.setMaximumHeight(100)
        layout.addWidget(self.recipient_emails)

        save_btn = QPushButton("Save Email Settings")
        save_btn.clicked.connect(self.save_email_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_system_settings(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("System Configuration:"))
        layout.addWidget(QLabel("- Application Data: C:/ProgramData/EdgeAI"))
        layout.addWidget(QLabel("- Database: SQLite"))
        layout.addWidget(QLabel("- AI Model: YOLOv8"))

        layout.addWidget(QLabel("Runtime Behavior:"))
        self.enable_tray_checkbox = QCheckBox("Run in background (tray)")
        layout.addWidget(self.enable_tray_checkbox)

        self.silent_mode_checkbox = QCheckBox("Start hidden (silent mode)")
        layout.addWidget(self.silent_mode_checkbox)

        self.auto_start_engine_checkbox = QCheckBox("Auto-start engine after login")
        layout.addWidget(self.auto_start_engine_checkbox)

        layout.addWidget(QLabel("Performance Settings:"))
        layout.addWidget(QLabel("Frame Skip:"))
        self.frame_skip = QSpinBox()
        self.frame_skip.setValue(2)
        layout.addWidget(self.frame_skip)

        layout.addWidget(QLabel("Target FPS:"))
        self.target_fps = QSpinBox()
        self.target_fps.setValue(15)
        layout.addWidget(self.target_fps)

        save_btn = QPushButton("Save System Settings")
        save_btn.clicked.connect(self.save_system_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_license_settings(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("License Information:"))
        self.license_info = QTextEdit()
        self.license_info.setReadOnly(True)
        self.license_info.setText("License: Trial\nExpires: 7 days\nCameras: 2/2")
        layout.addWidget(self.license_info)

        layout.addWidget(QLabel("Upgrade License:"))
        upgrade_btn = QPushButton("Open Microsoft Store")
        upgrade_btn.clicked.connect(self.open_store)
        layout.addWidget(upgrade_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def save_email_settings(self):
        user = self.auth_manager.get_current_user()
        if not user:
            QMessageBox.warning(self, "Error", "Login required to save email settings")
            return

        smtp_server = self.smtp_server.text().strip()
        smtp_port = int(self.smtp_port.value())
        smtp_username = self.smtp_username.text().strip()
        sender_email = self.sender_email.text().strip()
        sender_password = self.sender_password.text()
        use_tls = self.use_tls_checkbox.isChecked()
        recipients = self.recipient_emails.toPlainText().strip()

        if not recipients:
            recipients = user.get("email", "")

        if not smtp_server or not smtp_username or not sender_email or not sender_password:
            QMessageBox.warning(self, "Error", "Please fill SMTP settings")
            return

        self.app_settings.set("smtp_server", smtp_server)
        self.app_settings.set("smtp_port", smtp_port)
        self.app_settings.set("smtp_username", smtp_username)
        self.app_settings.set("smtp_password", sender_password)
        self.app_settings.set("smtp_from", sender_email)
        self.app_settings.set("smtp_use_tls", use_tls)
        self.app_settings.save()

        self.db_manager.set_email_settings(
            user_id=user["id"],
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            sender_email=sender_email,
            sender_password=sender_password,
            recipient_emails=recipients
        )

        QMessageBox.information(self, "Success", "Email settings saved successfully!")

    def save_system_settings(self):
        enable_tray = self.enable_tray_checkbox.isChecked()
        silent_mode = self.silent_mode_checkbox.isChecked()
        auto_start = self.auto_start_engine_checkbox.isChecked()

        if silent_mode and not enable_tray:
            silent_mode = False
            self.silent_mode_checkbox.setChecked(False)
            QMessageBox.warning(self, "Warning", "Silent mode requires tray enabled")

        self.app_settings.set("enable_tray", enable_tray)
        self.app_settings.set("silent_mode", silent_mode)
        self.app_settings.set("auto_start_engine", auto_start)
        self.app_settings.save()

        QMessageBox.information(
            self,
            "Success",
            "System settings saved. Restart may be required to apply changes."
        )

    def open_store(self):
        import webbrowser
        webbrowser.open("https://www.microsoft.com/store/apps/")

    def refresh(self):
        if hasattr(self, "enable_tray_checkbox"):
            self.enable_tray_checkbox.setChecked(self.app_settings.get("enable_tray", True))
            self.silent_mode_checkbox.setChecked(self.app_settings.get("silent_mode", False))
            self.auto_start_engine_checkbox.setChecked(self.app_settings.get("auto_start_engine", True))

        if hasattr(self, "smtp_server"):
            self.smtp_server.setText(self.app_settings.get("smtp_server", ""))
            self.smtp_port.setValue(int(self.app_settings.get("smtp_port", 587)))
            self.smtp_username.setText(self.app_settings.get("smtp_username", ""))
            self.sender_email.setText(self.app_settings.get("smtp_from", ""))
            self.sender_password.setText(self.app_settings.get("smtp_password", ""))
            self.use_tls_checkbox.setChecked(bool(self.app_settings.get("smtp_use_tls", True)))

            user = self.auth_manager.get_current_user()
            if user:
                settings = self.db_manager.get_email_settings(user["id"])
                if settings:
                    self.recipient_emails.setText(settings["recipient_emails"])
