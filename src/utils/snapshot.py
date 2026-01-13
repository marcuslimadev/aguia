"""
Utilitários para captura e processamento de snapshots
"""
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Gerencia captura e armazenamento de snapshots"""

    def __init__(self, snapshots_dir: Path):
        self.snapshots_dir = snapshots_dir
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, frame: np.ndarray, alert_id: int, quality: int = 85) -> Optional[str]:
        """
        Salva um snapshot de um frame
        Retorna o caminho do arquivo
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"alert_{alert_id}_{timestamp}.jpg"
            filepath = self.snapshots_dir / filename

            # Redimensionar se necessário
            height, width = frame.shape[:2]
            if width > 1920 or height > 1080:
                scale = min(1920 / width, 1080 / height)
                frame = cv2.resize(frame, (int(width * scale), int(height * scale)))

            # Salvar com qualidade especificada
            cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            logger.info(f"Snapshot salvo: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Erro ao salvar snapshot: {e}")
            return None

    def cleanup_old_snapshots(self, days: int = 7):
        """Remove snapshots antigos"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)

            for filepath in self.snapshots_dir.glob("*.jpg"):
                if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff_time:
                    filepath.unlink()
                    logger.info(f"Snapshot antigo removido: {filepath}")

        except Exception as e:
            logger.error(f"Erro ao limpar snapshots antigos: {e}")

    def draw_detections(self, frame: np.ndarray, detections) -> np.ndarray:
        """Desenha detecções no frame"""
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            confidence = detection.confidence
            class_name = detection.class_name

            # Desenhar bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Desenhar label
            label = f"{class_name} {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Desenhar track ID se disponível
            if detection.track_id is not None:
                track_label = f"ID: {detection.track_id}"
                cv2.putText(frame, track_label, (x1, y2 + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        return frame

    def draw_zones(self, frame: np.ndarray, zones: list) -> np.ndarray:
        """Desenha zonas no frame"""
        for zone in zones:
            if hasattr(zone, 'coordinates'):
                points = zone.coordinates
                if isinstance(points, list) and len(points) > 0:
                    pts = np.array(points, np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    cv2.polylines(frame, [pts], True, (0, 0, 255), 2)

                    # Desenhar nome da zona
                    if len(points) > 0:
                        cv2.putText(frame, zone.name, tuple(points[0]),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return frame
