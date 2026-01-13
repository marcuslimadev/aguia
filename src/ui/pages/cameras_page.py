"""
UI pages for cameras, zones, and settings.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QTextEdit, QTabWidget, QCheckBox, QFileDialog, QApplication, QDialog
)
from PySide6.QtGui import QFont, QColor, QImage, QPixmap
from PySide6.QtCore import QTimer, QThread, Signal, Qt
import cv2
import numpy as np

from pathlib import Path

from config.config import APP_DATA_DIR
from config.ui_theme import color_for_severity, color_for_status, contrast_text

logger = logging.getLogger(__name__)


class VideoThread(QThread):
    """Thread para capturar frames de vídeo RTSP com detecção YOLO"""
    frame_ready = Signal(np.ndarray, list)  # frame, detections
    error_occurred = Signal(str)
    
    def __init__(self, rtsp_url):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.running = True
        self.detector = None
        
    def run(self):
        # Inicializar detector YOLO
        try:
            from ultralytics import YOLO
            self.detector = YOLO("yolov8m.pt")
            logger.info("✓ YOLO detector initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize YOLO: {e}")
            self.detector = None
        
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            self.error_occurred.emit("Failed to open stream")
            return
        
        # Classes suspeitas para alertar
        suspicious_classes = ["person", "knife", "scissors", "backpack", "handbag", "suitcase"]
        
        while self.running:
            ret, frame = cap.read()
            if ret and frame is not None:
                detections = []
                
                # Processar com YOLO
                if self.detector:
                    try:
                        results = self.detector(frame, conf=0.4, verbose=False)
                        for result in results:
                            for box in result.boxes:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                conf = float(box.conf[0])
                                class_id = int(box.cls[0])
                                class_name = result.names[class_id]
                                
                                detections.append({
                                    'bbox': (x1, y1, x2, y2),
                                    'class': class_name,
                                    'conf': conf,
                                    'suspicious': class_name in suspicious_classes
                                })
                    except Exception as e:
                        logger.error(f"Detection error: {e}")
                
                self.frame_ready.emit(frame, detections)
            else:
                self.error_occurred.emit("Lost connection")
                break
            
            self.msleep(30)  # ~30 FPS
        
        cap.release()
    
    def stop(self):
        self.running = False
        self.wait()


class LiveViewDialog(QDialog):
    """Janela para visualização ao vivo"""
    
    def __init__(self, rtsp_url, camera_name, parent=None):
        super().__init__(parent)
        self.rtsp_url = rtsp_url
        self.camera_name = camera_name
        self.video_thread = None
        self.setup_ui()
        self.start_stream()
    
    def setup_ui(self):
        self.setWindowTitle(f"Live View - {self.camera_name}")
        self.setMinimumSize(1024, 768)
        
        layout = QVBoxLayout()
        
        # Label para exibir vídeo
        self.video_label = QLabel("Loading stream...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("background-color: #000000; color: #ffffff;")
        layout.addWidget(self.video_label)
        
        # Status e alertas
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel(f"Connecting to {self.rtsp_url}...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        status_layout.addWidget(self.status_label)
        
        self.alert_label = QLabel("")
        self.alert_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.alert_label.setStyleSheet("color: #ff0000; font-weight: bold;")
        status_layout.addWidget(self.alert_label)
        
        layout.addLayout(status_layout)
        
        # Botão Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def start_stream(self):
        """Inicia thread de captura"""
        self.video_thread = VideoThread(self.rtsp_url)
        self.video_thread.frame_ready.connect(self.update_frame)
        self.video_thread.error_occurred.connect(self.handle_error)
        self.video_thread.start()
    
    def update_frame(self, frame, detections):
        """Atualiza frame no QLabel com bounding boxes"""
        try:
            # Fazer cópia para desenhar
            display_frame = frame.copy()
            
            # Desenhar detecções
            suspicious_count = 0
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                class_name = det['class']
                conf = det['conf']
                is_suspicious = det['suspicious']
                
                # Cor: vermelho se suspeito, verde se normal
                color = (0, 0, 255) if is_suspicious else (0, 255, 0)
                
                # Desenhar bbox
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                
                # Label
                label = f"{class_name} {conf:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(display_frame, (x1, y1 - label_size[1] - 10), 
                             (x1 + label_size[0], y1), color, -1)
                cv2.putText(display_frame, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                if is_suspicious:
                    suspicious_count += 1
            
            # Converter BGR para RGB
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            # Criar QImage
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Redimensionar mantendo aspecto
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
            
            # Atualizar status
            self.status_label.setText(f"Live - {w}x{h} @ 30fps | Detections: {len(detections)}")
            
            # Alertas
            if suspicious_count > 0:
                self.alert_label.setText(f"⚠ {suspicious_count} suspicious object(s) detected!")
            else:
                self.alert_label.setText("")
            
        except Exception as e:
            logger.error(f"Error updating frame: {e}")
    
    def handle_error(self, error_msg):
        """Trata erros de stream"""
        self.video_label.setText(f"✗ Stream Error\n\n{error_msg}")
        self.status_label.setText("Disconnected")
    
    def closeEvent(self, event):
        """Para thread ao fechar"""
        if self.video_thread:
            self.video_thread.stop()
        event.accept()


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
        
        # Status label for inline feedback (replaces QMessageBox)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(30)
        self.status_label.hide()
        main_layout.addWidget(self.status_label)

        # Camera form (RTSP Direct - simplified)
        form_layout = QVBoxLayout()
        
        form_layout.addWidget(QLabel("Camera Name:"))
        self.camera_name = QLineEdit()
        self.camera_name.setPlaceholderText("e.g., Front Door, Parking Lot, Store Entrance")
        form_layout.addWidget(self.camera_name)

        form_layout.addWidget(QLabel("RTSP URL:"))
        self.rtsp_url = QLineEdit()
        self.rtsp_url.setPlaceholderText("e.g., rtsp://192.168.0.20:8080/h264.sdp")
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
        self.cameras_table.setColumnCount(6)
        self.cameras_table.setHorizontalHeaderLabels(
            ["ID", "Name", "RTSP URL", "Status", "Actions", "View"]
        )
        self.cameras_table.setColumnWidth(0, 50)   # ID
        self.cameras_table.setColumnWidth(1, 150)  # Name
        self.cameras_table.setColumnWidth(2, 280)  # RTSP URL
        self.cameras_table.setColumnWidth(3, 80)   # Status
        self.cameras_table.setColumnWidth(4, 150)  # Actions
        self.cameras_table.setColumnWidth(5, 100)  # View
        main_layout.addWidget(self.cameras_table)

        main_layout.addStretch()
        self.setLayout(main_layout)
    
    def show_status(self, message: str, status_type: str = "info", duration: int = 5000):
        """Show inline status message instead of QMessageBox"""
        self.status_label.setText(message)
        self.status_label.setProperty("feedbackType", status_type)
        self.status_label.setStyleSheet(self.status_label.styleSheet())  # Refresh style
        self.status_label.show()
        
        # Auto-hide after duration
        if duration > 0:
            QTimer.singleShot(duration, self.status_label.hide)

    def add_camera(self):
        name = self.camera_name.text().strip()
        rtsp_url = self.rtsp_url.text().strip()

        user_id = self.auth_manager.get_user_id()
        if not user_id:
            self.show_status("✗ You must be logged in to add cameras", "error")
            return

        if not name or not rtsp_url:
            self.show_status("✗ Please fill all fields", "error")
            return

        if not rtsp_url.startswith("rtsp://"):
            self.show_status("✗ RTSP URL must start with rtsp://", "error")
            return

        try:
            camera_id = self.db_manager.add_camera(user_id, name, rtsp_url)
            self.camera_manager.add_camera_processor(
                camera_id,
                rtsp_url,
                start_processor=self.engine_manager.is_running
            )
            self.show_status(f"✓ Camera '{name}' added successfully!", "success")
            self.camera_name.clear()
            self.rtsp_url.clear()
            self.refresh()
        except Exception as e:
            logger.error(f"Error adding camera: {e}")
            self.show_status(f"✗ Failed to add camera: {e}", "error")

    def add_intelbras_camera(self):
        """Add Intelbras camera via Cloud/P2P"""
        name = self.intelbras_name.text().strip()
        device_id = self.device_id.text().strip()
        device_password = self.device_password.text().strip()
        cloud_user = self.cloud_user.text().strip()
        
        user_id = self.auth_manager.get_user_id()
        if not user_id:
            self.show_status("✗ You must be logged in to add cameras", "error")
            return
        
        if not name or not device_id or not device_password:
            self.show_status("✗ Please fill Name, Device ID and Password", "error")
            return
        
        try:
            # Import Intelbras integration
            from src.ai.onvif_discovery import discover_intelbras_p2p
            
            self.show_status(f"🔍 Connecting to Intelbras device {device_id}...", "info", 0)
            QApplication.processEvents()
            
            # Try to get P2P URL from device
            rtsp_url = discover_intelbras_p2p(device_id, device_password, cloud_user)
            
            if rtsp_url:
                camera_id = self.db_manager.add_camera(user_id, name, rtsp_url)
                self.camera_manager.add_camera_processor(
                    camera_id,
                    rtsp_url,
                    start_processor=self.engine_manager.is_running
                )
                self.show_status(f"✓ Intelbras camera '{name}' added successfully!", "success")
                self.intelbras_name.clear()
                self.device_id.clear()
                self.device_password.clear()
                self.cloud_user.clear()
                self.refresh()
            else:
                self.show_status(f"✗ Could not connect to device {device_id}", "error")
                
        except Exception as e:
            logger.error(f"Error adding Intelbras camera: {e}", exc_info=True)
            self.show_status(f"✗ Failed to add Intelbras camera: {e}", "error")
    
    def discover_onvif_cameras(self):
        """Discover ONVIF cameras on network"""
        try:
            from src.ai.onvif_discovery import discover_onvif_cameras
            
            self.show_status("🔍 Scanning network for ONVIF cameras (30s timeout)...", "info", 0)
            QApplication.processEvents()
            
            cameras = discover_onvif_cameras(timeout=30)
            
            if cameras:
                msg = f"✓ Found {len(cameras)} cameras:\n"
                for cam in cameras:
                    msg += f"• {cam['name']} at {cam['ip']}\n"
                self.show_status(msg, "success", 15000)
                
                # Auto-fill first camera if available
                if cameras and not self.rtsp_url.text():
                    first = cameras[0]
                    self.camera_name.setText(first.get('name', 'ONVIF Camera'))
                    # Try to construct RTSP URL
                    ip = first.get('ip', '')
                    if ip:
                        # Standard ONVIF RTSP path
                        self.rtsp_url.setText(f"rtsp://{ip}:554/onvif1")
            else:
                self.show_status("⚠ No ONVIF cameras found on network", "warning", 10000)
                
        except Exception as e:
            logger.error(f"Error discovering ONVIF: {e}", exc_info=True)
            self.show_status(f"✗ Failed to discover cameras: {e}", "error")

    def test_connection(self):
        rtsp_url = self.rtsp_url.text().strip()
        if not rtsp_url:
            self.show_status("✗ Please enter RTSP URL", "error")
            return

        # Testar conexão RTSP real com diagnóstico detalhado
        try:
            import cv2
            import time
            
            # Feedback inline durante teste
            self.show_status("⟳ Testing RTSP connection... (up to 10 seconds)", "info", duration=0)
            QApplication.processEvents()
            
            # Configurações para melhor compatibilidade
            backends = [
                (cv2.CAP_FFMPEG, "FFmpeg"),
                (cv2.CAP_ANY, "Auto")
            ]
            
            success = False
            error_details = []
            backend_used = ""
            
            for backend, backend_name in backends:
                try:
                    logger.info(f"Tentando conectar via {backend_name}: {rtsp_url}")
                    
                    # Configurar VideoCapture com timeout e buffer mínimo
                    cap = cv2.VideoCapture(rtsp_url, backend)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    # Aguardar até 10 segundos
                    timeout = 10.0
                    start = time.time()
                    
                    while time.time() - start < timeout:
                        if cap.isOpened():
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                h, w = frame.shape[:2]
                                success = True
                                backend_used = backend_name
                                logger.info(f"✓ Conectado via {backend_name}: {w}x{h}")
                                break
                        time.sleep(0.2)
                        QApplication.processEvents()
                    
                    cap.release()
                    
                    if success:
                        break
                    else:
                        error_details.append(f"{backend_name}: timeout após {timeout}s")
                        
                except Exception as e:
                    error_details.append(f"{backend_name}: {str(e)}")
                    logger.error(f"Erro com {backend_name}: {e}")
            
            if success:
                self.show_status(
                    f"✓ Connected via {backend_used}! Resolution: {w}x{h}",
                    "success",
                    8000
                )
            else:
                # Diagnóstico detalhado
                diagnostics = "\n".join([
                    "✗ Connection failed",
                    f"URL: {rtsp_url}",
                    "",
                    "Tried:",
                ] + [f"  • {detail}" for detail in error_details] + [
                    "",
                    "Common issues:",
                    "  • Wrong port (try 554, 8080, 8554)",
                    "  • Wrong path (try /h264, /stream, /cam/realmonitor)",
                    "  • Authentication required (add user:pass@ before IP)",
                    "  • Camera not on network or firewall blocking"
                ])
                
                self.show_status(diagnostics, "error", 15000)
                logger.warning(f"RTSP test failed: {rtsp_url}")
                
        except Exception as e:
            self.show_status(f"✗ Test failed: {str(e)}", "error")
    
    def view_live(self, rtsp_url, camera_name):
        """Navega para visualização ao vivo"""
        try:
            # Obter referência ao MainWindow
            main_window = self.window()
            if not hasattr(main_window, 'live_view_page'):
                logger.error("MainWindow does not have live_view_page")
                self.show_status("✗ Live view page not available", "error")
                return
            
            # Iniciar stream na página de live view
            main_window.live_view_page.start_stream(rtsp_url, camera_name)
            
            # Navegar para a página live
            main_window.navigate_to("live")
            
        except Exception as e:
            logger.error(f"Error opening live view: {e}", exc_info=True)
            self.show_status(f"✗ Failed to open live view: {e}", "error")

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
                
                # Botões de ação (Delete)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(4)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setMaximumWidth(70)
                delete_btn.clicked.connect(lambda checked, cid=camera_id: self.delete_camera(cid))
                actions_layout.addWidget(delete_btn)
                
                actions_widget.setLayout(actions_layout)
                self.cameras_table.setCellWidget(row, 4, actions_widget)
                
                # Botão View Live
                view_btn = QPushButton("View Live")
                view_btn.setMaximumWidth(90)
                view_btn.clicked.connect(lambda checked, url=camera["rtsp_url"], name=camera["name"]: self.view_live(url, name))
                self.cameras_table.setCellWidget(row, 5, view_btn)
        except Exception as e:
            logger.error(f"Error refreshing cameras: {e}")
    
    def delete_camera(self, camera_id):
        """Deleta câmera"""
        try:
            self.db_manager.delete_camera(camera_id)
            self.camera_manager.remove_camera_processor(camera_id)
            self.show_status(f"✓ Camera deleted successfully", "success")
            self.refresh()
        except Exception as e:
            logger.error(f"Error deleting camera: {e}")
            self.show_status(f"✗ Failed to delete camera: {e}", "error")


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
                severity_hex = color_for_severity(alert.severity)
                severity_item.setBackground(QColor(severity_hex))
                severity_item.setForeground(QColor(contrast_text(severity_hex)))
                self.alerts_table.setItem(row, 2, severity_item)

                self.alerts_table.setItem(row, 3, QTableWidgetItem(alert.timestamp.isoformat()))
                status = "Acknowledged" if alert.acknowledged else "Active"
                status_item = QTableWidgetItem(status)
                status_hex = color_for_status(status)
                status_item.setBackground(QColor(status_hex))
                status_item.setForeground(QColor(contrast_text(status_hex)))
                self.alerts_table.setItem(row, 4, status_item)

                ack_btn = QPushButton("Acknowledge")
                ack_btn.setObjectName("SuccessButton")
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
        layout.addWidget(QLabel("Application Data Location:"))

        data_layout = QHBoxLayout()
        self.data_dir = QLineEdit()
        self.data_dir.setReadOnly(True)
        self.data_dir.setText(str(APP_DATA_DIR))
        data_layout.addWidget(self.data_dir)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_data_dir)
        data_layout.addWidget(browse_btn)
        layout.addLayout(data_layout)

        layout.addWidget(QLabel("Restart required to apply data directory changes."))

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
        data_dir_changed = False

        current_data_dir = self.app_settings.get("data_dir", str(APP_DATA_DIR))
        new_data_dir = self.data_dir.text().strip()
        if not new_data_dir:
            new_data_dir = current_data_dir
        if new_data_dir != current_data_dir:
            try:
                Path(new_data_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create data directory: {e}")
                return
            self.app_settings.set("data_dir", new_data_dir)
            data_dir_changed = True

        if silent_mode and not enable_tray:
            silent_mode = False
            self.silent_mode_checkbox.setChecked(False)
            QMessageBox.warning(self, "Warning", "Silent mode requires tray enabled")

        self.app_settings.set("enable_tray", enable_tray)
        self.app_settings.set("silent_mode", silent_mode)
        self.app_settings.set("auto_start_engine", auto_start)
        self.app_settings.save()

        if data_dir_changed:
            message = "System settings saved. Restart required to apply data directory changes."
        else:
            message = "System settings saved. Restart may be required to apply changes."

        QMessageBox.information(
            self,
            "Success",
            message
        )

    def browse_data_dir(self):
        current = self.data_dir.text().strip() or str(APP_DATA_DIR)
        selected = QFileDialog.getExistingDirectory(
            self,
            "Select Data Directory",
            current
        )
        if selected:
            self.data_dir.setText(selected)

    def open_store(self):
        import webbrowser
        webbrowser.open("https://www.microsoft.com/store/apps/")

    def refresh(self):
        if hasattr(self, "enable_tray_checkbox"):
            self.enable_tray_checkbox.setChecked(self.app_settings.get("enable_tray", True))
            self.silent_mode_checkbox.setChecked(self.app_settings.get("silent_mode", False))
            self.auto_start_engine_checkbox.setChecked(self.app_settings.get("auto_start_engine", True))
            if hasattr(self, "data_dir"):
                current_data_dir = self.app_settings.get("data_dir", str(APP_DATA_DIR))
                self.data_dir.setText(str(current_data_dir))

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
