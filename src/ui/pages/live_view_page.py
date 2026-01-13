"""
Live camera view with multi-camera grid detection.
"""
import logging
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame, QGridLayout
)

from ultralytics import YOLO
from config.config import SUSPICIOUS_CLASSES, HIGH_RISK_CLASSES, CONFIDENCE_THRESHOLD

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
            
            frame_count = 0
            suspicious_count = 0  # Track suspicious detections
            
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
                
                # Detectar objetos com threshold configurado
                results = self.detector(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
                detections = []
                has_high_risk = False
                
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        cls_name = self.detector.names[cls_id]
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        is_suspicious = cls_name in SUSPICIOUS_CLASSES
                        is_high_risk = cls_name in HIGH_RISK_CLASSES
                        
                        if is_suspicious:
                            suspicious_count += 1
                            if is_high_risk:
                                has_high_risk = True
                                logger.warning(f"[ALERT] High risk object detected: {cls_name} (conf: {conf:.2f})")
                        
                        detections.append({
                            'class_name': cls_name,
                            'confidence': conf,
                            'bbox': (x1, y1, x2, y2),
                            'suspicious': is_suspicious,
                            'high_risk': is_high_risk
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
    """Live view page for multi-camera grid streaming."""

    def __init__(self, db_manager, auth_manager, camera_manager, engine_manager):
        super().__init__()
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.camera_manager = camera_manager
        self.engine_manager = engine_manager
        
        # Multi-camera grid streaming
        self.video_threads = {}  # camera_id -> VideoThread
        self.video_labels = {}   # camera_id -> QLabel
        self.camera_name_labels = {}  # camera_id -> QLabel
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
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(4)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Criar células
        for i in range(self.grid_size):
            row = i // cols
            col = i % cols
            
            # Frame para cada câmera
            camera_frame = QFrame()
            camera_frame.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")
            camera_layout = QVBoxLayout()
            camera_layout.setContentsMargins(2, 2, 2, 2)
            camera_layout.setSpacing(2)
            
            # Label para nome da câmera
            name_label = QLabel(f"Camera {i+1}")
            name_label.setStyleSheet("color: #fff; font-size: 11px; background: transparent; border: none;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            camera_layout.addWidget(name_label)
            self.camera_name_labels[i] = name_label
            
            # Label para vídeo
            video_label = QLabel("No signal")
            video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            video_label.setStyleSheet("background-color: #0a0a0a; color: #666; border: none;")
            video_label.setMinimumSize(160, 120)
            camera_layout.addWidget(video_label, 1)
            self.video_labels[i] = video_label
            
            camera_frame.setLayout(camera_layout)
            self.grid_layout.addWidget(camera_frame, row, col)
        
        self.grid_container.setLayout(self.grid_layout)
    
    def on_grid_size_changed(self):
        """Muda tamanho do grid"""
        self.stop_all_cameras()
        self.grid_size = self.grid_selector.currentData()
        self.create_grid()
    
    def start_all_cameras(self):
        """Inicia todas as câmeras disponíveis"""
        user_id = self.auth_manager.get_user_id()
        if not user_id:
            self.status_label.setText("Please login first")
            return
        
        # Obter câmeras do usuário
        cameras = self.db_manager.get_cameras(user_id)
        if not cameras:
            self.status_label.setText("No cameras configured")
            return
        
        # Limitar ao tamanho do grid
        cameras = cameras[:self.grid_size]
        
        self.status_label.setText(f"Starting {len(cameras)} cameras...")
        
        # Iniciar thread para cada câmera
        for idx, camera in enumerate(cameras):
            camera_id = camera['id']
            camera_name = camera['name']
            rtsp_url = camera['rtsp_url']
            
            # Atualizar label
            self.camera_name_labels[idx].setText(camera_name)
            self.video_labels[idx].setText("Connecting...")
            
            # Criar e iniciar thread
            thread = VideoThread(rtsp_url)
            thread.frame_ready.connect(lambda frame, dets, idx=idx: self.update_grid_frame(idx, frame, dets))
            thread.error_signal.connect(lambda error, idx=idx: self.on_grid_error(idx, error))
            thread.start()
            
            self.video_threads[idx] = thread
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
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
        has_high_risk = False
        suspicious_items = []
        
        # Desenhar bounding boxes com cores por nível de risco
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cls_name = det['class_name']
            conf = det['confidence']
            is_suspicious = det['suspicious']
            is_high_risk = det.get('high_risk', False)
            
            # Cores: Vermelho (alto risco), Laranja (suspeito), Verde (normal)
            if is_high_risk:
                color = (0, 0, 255)  # Vermelho brilhante
                thickness = 2
                has_high_risk = True
                suspicious_items.append(f"{cls_name}!")
            elif is_suspicious:
                color = (0, 165, 255)  # Laranja
                thickness = 2
                suspicious_items.append(cls_name)
            else:
                color = (0, 255, 0)  # Verde
                thickness = 1
            
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, thickness)
            
            # Label menor para grid com indicador de risco
            prefix = "⚠" if is_high_risk else ("!" if is_suspicious else "")
            label = f"{prefix}{cls_name[:4]} {conf:.2f}"
            
            # Fundo para texto
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            cv2.rectangle(display_frame, (x1, y1 - text_size[1] - 4), 
                         (x1 + text_size[0], y1), color, -1)
            cv2.putText(display_frame, label, (x1, y1 - 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Atualizar nome da câmera com status
        if grid_idx in self.camera_name_labels:
            camera_name = self.camera_name_labels[grid_idx].text().split(" - ")[0]
            if has_high_risk:
                self.camera_name_labels[grid_idx].setText(f"{camera_name} - ⚠ HIGH RISK!")
                self.camera_name_labels[grid_idx].setStyleSheet("color: #ff0000; font-weight: bold;")
            elif suspicious_items:
                items_str = ", ".join(suspicious_items[:2])
                self.camera_name_labels[grid_idx].setText(f"{camera_name} - Suspicious: {items_str}")
                self.camera_name_labels[grid_idx].setStyleSheet("color: #ffa500; font-weight: bold;")
            else:
                self.camera_name_labels[grid_idx].setText(camera_name)
                self.camera_name_labels[grid_idx].setStyleSheet("color: #00ff00;")
        
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
        self.start_all_cameras()
    
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
