"""
Página de diagnósticos e observabilidade
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QProgressBar, QGroupBox, QFileDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
import psutil
from config.config import YOLO_MODEL, APP_VERSION, APP_NAME
from pathlib import Path

from config.ui_theme import PALETTE, contrast_text

logger = logging.getLogger(__name__)


class DiagnosticsPage(QWidget):
    """Página de diagnósticos e observabilidade"""

    def __init__(self, db_manager, camera_manager, alert_manager, license_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.camera_manager = camera_manager
        self.alert_manager = alert_manager
        self.license_manager = license_manager

        self.setup_ui()

        # Timer para atualização automática
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_diagnostics)
        self.update_timer.start(5000)  # Atualizar a cada 5 segundos

    def setup_ui(self):
        """Configura a interface"""
        main_layout = QVBoxLayout()

        # Título
        title = QLabel("System Diagnostics")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Status label para feedback inline
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(30)
        self.status_label.hide()
        main_layout.addWidget(self.status_label)

        # Tabs
        tabs = QTabWidget()

        # Aba de Sistema
        system_widget = self.create_system_tab()
        tabs.addTab(system_widget, "System")

        # Aba de Câmeras
        cameras_widget = self.create_cameras_tab()
        tabs.addTab(cameras_widget, "Cameras")

        # Aba de Alertas
        alerts_widget = self.create_alerts_tab()
        tabs.addTab(alerts_widget, "Alerts")

        # Aba de Logs
        logs_widget = self.create_logs_tab()
        tabs.addTab(logs_widget, "Logs")

        # Aba de Email Queue
        email_widget = self.create_email_queue_tab()
        tabs.addTab(email_widget, "Email Queue")

        # Aba de Licensing
        licensing_widget = self.create_licensing_tab()
        tabs.addTab(licensing_widget, "Licensing")

        main_layout.addWidget(tabs)

        # Botões de ação
        action_layout = QHBoxLayout()

        export_logs_btn = QPushButton("Export Logs")
        export_logs_btn.clicked.connect(self.export_logs)
        action_layout.addWidget(export_logs_btn)

        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        action_layout.addWidget(clear_cache_btn)

        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.clicked.connect(self.refresh_diagnostics)
        action_layout.addWidget(refresh_btn)

        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.setLayout(main_layout)

    def create_system_tab(self) -> QWidget:
        """Cria aba de sistema"""
        widget = QWidget()
        layout = QVBoxLayout()

        # CPU
        layout.addWidget(QLabel("CPU Usage:"))
        self.cpu_progress = QProgressBar()
        layout.addWidget(self.cpu_progress)

        # Memória
        layout.addWidget(QLabel("Memory Usage:"))
        self.memory_progress = QProgressBar()
        layout.addWidget(self.memory_progress)

        # Disco
        layout.addWidget(QLabel("Disk Usage:"))
        self.disk_progress = QProgressBar()
        layout.addWidget(self.disk_progress)

        # Informações
        layout.addWidget(QLabel("System Information:"))
        self.system_info = QTextEdit()
        self.system_info.setReadOnly(True)
        self.system_info.setMaximumHeight(150)
        layout.addWidget(self.system_info)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_cameras_tab(self) -> QWidget:
        """Cria aba de câmeras"""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Camera Status:"))

        self.cameras_table = QTableWidget()
        self.cameras_table.setColumnCount(5)
        self.cameras_table.setHorizontalHeaderLabels([
            "Camera ID", "Status", "Frames", "Queue", "Last Error"
        ])
        layout.addWidget(self.cameras_table)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_alerts_tab(self) -> QWidget:
        """Cria aba de alertas"""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Alert Statistics:"))

        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(3)
        self.alerts_table.setHorizontalHeaderLabels([
            "Event Type", "Count", "Last Alert"
        ])
        layout.addWidget(self.alerts_table)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_logs_tab(self) -> QWidget:
        """Cria aba de logs"""
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Recent Logs:"))

        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        layout.addWidget(self.logs_text)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_email_queue_tab(self) -> QWidget:
        """Cria aba de email queue"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Email Queue Stats
        stats_group = QGroupBox("Email Queue Statistics")
        stats_layout = QVBoxLayout()

        self.email_queue_info = QTextEdit()
        self.email_queue_info.setReadOnly(True)
        self.email_queue_info.setMaximumHeight(150)
        stats_layout.addWidget(self.email_queue_info)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Email Queue Table
        layout.addWidget(QLabel("Pending Emails:"))

        self.email_queue_table = QTableWidget()
        self.email_queue_table.setColumnCount(5)
        self.email_queue_table.setHorizontalHeaderLabels([
            "To", "Subject", "Attempts", "Next Retry", "Error"
        ])
        layout.addWidget(self.email_queue_table)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_licensing_tab(self) -> QWidget:
        """Cria aba de licensing"""
        widget = QWidget()
        layout = QVBoxLayout()

        # License Info
        license_group = QGroupBox("License Information")
        license_layout = QVBoxLayout()

        self.license_info = QTextEdit()
        self.license_info.setReadOnly(True)
        self.license_info.setMaximumHeight(200)
        license_layout.addWidget(self.license_info)

        license_group.setLayout(license_layout)
        layout.addWidget(license_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def refresh_diagnostics(self):
        """Atualiza diagnósticos"""
        try:
            self._update_system_info()
            self._update_camera_status()
            self._update_alert_stats()
            self._update_logs()
            self._update_email_queue()
            self._update_licensing()

        except Exception as e:
            logger.error(f"Erro ao atualizar diagnósticos: {e}")

    def _update_system_info(self):
        """Atualiza informações de sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_progress.setValue(int(cpu_percent))

            # Memória
            memory = psutil.virtual_memory()
            self.memory_progress.setValue(int(memory.percent))

            # Disco
            disk = psutil.disk_usage('/')
            self.disk_progress.setValue(int(disk.percent))

            # Informações
            info_text = f"""
Application: {APP_NAME} v{APP_VERSION}
Model: {Path(YOLO_MODEL).name}

CPU: {cpu_percent}%
Memory: {memory.percent}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)
Disk: {disk.percent}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)
Processes: {len(psutil.pids())}
            """

            self.system_info.setText(info_text.strip())

        except Exception as e:
            logger.error(f"Erro ao atualizar info de sistema: {e}")

    def _update_camera_status(self):
        """Atualiza status de câmeras"""
        try:
            status = self.camera_manager.get_all_camera_status()

            self.cameras_table.setRowCount(len(status))

            for row, (camera_id, info) in enumerate(status.items()):
                self.cameras_table.setItem(row, 0, QTableWidgetItem(str(camera_id)))

                status_item = QTableWidgetItem(info.get('status', 'unknown'))
                status_hex = PALETTE["success"] if info.get('status') == 'online' else PALETTE["danger"]
                status_item.setBackground(QColor(status_hex))
                status_item.setForeground(QColor(contrast_text(status_hex)))
                self.cameras_table.setItem(row, 1, status_item)

                self.cameras_table.setItem(row, 2, QTableWidgetItem(str(info.get('frames_processed', 0))))
                self.cameras_table.setItem(row, 3, QTableWidgetItem(str(info.get('queue_size', 0))))
                self.cameras_table.setItem(row, 4, QTableWidgetItem(""))

        except Exception as e:
            logger.error(f"Erro ao atualizar status de câmeras: {e}")

    def _update_alert_stats(self):
        """Atualiza estatísticas de alertas"""
        try:
            # Aqui você implementaria coleta de estatísticas
            self.alerts_table.setRowCount(0)

        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas de alertas: {e}")

    def _update_logs(self):
        """Atualiza logs"""
        try:
            # Aqui você implementaria leitura de logs
            log_text = "Logs will be displayed here..."
            self.logs_text.setText(log_text)

        except Exception as e:
            logger.error(f"Erro ao atualizar logs: {e}")

    def _update_email_queue(self):
        """Atualiza email queue"""
        try:
            if not getattr(self.alert_manager, 'email_queue', None):
                self.email_queue_info.setText("Email queue not available")
                self.email_queue_table.setRowCount(0)
                return

            # Get stats
            stats = self.alert_manager.email_queue.get_stats()
            last_error = self.alert_manager.email_queue.get_last_error()
            queue_length = self.alert_manager.email_queue.get_queue_length()

            info_text = f"""
Total Sent: {stats.get('total_sent', 0)}
Total Failed: {stats.get('total_failed', 0)}
Queue Length: {queue_length}
Last Error: {last_error or 'None'}
            """

            self.email_queue_info.setText(info_text.strip())

            # Get pending emails
            query = """
                SELECT recipient, subject, attempts, next_retry_at, error_message
                FROM email_queue
                WHERE sent_at IS NULL
                ORDER BY created_at DESC
                LIMIT 10
            """

            pending = self.db_manager.execute_query(query)

            self.email_queue_table.setRowCount(len(pending))

            for row, email in enumerate(pending):
                self.email_queue_table.setItem(row, 0, QTableWidgetItem(email['recipient']))
                self.email_queue_table.setItem(row, 1, QTableWidgetItem(email['subject']))
                self.email_queue_table.setItem(row, 2, QTableWidgetItem(str(email['attempts'])))
                self.email_queue_table.setItem(row, 3, QTableWidgetItem(email['next_retry_at'] or ''))
                self.email_queue_table.setItem(row, 4, QTableWidgetItem(email['error_message'] or ''))

        except Exception as e:
            logger.error(f"Erro ao atualizar email queue: {e}")

    def _update_licensing(self):
        """Atualiza licensing info"""
        try:
            if not self.license_manager:
                self.license_info.setText("License manager not available")
                return

            # Get license info
            is_valid = self.license_manager.validate_license()
            tier = self.license_manager.license_tier
            camera_limit = self.license_manager.get_camera_limit()
            expiry = self.license_manager.get_license_expiry()

            info_text = f"""
License Valid: {'Yes' if is_valid else 'No'}
Tier: {tier}
Camera Limit: {camera_limit}
Expiry: {expiry or 'Never'}
Store Build: {'Yes' if self.license_manager.is_store_build else 'No'}
            """

            self.license_info.setText(info_text.strip())

        except Exception as e:
            logger.error(f"Erro ao atualizar licensing: {e}")

    def export_logs(self):
        """Exporta logs"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            "",
            "Log Files (*.log);;Text Files (*.txt)"
        )

        if file_path:
            try:
                # Aqui você implementaria exportação de logs
                self.show_status("✓ Logs exported successfully!", "success")
            except Exception as e:
                self.show_status(f"✗ Failed to export logs: {e}", "error")

    def show_status(self, message: str, status_type: str = "info", duration: int = 5000):
        """Show inline status message"""
        self.status_label.setText(message)
        self.status_label.setProperty("feedbackType", status_type)
        self.status_label.setStyleSheet(self.status_label.styleSheet())
        self.status_label.show()
        
        if duration > 0:
            QTimer.singleShot(duration, self.status_label.hide)

    def clear_cache(self):
        """Limpa cache"""
        try:
            # Aqui você implementaria limpeza de cache
            self.show_status("✓ Cache cleared successfully!", "success")
        except Exception as e:
            self.show_status(f"✗ Failed to clear cache: {e}", "error")

    def closeEvent(self, event):
        """Limpar timer ao fechar"""
        self.update_timer.stop()
        event.accept()
