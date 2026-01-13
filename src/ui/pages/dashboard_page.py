"""
Página de Dashboard
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout,
    QFrame, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
import logging

from config.ui_theme import color_for_severity, color_for_status, contrast_text

logger = logging.getLogger(__name__)


class DashboardPage(QWidget):
    """Página de dashboard com resumo do sistema"""

    def __init__(self, db_manager, alert_manager):
        super().__init__()
        self.db_manager = db_manager
        self.alert_manager = alert_manager
        self.setup_ui()

        # Timer para atualizar dados
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.auto_refresh)
        self.update_timer.start(10000)  # Atualizar a cada 10 segundos

    def setup_ui(self):
        """Configura a interface"""
        main_layout = QVBoxLayout()

        # Título
        title = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # Grid de estatísticas
        stats_layout = QGridLayout()

        self.cameras_card = self.create_stat_card("Cameras", "0")
        self.zones_card = self.create_stat_card("Zones", "0")
        self.alerts_card = self.create_stat_card("Active Alerts", "0")
        self.license_card = self.create_stat_card("License Status", "Trial")

        stats_layout.addWidget(self.cameras_card, 0, 0)
        stats_layout.addWidget(self.zones_card, 0, 1)
        stats_layout.addWidget(self.alerts_card, 1, 0)
        stats_layout.addWidget(self.license_card, 1, 1)

        stats_layout.setSpacing(15)
        main_layout.addLayout(stats_layout)

        # Alertas recentes
        main_layout.addWidget(QLabel("Recent Alerts:"))

        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(5)
        self.alerts_table.setHorizontalHeaderLabels([
            "Time", "Event", "Severity", "Camera", "Status"
        ])
        self.alerts_table.setMaximumHeight(250)
        main_layout.addWidget(self.alerts_table)

        # Câmeras ativas
        main_layout.addWidget(QLabel("Active Cameras:"))

        self.cameras_table = QTableWidget()
        self.cameras_table.setColumnCount(3)
        self.cameras_table.setHorizontalHeaderLabels([
            "Camera", "Status", "Last Detection"
        ])
        self.cameras_table.setMaximumHeight(200)
        main_layout.addWidget(self.cameras_table)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def create_stat_card(self, title: str, value: str) -> QFrame:
        """Cria um card de estatistica"""
        card = QFrame()
        card.setObjectName("StatCard")
        layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("StatTitle")
        title_font = QFont()
        title_font.setPointSize(11)
        title_label.setFont(title_font)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        value_font = QFont()
        value_font.setPointSize(28)
        value_font.setBold(True)
        self.value_label.setFont(value_font)

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
        card.setLayout(layout)

        # Armazenar label para atualização
        card.value_label = self.value_label
        card.title = title

        return card

    def refresh(self):
        """Atualiza os dados do dashboard"""
        try:
            # Aqui você atualizaria os dados com informações reais
            # Por enquanto, vamos deixar como exemplo
            pass
        except Exception as e:
            logger.error(f"Erro ao atualizar dashboard: {e}")

    def auto_refresh(self):
        """Atualiza automaticamente os dados"""
        try:
            # Atualizar alertas
            alerts = self.alert_manager.get_active_alerts()
            unacknowledged = [a for a in alerts if not a.acknowledged]

            # Atualizar card de alertas
            self.alerts_card.value_label.setText(str(len(unacknowledged)))
            self._update_alert_card_state(bool(unacknowledged))

            # Atualizar tabela de alertas
            self.alerts_table.setRowCount(min(len(unacknowledged), 10))
            for row, alert in enumerate(unacknowledged[:10]):
                time_item = QTableWidgetItem(alert.timestamp.strftime("%H:%M:%S"))
                event_item = QTableWidgetItem(alert.event_type)
                severity_item = QTableWidgetItem(alert.severity)
                camera_item = QTableWidgetItem(str(alert.camera_id))
                status_item = QTableWidgetItem("Active")

                severity_hex = color_for_severity(alert.severity)
                severity_item.setBackground(QColor(severity_hex))
                severity_item.setForeground(QColor(contrast_text(severity_hex)))

                status_hex = color_for_status("active")
                status_item.setBackground(QColor(status_hex))
                status_item.setForeground(QColor(contrast_text(status_hex)))

                self.alerts_table.setItem(row, 0, time_item)
                self.alerts_table.setItem(row, 1, event_item)
                self.alerts_table.setItem(row, 2, severity_item)
                self.alerts_table.setItem(row, 3, camera_item)
                self.alerts_table.setItem(row, 4, status_item)

        except Exception as e:
            logger.error(f"Erro ao atualizar dashboard automaticamente: {e}")

    def _update_alert_card_state(self, has_alerts: bool):
        self.alerts_card.setProperty("alert", has_alerts)
        self.alerts_card.style().unpolish(self.alerts_card)
        self.alerts_card.style().polish(self.alerts_card)
        self.alerts_card.update()

    def closeEvent(self, event):
        """Limpar timer ao fechar"""
        self.update_timer.stop()
        event.accept()
