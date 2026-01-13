"""
Gerenciador de câmeras e processamento de vídeo
"""
import logging
import threading
from typing import Dict, List, Optional
from src.ai.video_processor import VideoProcessor

logger = logging.getLogger(__name__)


class CameraManager:
    """Gerencia múltiplas câmeras e seus processadores de vídeo"""

    def __init__(self, db_manager, alert_manager):
        self.db = db_manager
        self.alert_manager = alert_manager
        self.processors: Dict[int, VideoProcessor] = {}
        self.lock = threading.Lock()

    def add_camera_processor(self, camera_id: int, rtsp_url: str, start_processor: bool = True) -> bool:
        """Adiciona um processador de vídeo para uma câmera"""
        try:
            with self.lock:
                if camera_id in self.processors:
                    logger.warning(f"Processador já existe para câmera {camera_id}")
                    return False

                processor = VideoProcessor(rtsp_url, camera_id)
                if start_processor:
                    processor.start()
                self.processors[camera_id] = processor

                logger.info(f"Processador adicionado para câmera {camera_id}")
                return True

        except Exception as e:
            logger.error(f"Erro ao adicionar processador de câmera: {e}")
            return False

    def remove_camera_processor(self, camera_id: int) -> bool:
        """Remove o processador de vídeo de uma câmera"""
        try:
            with self.lock:
                if camera_id not in self.processors:
                    logger.warning(f"Processador não encontrado para câmera {camera_id}")
                    return False

                processor = self.processors[camera_id]
                processor.stop()
                del self.processors[camera_id]

                logger.info(f"Processador removido para câmera {camera_id}")
                return True

        except Exception as e:
            logger.error(f"Erro ao remover processador de câmera: {e}")
            return False

    def get_processor(self, camera_id: int) -> Optional[VideoProcessor]:
        """Obtém o processador de uma câmera"""
        with self.lock:
            return self.processors.get(camera_id)

    def get_all_processors(self) -> List[VideoProcessor]:
        """Obtém todos os processadores"""
        with self.lock:
            return list(self.processors.values())

    def process_detections(self, camera_id: int, frame):
        """Processa detecções de uma câmera"""
        try:
            processor = self.get_processor(camera_id)
            if not processor:
                return

            processed_frame = processor.process_frame(frame)

            for detection in processed_frame.detections:
                logger.debug(
                    f"Detecção: {detection.class_name} "
                    f"({detection.confidence:.2f}) em câmera {camera_id}"
                )

        except Exception as e:
            logger.error(f"Erro ao processar detecções: {e}")

    def start_all_processors(self):
        """Inicia todos os processadores"""
        with self.lock:
            for processor in self.processors.values():
                if not processor.is_running:
                    processor.start()
            logger.info(f"Iniciados {len(self.processors)} processadores")

    def stop_all_processors(self):
        """Para todos os processadores"""
        with self.lock:
            for processor in self.processors.values():
                processor.stop()
            logger.info(f"Parados {len(self.processors)} processadores")

    def get_camera_status(self, camera_id: int) -> dict:
        """Obtém o status de uma câmera"""
        try:
            processor = self.get_processor(camera_id)
            if not processor:
                return {'status': 'offline', 'frames_processed': 0}

            return {
                'status': 'online' if processor.is_running else 'offline',
                'frames_processed': processor.frame_id,
                'queue_size': processor.frame_queue.qsize()
            }

        except Exception as e:
            logger.error(f"Erro ao obter status da câmera: {e}")
            return {'status': 'error'}

    def get_all_camera_status(self) -> Dict[int, dict]:
        """Obtém o status de todas as câmeras"""
        status = {}
        for camera_id in self.processors.keys():
            status[camera_id] = self.get_camera_status(camera_id)
        return status


    def load_cameras_for_user(self, user_id: int, start_processors: bool = True) -> int:
        """Carrega cameras do banco e cria processadores"""
        cameras = self.db.get_cameras(user_id)
        added = 0
        for camera in cameras:
            if self.add_camera_processor(camera["id"], camera["rtsp_url"], start_processor=start_processors):
                added += 1
        return added

    def clear_processors(self):
        """Para e remove todos os processadores"""
        with self.lock:
            for camera_id in list(self.processors.keys()):
                processor = self.processors[camera_id]
                processor.stop()
                del self.processors[camera_id]
