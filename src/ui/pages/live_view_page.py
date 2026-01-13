"""
Live camera view with detection overlays.
"""
import logging
from typing import Optional

import cv2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame, QGraphicsDropShadowEffect
)

logger = logging.getLogger(__name__)


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

        self.setup_ui()

        self.update_timer = QTimer()
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self.update_frame)

    def setup_ui(self):
        """Builds the UI."""
        main_layout = QVBoxLayout()

        header_frame = QFrame()
        header_frame.setObjectName("LiveViewHeader")
        header_shadow = QGraphicsDropShadowEffect(self)
        header_shadow.setBlurRadius(18)
        header_shadow.setOffset(0, 3)
        header_shadow.setColor(QColor("#cecece"))
        header_frame.setGraphicsEffect(header_shadow)
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Camera:"))
        self.camera_selector = QComboBox()
        self.camera_selector.currentIndexChanged.connect(self.on_camera_changed)
        header_layout.addWidget(self.camera_selector)

        self.engine_status = QLabel("Engine: stopped")
        header_layout.addWidget(self.engine_status)
        header_layout.addStretch()

        self.start_btn = QPushButton("Start Engine")
        self.start_btn.clicked.connect(self.start_engine)
        header_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Engine")
        self.stop_btn.clicked.connect(self.stop_engine)
        header_layout.addWidget(self.stop_btn)

        header_frame.setLayout(header_layout)
        main_layout.addWidget(header_frame)

        self.video_label = QLabel("No camera selected")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(420)
        self.video_label.setStyleSheet("background-color: #ffffff;")
        video_shadow = QGraphicsDropShadowEffect(self)
        video_shadow.setBlurRadius(18)
        video_shadow.setOffset(0, 3)
        video_shadow.setColor(QColor("#cecece"))
        self.video_label.setGraphicsEffect(video_shadow)
        main_layout.addWidget(self.video_label, 1)

        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

    def refresh(self):
        """Refresh camera list and UI state."""
        user_id = self.auth_manager.get_user_id()
        self.camera_selector.blockSignals(True)
        self.camera_selector.clear()
        if not user_id:
            self.camera_selector.addItem("Login required")
            self.camera_selector.setEnabled(False)
            self.current_camera_id = None
        else:
            cameras = self.db_manager.get_cameras(user_id)
            for camera in cameras:
                self.camera_selector.addItem(
                    f"{camera['name']} (ID {camera['id']})",
                    camera["id"]
                )
            self.camera_selector.setEnabled(True)
            self.current_camera_id = (
                self.camera_selector.currentData()
                if cameras else None
            )
        self.camera_selector.blockSignals(False)
        self._update_engine_state()
        self._ensure_timer()

    def on_camera_changed(self):
        """Handle camera selection changes."""
        self.current_camera_id = self.camera_selector.currentData()
        self._last_frame_id = -1
        self.update_frame()

    def start_engine(self):
        """Start processing engine."""
        if not self.engine_manager.is_running:
            self.engine_manager.start()
        self._update_engine_state()
        self._ensure_timer()

    def stop_engine(self):
        """Stop processing engine."""
        if self.engine_manager.is_running:
            self.engine_manager.stop()
        self._update_engine_state()
        self._ensure_timer()

    def _update_engine_state(self):
        state = "running" if self.engine_manager.is_running else "stopped"
        self.engine_status.setText(f"Engine: {state}")

    def _ensure_timer(self):
        if self.engine_manager.is_running and self.current_camera_id is not None:
            if not self.update_timer.isActive():
                self.update_timer.start()
        else:
            if self.update_timer.isActive():
                self.update_timer.stop()

    def update_frame(self):
        """Fetch and render the latest frame."""
        if self.current_camera_id is None:
            self.video_label.setText("No camera selected")
            return

        processor = self.camera_manager.get_processor(self.current_camera_id)
        if not processor or not processor.is_running:
            self.video_label.setText("Camera offline or engine stopped")
            return

        frame = processor.get_frame(timeout=0.01)
        if not frame or frame.raw_frame is None:
            return

        if frame.frame_id == self._last_frame_id:
            return
        self._last_frame_id = frame.frame_id

        draw = frame.raw_frame.copy()
        for det in frame.detections:
            x1, y1, x2, y2 = det.bbox
            color = (0, 91, 187)  # blue
            if det.class_name == "person":
                color = (212, 0, 0)  # red
            cv2.rectangle(draw, (x1, y1), (x2, y2), color, 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(draw, label, (x1, max(y1 - 6, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        rgb = cv2.cvtColor(draw, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled)
        self.status_label.setText(f"Frame {frame.frame_id} - Detections: {len(frame.detections)}")

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_timer()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self.update_timer.isActive():
            self.update_timer.stop()
