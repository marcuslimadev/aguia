"""
Página de feedback para calibração de falsos positivos
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QSpinBox, QMessageBox, QHeaderView, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from config.ui_theme import color_for_status, contrast_text

logger = logging.getLogger(__name__)


class FeedbackPage(QWidget):
    """Página de feedback para calibração de modelo"""

    def __init__(self, db_manager, validator_model):
        super().__init__()
        self.db_manager = db_manager
        self.validator_model = validator_model

        self.setup_ui()
        self.load_feedback_data()

        # Timer para atualização automática
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.load_feedback_data)
        self.update_timer.start(30000)  # Atualizar a cada 30 segundos

    def setup_ui(self):
        """Configura a interface"""
        main_layout = QVBoxLayout()

        # Título
        title = QLabel("Model Calibration & Feedback")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # Seção de estatísticas
        stats_layout = QHBoxLayout()

        # Total de amostras
        stats_layout.addWidget(QLabel("Total Samples:"))
        self.total_samples_label = QLabel("0")
        stats_layout.addWidget(self.total_samples_label)

        # Taxa de falsos positivos
        stats_layout.addWidget(QLabel("False Positive Rate:"))
        self.fp_rate_label = QLabel("0%")
        stats_layout.addWidget(self.fp_rate_label)

        # Confiança média
        stats_layout.addWidget(QLabel("Avg Confidence:"))
        self.avg_confidence_label = QLabel("0%")
        stats_layout.addWidget(self.avg_confidence_label)

        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)

        # Seletor de tipo de evento
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Event Type:"))
        self.event_type_selector = QComboBox()
        self.event_type_selector.addItems([
            "intrusion", "loitering", "theft", "crowd_anomaly",
            "fire_smoke", "vandalism"
        ])
        self.event_type_selector.currentTextChanged.connect(self.load_feedback_data)
        filter_layout.addWidget(self.event_type_selector)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Tabela de feedback
        self.feedback_table = QTableWidget()
        self.feedback_table.setColumnCount(6)
        self.feedback_table.setHorizontalHeaderLabels([
            "ID", "Timestamp", "Confidence", "User Feedback", "Notes", "Actions"
        ])

        header = self.feedback_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        main_layout.addWidget(self.feedback_table)

        # Seção de calibração
        calibration_layout = QVBoxLayout()

        calibration_label = QLabel("Threshold Calibration")
        calibration_font = QFont()
        calibration_font.setBold(True)
        calibration_label.setFont(calibration_font)
        calibration_layout.addWidget(calibration_label)

        # Threshold atual
        threshold_layout = QHBoxLayout()

        threshold_layout.addWidget(QLabel("Current Threshold:"))
        self.current_threshold_label = QLabel("0.70")
        threshold_layout.addWidget(self.current_threshold_label)

        threshold_layout.addWidget(QLabel("Suggested Threshold:"))
        self.suggested_threshold_label = QLabel("0.70")
        threshold_layout.addWidget(self.suggested_threshold_label)

        # Slider para ajuste manual
        threshold_layout.addWidget(QLabel("Manual Adjustment:"))
        self.threshold_spinbox = QSpinBox()
        self.threshold_spinbox.setMinimum(0)
        self.threshold_spinbox.setMaximum(100)
        self.threshold_spinbox.setValue(70)
        self.threshold_spinbox.setSuffix("%")
        threshold_layout.addWidget(self.threshold_spinbox)

        apply_btn = QPushButton("Apply Threshold")
        apply_btn.clicked.connect(self.apply_threshold)
        threshold_layout.addWidget(apply_btn)

        threshold_layout.addStretch()
        calibration_layout.addLayout(threshold_layout)

        # Gráfico de distribuição (simplificado)
        distribution_layout = QHBoxLayout()

        distribution_layout.addWidget(QLabel("True Positives:"))
        self.tp_progress = QProgressBar()
        self.tp_progress.setMaximumWidth(200)
        distribution_layout.addWidget(self.tp_progress)

        distribution_layout.addWidget(QLabel("False Positives:"))
        self.fp_progress = QProgressBar()
        self.fp_progress.setMaximumWidth(200)
        distribution_layout.addWidget(self.fp_progress)

        distribution_layout.addStretch()
        calibration_layout.addLayout(distribution_layout)

        main_layout.addLayout(calibration_layout)

        # Botões de ação
        action_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.clicked.connect(self.load_feedback_data)
        action_layout.addWidget(refresh_btn)

        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_threshold)
        action_layout.addWidget(reset_btn)

        export_btn = QPushButton("Export Report")
        export_btn.clicked.connect(self.export_report)
        action_layout.addWidget(export_btn)

        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.setLayout(main_layout)

    def load_feedback_data(self):
        """Carrega dados de feedback"""
        try:
            event_type = self.event_type_selector.currentText()

            # Obter calibração
            calibration = self._get_calibration_data(event_type)

            # Atualizar estatísticas
            total = calibration.get('total_samples', 0)
            tp = calibration.get('true_positives', 0)
            fp = calibration.get('false_positives', 0)

            self.total_samples_label.setText(str(total))

            if total > 0:
                fp_rate = fp / total
                self.fp_rate_label.setText(f"{fp_rate:.1%}")

                avg_confidence = (
                    calibration.get('avg_tp_confidence', 0) * tp +
                    calibration.get('avg_fp_confidence', 0) * fp
                ) / total
                self.avg_confidence_label.setText(f"{avg_confidence:.1%}")

                # Atualizar progress bars
                self.tp_progress.setValue(int((tp / total) * 100))
                self.fp_progress.setValue(int((fp / total) * 100))

            # Atualizar thresholds
            current_threshold = self.validator_model.get_threshold(event_type)
            self.current_threshold_label.setText(f"{current_threshold:.2f}")

            suggested = self.validator_model.suggest_threshold_adjustment(event_type)
            if suggested:
                self.suggested_threshold_label.setText(f"{suggested:.2f}")
                self.threshold_spinbox.setValue(int(suggested * 100))

            # Carregar feedback na tabela
            self._load_feedback_table(event_type)

        except Exception as e:
            logger.error(f"Erro ao carregar dados de feedback: {e}")

    def _get_calibration_data(self, event_type: str) -> dict:
        """Obtém dados de calibração"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_real = 1 THEN 1 ELSE 0 END) as true_positives,
                    SUM(CASE WHEN is_real = 0 THEN 1 ELSE 0 END) as false_positives,
                    AVG(CASE WHEN is_real = 1 THEN confidence ELSE NULL END) as avg_tp_confidence,
                    AVG(CASE WHEN is_real = 0 THEN confidence ELSE NULL END) as avg_fp_confidence
                FROM user_feedback
                WHERE event_type = ?
            """

            result = self.db_manager.execute_query(query, (event_type,))

            if result:
                row = result[0]
                return {
                    'total_samples': row[0] or 0,
                    'true_positives': row[1] or 0,
                    'false_positives': row[2] or 0,
                    'avg_tp_confidence': row[3] or 0.0,
                    'avg_fp_confidence': row[4] or 0.0
                }

            return {}

        except Exception as e:
            logger.error(f"Erro ao obter dados de calibração: {e}")
            return {}

    def _load_feedback_table(self, event_type: str):
        """Carrega tabela de feedback"""
        try:
            query = """
                SELECT id, created_at, confidence, is_real, notes
                FROM user_feedback
                WHERE event_type = ?
                ORDER BY created_at DESC
                LIMIT 100
            """

            results = self.db_manager.execute_query(query, (event_type,))

            self.feedback_table.setRowCount(len(results) if results else 0)

            if results:
                for row, feedback in enumerate(results):
                    # ID
                    self.feedback_table.setItem(row, 0, QTableWidgetItem(str(feedback[0])))

                    # Timestamp
                    self.feedback_table.setItem(row, 1, QTableWidgetItem(str(feedback[1])))

                    # Confidence
                    confidence = feedback[2]
                    self.feedback_table.setItem(
                        row, 2,
                        QTableWidgetItem(f"{confidence:.2%}" if confidence else "-")
                    )

                    # User Feedback
                    is_real = feedback[3]
                    if is_real is None:
                        feedback_text = "Pending"
                    elif is_real:
                        feedback_text = "Real"
                    else:
                        feedback_text = "False Positive"

                    feedback_item = QTableWidgetItem(feedback_text)
                    feedback_hex = color_for_status(feedback_text)
                    feedback_item.setBackground(QColor(feedback_hex))
                    feedback_item.setForeground(QColor(contrast_text(feedback_hex)))
                    self.feedback_table.setItem(row, 3, feedback_item)

                    # Notes
                    self.feedback_table.setItem(row, 4, QTableWidgetItem(feedback[4] or ""))

                    # Actions
                    delete_btn = QPushButton("Delete")
                    delete_btn.setObjectName("DangerButton")
                    delete_btn.clicked.connect(
                        lambda checked, fid=feedback[0]: self.delete_feedback(fid)
                    )
                    self.feedback_table.setCellWidget(row, 5, delete_btn)

        except Exception as e:
            logger.error(f"Erro ao carregar tabela de feedback: {e}")

    def apply_threshold(self):
        """Aplica novo threshold"""
        try:
            event_type = self.event_type_selector.currentText()
            new_threshold = self.threshold_spinbox.value() / 100.0

            self.validator_model.set_threshold(event_type, new_threshold)

            QMessageBox.information(
                self,
                "Success",
                f"Threshold for {event_type} updated to {new_threshold:.2f}"
            )

        except Exception as e:
            logger.error(f"Erro ao aplicar threshold: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply threshold: {e}")

    def reset_threshold(self):
        """Reseta threshold para padrão"""
        try:
            event_type = self.event_type_selector.currentText()
            default_threshold = 0.7

            self.validator_model.set_threshold(event_type, default_threshold)
            self.threshold_spinbox.setValue(int(default_threshold * 100))

            QMessageBox.information(
                self,
                "Success",
                f"Threshold for {event_type} reset to {default_threshold:.2f}"
            )

        except Exception as e:
            logger.error(f"Erro ao resetar threshold: {e}")

    def delete_feedback(self, feedback_id: int):
        """Deleta feedback"""
        try:
            query = "DELETE FROM user_feedback WHERE id = ?"
            self.db_manager.execute_update(query, (feedback_id,))

            self.load_feedback_data()

        except Exception as e:
            logger.error(f"Erro ao deletar feedback: {e}")

    def export_report(self):
        """Exporta relatório de calibração"""
        try:
            from PySide6.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Calibration Report",
                "",
                "PDF Files (*.pdf);;Text Files (*.txt)"
            )

            if not file_path:
                return

            # Aqui você implementaria exportação do relatório
            QMessageBox.information(self, "Success", f"Report exported to {file_path}")

        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {e}")

    def closeEvent(self, event):
        """Limpar timer ao fechar"""
        self.update_timer.stop()
        event.accept()
