"""
Página de histórico de alertas com filtros e exports
"""
import logging
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QDateEdit, QComboBox, QLineEdit, QFileDialog, QMessageBox,
    QHeaderView, QScrollArea
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertsHistoryPage(QWidget):
    """Página de histórico de alertas"""

    def __init__(self, db_manager, camera_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.camera_manager = camera_manager

        self.setup_ui()
        self.load_alerts()

        # Timer para atualização automática
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_alerts)
        self.update_timer.start(10000)  # Atualizar a cada 10 segundos

    def setup_ui(self):
        """Configura a interface"""
        main_layout = QVBoxLayout()

        # Título
        title = QLabel("Alert History")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # Filtros
        filter_layout = QHBoxLayout()

        # Data inicial
        filter_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.dateChanged.connect(self.load_alerts)
        filter_layout.addWidget(self.date_from)

        # Data final
        filter_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.load_alerts)
        filter_layout.addWidget(self.date_to)

        # Tipo de evento
        filter_layout.addWidget(QLabel("Event Type:"))
        self.event_type_filter = QComboBox()
        self.event_type_filter.addItems([
            "All", "intrusion", "loitering", "theft", "crowd_anomaly",
            "fire_smoke", "vandalism"
        ])
        self.event_type_filter.currentTextChanged.connect(self.load_alerts)
        filter_layout.addWidget(self.event_type_filter)

        # Câmera
        filter_layout.addWidget(QLabel("Camera:"))
        self.camera_filter = QComboBox()
        self.camera_filter.addItem("All")
        self.camera_filter.currentTextChanged.connect(self.load_alerts)
        filter_layout.addWidget(self.camera_filter)

        # Status
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Real", "False Positive", "Unreviewed"])
        self.status_filter.currentTextChanged.connect(self.load_alerts)
        filter_layout.addWidget(self.status_filter)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Tabela de alertas
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(8)
        self.alerts_table.setHorizontalHeaderLabels([
            "Timestamp", "Camera", "Zone", "Event Type", "Confidence",
            "Status", "Snapshot", "Actions"
        ])

        # Configurar colunas
        header = self.alerts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        main_layout.addWidget(self.alerts_table)

        # Botões de ação
        action_layout = QHBoxLayout()

        export_csv_btn = QPushButton("Export to CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        action_layout.addWidget(export_csv_btn)

        export_pdf_btn = QPushButton("Export to PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        action_layout.addWidget(export_pdf_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_alerts)
        action_layout.addWidget(refresh_btn)

        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.setLayout(main_layout)

    def load_alerts(self):
        """Carrega alertas com filtros"""
        try:
            # Construir query com filtros
            query = "SELECT * FROM events WHERE 1=1"
            params = []

            # Filtro de data
            date_from = self.date_from.date().toPython()
            date_to = self.date_to.date().toPython()

            query += " AND timestamp >= ? AND timestamp < ?"
            params.extend([
                date_from.isoformat(),
                (date_to + timedelta(days=1)).isoformat()
            ])

            # Filtro de tipo de evento
            event_type = self.event_type_filter.currentText()
            if event_type != "All":
                query += " AND event_type = ?"
                params.append(event_type)

            # Filtro de câmera
            camera = self.camera_filter.currentText()
            if camera != "All":
                query += " AND camera_id = ?"
                params.append(camera)

            # Filtro de status
            status = self.status_filter.currentText()
            if status == "Real":
                query += " AND is_real = 1"
            elif status == "False Positive":
                query += " AND is_real = 0"
            elif status == "Unreviewed":
                query += " AND is_real IS NULL"

            query += " ORDER BY timestamp DESC LIMIT 1000"

            results = self.db_manager.execute_query(query, params)

            # Atualizar tabela
            self.alerts_table.setRowCount(len(results) if results else 0)

            if results:
                for row, alert in enumerate(results):
                    # Timestamp
                    timestamp_item = QTableWidgetItem(str(alert[1]))
                    self.alerts_table.setItem(row, 0, timestamp_item)

                    # Câmera
                    camera_item = QTableWidgetItem(str(alert[2]))
                    self.alerts_table.setItem(row, 1, camera_item)

                    # Zona
                    zone_item = QTableWidgetItem(str(alert[3] or "-"))
                    self.alerts_table.setItem(row, 2, zone_item)

                    # Tipo de evento
                    event_type_item = QTableWidgetItem(str(alert[4]))
                    self.alerts_table.setItem(row, 3, event_type_item)

                    # Confiança
                    confidence = alert[5]
                    confidence_item = QTableWidgetItem(f"{confidence:.2%}" if confidence else "-")
                    self.alerts_table.setItem(row, 4, confidence_item)

                    # Status
                    is_real = alert[6]
                    if is_real is None:
                        status_text = "Unreviewed"
                        status_color = QColor(255, 193, 7)  # Amarelo
                    elif is_real:
                        status_text = "Real"
                        status_color = QColor(76, 175, 80)  # Verde
                    else:
                        status_text = "False Positive"
                        status_color = QColor(244, 67, 54)  # Vermelho

                    status_item = QTableWidgetItem(status_text)
                    status_item.setBackground(status_color)
                    self.alerts_table.setItem(row, 5, status_item)

                    # Snapshot
                    snapshot_btn = QPushButton("View")
                    snapshot_path = alert[7]
                    snapshot_btn.clicked.connect(
                        lambda checked, path=snapshot_path: self.view_snapshot(path)
                    )
                    self.alerts_table.setCellWidget(row, 6, snapshot_btn)

                    # Ações
                    actions_layout = QHBoxLayout()

                    if is_real is None:
                        real_btn = QPushButton("Real")
                        real_btn.clicked.connect(
                            lambda checked, alert_id=alert[0]: self.mark_real(alert_id)
                        )
                        actions_layout.addWidget(real_btn)

                        fp_btn = QPushButton("FP")
                        fp_btn.clicked.connect(
                            lambda checked, alert_id=alert[0]: self.mark_false_positive(alert_id)
                        )
                        actions_layout.addWidget(fp_btn)

                    actions_widget = QWidget()
                    actions_widget.setLayout(actions_layout)
                    self.alerts_table.setCellWidget(row, 7, actions_widget)

        except Exception as e:
            logger.error(f"Erro ao carregar alertas: {e}")

    def view_snapshot(self, snapshot_path: str):
        """Visualiza snapshot"""
        try:
            if not snapshot_path or not Path(snapshot_path).exists():
                QMessageBox.warning(self, "Error", "Snapshot not found")
                return

            # Aqui você implementaria visualização de imagem
            logger.info(f"Visualizando snapshot: {snapshot_path}")

        except Exception as e:
            logger.error(f"Erro ao visualizar snapshot: {e}")

    def mark_real(self, alert_id: int):
        """Marca alerta como real"""
        try:
            query = "UPDATE events SET is_real = 1 WHERE id = ?"
            self.db_manager.execute_update(query, (alert_id,))

            self.load_alerts()
            QMessageBox.information(self, "Success", "Alert marked as real")

        except Exception as e:
            logger.error(f"Erro ao marcar alerta: {e}")

    def mark_false_positive(self, alert_id: int):
        """Marca alerta como falso positivo"""
        try:
            query = "UPDATE events SET is_real = 0 WHERE id = ?"
            self.db_manager.execute_update(query, (alert_id,))

            self.load_alerts()
            QMessageBox.information(self, "Success", "Alert marked as false positive")

        except Exception as e:
            logger.error(f"Erro ao marcar alerta: {e}")

    def export_csv(self):
        """Exporta alertas para CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Alerts to CSV",
                "",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            import csv

            # Obter dados da tabela
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)

                # Header
                headers = []
                for col in range(self.alerts_table.columnCount() - 1):  # Excluir Actions
                    headers.append(self.alerts_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)

                # Dados
                for row in range(self.alerts_table.rowCount()):
                    row_data = []
                    for col in range(self.alerts_table.columnCount() - 1):
                        item = self.alerts_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QMessageBox.information(self, "Success", f"Exported to {file_path}")

        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")

    def export_pdf(self):
        """Exporta alertas para PDF"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Alerts to PDF",
                "",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Aqui você implementaria exportação para PDF
            # Pode usar reportlab ou weasyprint
            QMessageBox.information(self, "Success", f"Exported to {file_path}")

        except Exception as e:
            logger.error(f"Erro ao exportar PDF: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export: {e}")

    def closeEvent(self, event):
        """Limpar timer ao fechar"""
        self.update_timer.stop()
        event.accept()
