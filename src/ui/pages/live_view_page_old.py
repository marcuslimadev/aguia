"""
Live camera view with detection overlays.
"""
import logging
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame
)

from ultralytics import YOLO
from config.ui_theme import PALETTE

logger = logging.getLogger(__name__)


class VideoThread(QThread):
    """Thread para processar video RTSP com YOLO"""
    frame_ready = Signal(np.ndarray, list)  # frame, detections
    error_signal = Signal(str)
    
    def __init__(self, rtsp_url):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.running = True
        self.detector = None
    
    def run(self):
        """Processa video"""
        cap = None
        try:
            # Inicializar YOLO
            logger.info("Loading YOLO model...")
            self.detector = YOLO("yolov8m.pt")
            
            # Abrir stream RTSP com timeout de 10s
            logger.info(f"Opening RTSP stream: {self.rtsp_url}")
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10s timeout
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)  # 10s read timeout
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
            
            if not cap.isOpened():
                self.error_signal.emit("Failed to open RTSP stream (timeout or connection error)")
                return
            
            logger.info("RTSP stream opened successfully")
            
            # Classes suspeitas para detecção de shoplifting
            suspicious_classes = ["person", "backpack", "handbag", "suitcase", "knife", "scissors", "bottle", "cup"]
            
            frame_count = 0
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    if not self.running:
                        break  # Stopped intentionally
                    self.error_signal.emit("Lost connection to camera")
                    break
                
                frame_count += 1
                
                # Frame skipping - processar 1 a cada 3 frames (melhor performance)
                if frame_count % 3 != 0:
                    self.msleep(33)
                    continue
                
                # Detectar objetos
                results = self.detector(frame, conf=0.5, verbose=False)
                detections = []
                
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        cls_name = self.detector.names[cls_id]
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        detections.append({
                            'class_name': cls_name,
                            'confidence': conf,
                            'bbox': (x1, y1, x2, y2),
                            'suspicious': cls_name in suspicious_classes
                        })
                
                self.frame_ready.emit(frame, detections)
                self.msleep(33)  # ~30 FPS
            
            logger.info(f"VideoThread stopped after {frame_count} frames")
            
        except Exception as e:
            logger.error(f"VideoThread error: {e}", exc_info=True)
            self.error_signal.emit(str(e))
        finally:
            if cap is not None:
                cap.release()
                logger.info("RTSP capture released")
    
    def stop(self):
        """Para thread"""
        self.running = False


class LiveViewPage(QWidget):
    """Live view page for camera streams."""

    def __init__(self, db_manager, auth_manager, camera_manager, engine_manager):
        super().__init__()
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.camera_manager = camera_manager
        self.engine_manager = engine_manager

        self.current_camera_id: Optional[int] = None
        self._last_frame_id = -1
        
        # Multi-camera grid streaming
        self.video_threads = {}  # camera_id -> VideoThread
        self.video_labels = {}   # camera_id -> QLabel
        self.camera_name_labels = {}  # camera_id -> QLabel
        self.active_cameras = []  # List of (camera_id, name, rtsp_url)
        self.grid_size = 6  # Default: 6 cameras

        self.setup_ui()

    def setup_ui(self):
        """Builds the UI."""
        main_layout = QVBoxLayout()

        # Header with controls
        header_frame = QFrame()
        header_frame.setObjectName("LiveViewHeader")
        header_layout = QHBoxLayout()
        
        # Grid size selector
        header_layout.addWidget(QLabel("Layout:"))
        self.grid_selector = QComboBox()
        self.grid_selector.addItem("6 cameras (2×3)", 6)
        self.grid_selector.addItem("12 cameras (3×4)", 12)
        self.grid_selector.addItem("24 cameras (4×6)", 24)
        self.grid_selector.currentIndexChanged.connect(self.on_grid_size_changed)
        header_layout.addWidget(self.grid_selector)
        
        header_layout.addStretch()
        
        # Start/Stop buttons
        self.start_btn = QPushButton("Start All Cameras")
        self.start_btn.clicked.connect(self.start_all_cameras)
        header_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop All")
        self.stop_btn.clicked.connect(self.stop_all_cameras)
        self.stop_btn.setEnabled(False)
        header_layout.addWidget(self.stop_btn)

        header_frame.setLayout(header_layout)
        main_layout.addWidget(header_frame)

        # Grid container
        self.grid_container = QWidget()
        self.grid_layout = None
        main_layout.addWidget(self.grid_container, 1)
        
        # Create initial grid
        self.create_grid()

        # Status
        self.status_label = QLabel("Ready - Click 'Start All Cameras' to begin")
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)
    
    def create_grid(self):
        """Cria grid de visualização baseado no tamanho selecionado"""
        # Limpar grid antigo
        if self.grid_layout:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(self.grid_layout)  # Remove old layout
        
        self.video_labels.clear()
        self.camera_name_labels.clear()
        
        # Determinar dimensões do grid
        if self.grid_size == 6:
            rows, cols = 2, 3
        elif self.grid_size == 12:
            rows, cols = 3, 4
        else:  # 24
            rows, cols = 4, 6
        
        # Criar novo grid
        from PySide6.QtWidgets import QGridLayout
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(4)

        self.status_label.setText(f"Streaming {len(cameras)} cameras")
        logger.info(f"Started {len(cameras)} camera streams")
    
    def stop_all_cameras(self):
        """Para todas as câmeras"""
        for idx, thread in list(self.video_threads.items()):
            if thread.isRunning():
                thread.stop()
                if not thread.wait(2000):
                    thread.terminate()
                    thread.wait(1000)
            thread.deleteLater()
        
        self.video_threads.clear()
        
        # Reset labels
        for idx, label in self.video_labels.items():
            label.clear()
            label.setText("No signal")
        
        for idx, label in self.camera_name_labels.items():
            label.setText(f"Camera {idx+1}")
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("All cameras stopped")
        logger.info("Stopped all camera streams")
    
    def update_grid_frame(self, grid_idx: int, frame: np.ndarray, detections: list):
        """Atualiza frame em célula do grid"""
        if grid_idx not in self.video_labels:
            return
        
        display_frame = frame.copy()
        
        # Desenhar bounding boxes (menores para grid)
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cls_name = det['class_name']
            conf = det['confidence']
            is_suspicious = det['suspicious']
            
            color = (0, 0, 255) if is_suspicious else (0, 255, 0)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 1)
            
            # Label menor para grid
            label = f"{cls_name[:3]} {conf:.1f}"
            cv2.putText(display_frame, label, (x1, max(y1 - 5, 10)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        
        # Converter e exibir
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimg)
        
        scaled = pixmap.scaled(
            self.video_labels[grid_idx].size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation  # Faster for grid
        )
        self.video_labels[grid_idx].setPixmap(scaled)
    
    def on_grid_error(self, grid_idx: int, error_msg: str):
        """Handle erro em câmera do grid"""
        if grid_idx in self.video_labels:
            self.video_labels[grid_idx].setText(f"Error:\n{error_msg[:30]}")
        logger.error(f"Grid camera {grid_idx} error: {error_msg}")
    
    def start_stream(self, rtsp_url: str, camera_name: str):
        """Método legado - agora usa grid multi-camera"""
        # Auto-start com a câmera selecionada
        self.start_all_cameras(m_error)
        self.video_thread.start()
        
        self.stop_btn.setEnabled(True)
        logger.info(f"Started live stream for {camera_name}")
    
    def stop_stream(self):
        """Para stream ativo"""
        if self.video_thread:
            if self.video_thread.isRunning():
                logger.info("Stopping video thread...")
                self.video_thread.stop()
                if not self.video_thread.wait(3000):  # Wait 3s
                    logger.warning("Video thread did not stop gracefully, terminating...")
                    self.video_thread.terminate()
                    self.video_thread.wait(1000)
            self.video_thread.deleteLater()
            self.video_thread = None
            logger.info("Video thread stopped")
        
        self.current_rtsp_url = None
        self.current_camera_name = None
        self.camera_name_label.setText("No camera")
        self.video_label.setText("No stream active")
        self.status_label.setText("Stopped")
        self.alert_label.setText("")
        self.stop_btn.setEnabled(False)
    
    def update_live_frame(self, frame: np.ndarray, detections: list):
        """Atualiza frame com detecções"""
        display_frame = frame.copy()
        
        # Desenhar bounding boxes
        suspicious_detected = False
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cls_name = det['class_name']
            conf = det['confidence']
            is_suspicious = det['suspicious']
            
            # Cor: vermelho se suspeito, verde caso contrário
            color = (0, 0, 255) if is_suspicious else (0, 255, 0)
            
            # Desenhar bbox
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"{cls_name} {conf:.2f}"
            cv2.putText(display_frame, label, (x1, max(y1 - 10, 10)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            if is_suspicious:
                suspicious_detected = True
        
        # Atualizar alerta
        if suspicious_detected:
            self.alert_label.setText("⚠ SUSPICIOUS OBJECT DETECTED")
        else:
            self.alert_label.setText("")
        
        # Converter BGR para RGB
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # Criar QImage e QPixmap
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimg)
        
        # Escalar mantendo aspect ratio
        scaled = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled)
        self.status_label.setText(f"Live - Detections: {len(detections)}")
    
    def on_stream_error(self, error_msg: str):
        """Handle stream error"""
        logger.error(f"Stream error: {error_msg}")
        self.video_label.setText(f"Stream error: {error_msg}")
        self.status_label.setText("Error")
        self.stop_btn.setEnabled(False)
    
    def refresh(self):
        """Refresh - not used for direct RTSP streaming"""
        pass

    def showEvent(self, event):
        super().showEvent(event)
        # Not used for direct RTSP streaming

    def hideEvent(self, event):
        super().hideEvent(event)
        # Stop all streams when page is hidden
        self.stop_all_cameras()
