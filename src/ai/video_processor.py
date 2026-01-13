"""
Processador de vídeo com IA (YOLOv8)
"""
import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import threading
from queue import Queue

# Importar RtspReader e EventEngine
from src.ai.rtsp_reader import RtspReader
from src.ai.event_engine import EventEngine, EventCandidate
from src.ai.pose_estimator import PoseEstimator, PoseSequenceBuffer
from src.ai.shoplifting_detector import ShopliftingDetector
from config.config import (
    POSE_MODEL_COMPLEXITY, POSE_MIN_DETECTION_CONFIDENCE,
    SHOPLIFTING_ENABLED, SHOPLIFTING_SEQUENCE_LENGTH, SHOPLIFTING_ANOMALY_THRESHOLD
)

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Representa uma detecção de objeto"""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    track_id: Optional[int] = None
    
    @property
    def center(self) -> Tuple[int, int]:
        """Retorna centro do bbox"""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)


@dataclass
class Frame:
    """Representa um frame processado"""
    timestamp: datetime
    frame_id: int
    detections: List[Detection]
    motion_detected: bool
    events: List[EventCandidate]
    raw_frame: Optional[np.ndarray] = None


class MotionDetector:
    """Detecta movimento em frames"""

    def __init__(self, threshold: int = 30, min_area: int = 500):
        self.threshold = threshold
        self.min_area = min_area
        self.prev_gray = None

    def detect(self, frame: np.ndarray) -> Tuple[bool, np.ndarray]:
        """
        Detecta movimento no frame
        Retorna (motion_detected, diff_frame)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_gray is None:
            self.prev_gray = gray
            return False, None

        # Diferença entre frames
        frame_diff = cv2.absdiff(self.prev_gray, gray)
        thresh = cv2.threshold(frame_diff, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Encontrar contornos
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                motion_detected = True
                break

        self.prev_gray = gray
        return motion_detected, thresh


class YOLODetector:
    """Detector de objetos usando YOLO (ONNX ou Ultralytics fallback)"""

    def __init__(self, model_path: str = "yolov8m.onnx", conf_threshold: float = 0.5, use_onnx: bool = True):
        """
        Inicializa o detector YOLO
        
        Args:
            model_path: Caminho para modelo (.onnx ou .pt)
            conf_threshold: Threshold de confiança
            use_onnx: Se True, tenta usar ONNX primeiro. Se False ou ONNX falhar, usa Ultralytics
        """
        self.conf_threshold = conf_threshold
        self.model = None
        self.using_onnx = False
        
        # Tentar ONNX primeiro
        if use_onnx and model_path.endswith('.onnx'):
            try:
                from src.ai.yolo_onnx import YoloOnnxDetector
                from pathlib import Path
                from config.config import MODELS_DIR
                
                onnx_path = MODELS_DIR / model_path if not Path(model_path).is_absolute() else Path(model_path)
                
                if onnx_path.exists():
                    self.model = YoloOnnxDetector(onnx_path, conf_threshold)
                    self.using_onnx = True
                    logger.info(f"✓ Usando detector ONNX: {onnx_path}")
                else:
                    logger.warning(f"Modelo ONNX não encontrado: {onnx_path}")
                    logger.info("Tentando fallback para Ultralytics...")
                    
            except Exception as e:
                logger.warning(f"Erro ao carregar ONNX: {e}")
                logger.info("Tentando fallback para Ultralytics...")
        
        # Fallback para Ultralytics se ONNX falhar ou não for solicitado
        if self.model is None:
            try:
                from ultralytics import YOLO
                pt_model = model_path.replace('.onnx', '.pt') if model_path.endswith('.onnx') else model_path
                self.model = YOLO(pt_model)
                self.using_onnx = False
                logger.info(f"✓ Usando detector Ultralytics: {pt_model}")
            except ImportError:
                logger.error("ultralytics não está instalado e ONNX falhou")
                self.model = None

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detecta objetos no frame
        """
        if self.model is None:
            return []

        try:
            if self.using_onnx:
                # ONNX detector já retorna Detection objects
                return self.model.detect(frame)
            else:
                # Ultralytics - converter para Detection objects
                results = self.model(frame, conf=self.conf_threshold, verbose=False)
                detections = []

                for result in results:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = result.names[class_id]

                        detection = Detection(
                            class_id=class_id,
                            class_name=class_name,
                            confidence=conf,
                            bbox=(x1, y1, x2, y2)
                        )
                        detections.append(detection)

                return detections
        except Exception as e:
            logger.error(f"Erro ao detectar objetos: {e}")
            return []


class ObjectTracker:
    """Rastreia objetos entre frames usando ByteTrack"""

    def __init__(self):
        try:
            from byte_track import BYTETracker
            self.tracker = BYTETracker()
            logger.info("ByteTracker inicializado")
        except ImportError:
            logger.warning("ByteTrack não está instalado, usando rastreamento simples")
            self.tracker = None
            self.tracks = {}
            self.next_track_id = 0

    def update(self, detections: List[Detection], frame_shape: Tuple[int, int]) -> List[Detection]:
        """
        Atualiza rastreamento de objetos
        """
        if not detections:
            return []

        if self.tracker is not None:
            # Usar ByteTrack
            dets = np.array([
                [d.bbox[0], d.bbox[1], d.bbox[2], d.bbox[3], d.confidence]
                for d in detections
            ])
            tracked_objects = self.tracker.update(dets)

            for i, detection in enumerate(detections):
                if i < len(tracked_objects):
                    detection.track_id = int(tracked_objects[i][4])

        else:
            # Rastreamento simples por centroide
            for detection in detections:
                centroid = (
                    (detection.bbox[0] + detection.bbox[2]) // 2,
                    (detection.bbox[1] + detection.bbox[3]) // 2
                )

                # Encontrar track mais próximo
                min_dist = float('inf')
                closest_track_id = None

                for track_id, track_data in self.tracks.items():
                    dist = np.sqrt(
                        (centroid[0] - track_data['centroid'][0]) ** 2 +
                        (centroid[1] - track_data['centroid'][1]) ** 2
                    )
                    if dist < min_dist and dist < 50:
                        min_dist = dist
                        closest_track_id = track_id

                if closest_track_id is not None:
                    detection.track_id = closest_track_id
                    self.tracks[closest_track_id]['centroid'] = centroid
                    self.tracks[closest_track_id]['frames'] += 1
                else:
                    detection.track_id = self.next_track_id
                    self.tracks[self.next_track_id] = {
                        'centroid': centroid,
                        'frames': 1,
                        'class_name': detection.class_name
                    }
                    self.next_track_id += 1

        return detections


class VideoProcessor:
    """Processador principal de vídeo com RtspReader robusto e EventEngine"""

    def __init__(
        self, 
        rtsp_url: str, 
        camera_id: int,
        target_fps: int = 5,
        target_size: Tuple[int, int] = (1280, 720),
        use_onnx: bool = True,
        zones: Optional[Dict] = None
    ):
        self.rtsp_url = rtsp_url
        self.camera_id = camera_id
        self.target_fps = target_fps
        self.target_size = target_size
        self.zones = zones or {}  # Zonas para detecção de eventos
        
        # Usar RtspReader em vez de cv2.VideoCapture
        self.rtsp_reader = RtspReader(
            rtsp_url=rtsp_url,
            camera_id=camera_id,
            target_fps=target_fps,
            target_size=target_size
        )
        
        self.is_running = False
        self.frame_queue = Queue(maxsize=10)
        self.frame_id = 0

        # Componentes - ONNX por padrão
        self.motion_detector = MotionDetector()
        self.yolo_detector = YOLODetector(
            model_path="yolov8m.onnx" if use_onnx else "yolov8m.pt",
            use_onnx=use_onnx
        )
        self.tracker = ObjectTracker()
        
        # Event Engine para raciocínio temporal
        self.event_engine = EventEngine()
        
        # Pose Estimation para shoplifting detection
        if SHOPLIFTING_ENABLED:
            self.pose_estimator = PoseEstimator(
                model_complexity=POSE_MODEL_COMPLEXITY,
                min_detection_confidence=POSE_MIN_DETECTION_CONFIDENCE
            )
            self.pose_buffer = PoseSequenceBuffer(
                sequence_length=SHOPLIFTING_SEQUENCE_LENGTH,
                stride=12  # stride fixo
            )
            self.shoplifting_detector = ShopliftingDetector(
                anomaly_threshold=SHOPLIFTING_ANOMALY_THRESHOLD,
                model_path=None,  # usar heurísticas por padrão
                use_onnx=False
            )
            logger.info("✓ Shoplifting detection habilitado (modo heurístico)")
        else:
            self.pose_estimator = None
            self.pose_buffer = None
            self.shoplifting_detector = None

    def connect(self) -> bool:
        """Conecta à câmera via RtspReader"""
        try:
            if self.rtsp_reader.start():
                logger.info(f"Conectado à câmera {self.camera_id}: {self.rtsp_url}")
                return True
            else:
                logger.error(f"Falha ao iniciar RtspReader para câmera {self.camera_id}")
                return False
        except Exception as e:
            logger.error(f"Erro ao conectar à câmera {self.camera_id}: {e}")
            return False

    def disconnect(self):
        """Desconecta da câmera"""
        if self.rtsp_reader:
            self.rtsp_reader.stop()
            logger.info(f"Desconectado da câmera {self.camera_id}")
    
    def is_healthy(self) -> bool:
        """Verifica se o processador está saudável"""
        return self.rtsp_reader.is_healthy() if self.rtsp_reader else False
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do processador para diagnósticos"""
        stats = {
            'camera_id': self.camera_id,
            'running': self.is_running,
            'frame_id': self.frame_id,
        }
        
        if self.rtsp_reader:
            stats.update(self.rtsp_reader.get_stats())
        
        return stats

    def process_frame(self, frame: np.ndarray) -> Frame:
        """Processa um frame (já vem redimensionado do RtspReader)"""
        # Frame já vem no tamanho correto do RtspReader, não precisa redimensionar
        
        # Detectar movimento
        motion_detected, _ = self.motion_detector.detect(frame)

        # Detectar objetos apenas se houver movimento
        detections = []
        events = []
        
        if motion_detected:
            detections = self.yolo_detector.detect(frame)
            detections = self.tracker.update(detections, frame.shape[:2])
            
            # Event Engine - raciocínio temporal
            if detections:
                # Atualizar tracks no event engine
                self.event_engine.update_tracks(detections)
                
                # Atualizar presença em zonas
                for zone_id, zone_region in self.zones.items():
                    self.event_engine.update_zone_presence(zone_id, zone_region)
                
                # Detectar eventos temporais em cada zona
                for zone_id, zone_data in self.zones.items():
                    zone_region = zone_data.get('region')
                    zone_schedule = zone_data.get('schedule')
                    
                    # Intrusion - pessoa em zona fora do horário
                    intrusion_events = self.event_engine.detect_intrusion(
                        zone_id=zone_id,
                        zone_schedule=zone_schedule
                    )
                    events.extend(intrusion_events)
                    
                    # Loitering - permanência prolongada
                    loitering_events = self.event_engine.detect_loitering(
                        zone_id=zone_id
                    )
                    events.extend(loitering_events)
                    
                    # Crowd anomaly
                    crowd_events = self.event_engine.detect_crowd_anomaly(
                        zone_id=zone_id
                    )
                    events.extend(crowd_events)
                
                # Shoplifting detection (se habilitado)
                if SHOPLIFTING_ENABLED and self.pose_estimator:
                    # Extrair bboxes de pessoas
                    person_bboxes = [
                        det.bbox for det in detections 
                        if det.class_name == 'person' and det.track_id is not None
                    ]
                    
                    if person_bboxes:
                        # Estimar poses para todas as pessoas detectadas
                        poses = self.pose_estimator.detect_poses(frame, person_bboxes)
                        
                        # Adicionar poses ao buffer temporal
                        self.pose_buffer.add_frame(self.frame_id, poses)
                        
                        # Obter sequências completas (24 frames)
                        sequences = self.pose_buffer.get_sequences()
                        
                        # Detectar shoplifting em cada sequência
                        for seq_info in sequences:
                            track_id = seq_info['track_id']
                            pose_sequence = seq_info['sequence']  # (24, 18, 2)
                            
                            # Detecção de shoplifting
                            shoplifting_event = self.shoplifting_detector.detect(
                                pose_sequence=pose_sequence,
                                track_id=track_id
                            )
                            
                            # Se detectou shoplifting, criar EventCandidate
                            if shoplifting_event and shoplifting_event.is_anomaly:
                                # Encontrar a pessoa correspondente
                                person_det = next(
                                    (d for d in detections if d.track_id == track_id),
                                    None
                                )
                                
                                if person_det:
                                    event_candidate = EventCandidate(
                                        event_type='shoplifting',
                                        confidence=shoplifting_event.anomaly_score,
                                        timestamp=datetime.now(),
                                        camera_id=self.camera_id,
                                        zone_id='retail_area',  # zona padrão
                                        track_ids=[track_id],
                                        metadata={
                                            'bbox': person_det.bbox,
                                            'hand_motion_score': shoplifting_event.hand_motion_score,
                                            'body_bend_score': shoplifting_event.body_bend_score,
                                            'furtive_score': shoplifting_event.furtive_score,
                                            'velocity_score': shoplifting_event.velocity_score,
                                            'start_frame': shoplifting_event.start_frame,
                                            'end_frame': shoplifting_event.end_frame
                                        }
                                    )
                                    events.append(event_candidate)
                                    logger.warning(
                                        f"⚠ Shoplifting detectado! "
                                        f"Track {track_id}, Score: {shoplifting_event.anomaly_score:.2f}"
                                    )

        # Criar objeto Frame
        frame_obj = Frame(
            timestamp=datetime.now(),
            frame_id=self.frame_id,
            detections=detections,
            motion_detected=motion_detected,
            events=events,
            raw_frame=frame.copy()
        )

        self.frame_id += 1
        return frame_obj

    def run(self):
        """Executa o processamento de vídeo em thread usando RtspReader"""
        if not self.connect():
            return

        self.is_running = True
        frame_count = 0

        try:
            # Usar iterator frames() do RtspReader
            for frame in self.rtsp_reader.frames(timeout=2.0):
                if not self.is_running:
                    break
                
                if frame is None:
                    continue

                frame_count += 1

                # Processar frame
                processed_frame = self.process_frame(frame)

                # Adicionar à fila (descartar se cheia)
                try:
                    self.frame_queue.put_nowait(processed_frame)
                except:
                    pass  # Queue cheia, descartar frame
                
                # Log periódico
                if frame_count % 100 == 0:
                    stats = self.get_stats()
                    logger.info(
                        f"Câmera {self.camera_id}: {frame_count} frames processados, "
                        f"reconexões: {stats.get('reconnect_count', 0)}"
                    )

        except Exception as e:
            logger.error(f"Erro no processamento de vídeo câmera {self.camera_id}: {e}", exc_info=True)
        finally:
            self.disconnect()

    def start(self):
        """Inicia o processamento em thread"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        logger.info(f"Processador de vídeo iniciado para câmera {self.camera_id}")

    def stop(self):
        """Para o processamento"""
        self.is_running = False
        logger.info(f"Processador de vídeo parado para câmera {self.camera_id}")

    def get_frame(self, timeout: float = 1.0) -> Optional[Frame]:
        """Obtém um frame processado da fila"""
        try:
            return self.frame_queue.get(timeout=timeout)
        except:
            return None
