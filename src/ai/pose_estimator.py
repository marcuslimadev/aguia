"""
Pose Estimation usando MediaPipe para análise de comportamento
"""
import logging
import os
import numpy as np
from typing import List, Tuple, Optional
import cv2

logger = logging.getLogger(__name__)


class PoseEstimator:
    """Estimador de pose humana usando MediaPipe"""

    # COCO 18 keypoint format (compatível com Shopformer)
    KEYPOINT_NAMES = [
        'nose', 'neck',  # 0, 1
        'right_shoulder', 'right_elbow', 'right_wrist',  # 2, 3, 4
        'left_shoulder', 'left_elbow', 'left_wrist',  # 5, 6, 7
        'right_hip', 'right_knee', 'right_ankle',  # 8, 9, 10
        'left_hip', 'left_knee', 'left_ankle',  # 11, 12, 13
        'right_eye', 'left_eye',  # 14, 15
        'right_ear', 'left_ear'  # 16, 17
    ]

    def __init__(self, model_complexity: int = 1, min_detection_confidence: float = 0.5):
        """
        Inicializa pose estimator
        
        Args:
            model_complexity: 0, 1 ou 2 (higher = more accurate, slower)
            min_detection_confidence: Threshold de confiança
        """
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.pose_detector = None
        
        self._init_mediapipe()

    def _init_mediapipe(self):
        """Inicializa MediaPipe Pose"""
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            # MediaPipe 0.10.30+ usa nova API com tasks
            logger.info("Initializing MediaPipe Pose (new API)...")
            
            # Download model if needed
            model_path = "pose_landmarker_lite.task"
            if not os.path.exists(model_path):
                logger.warning("MediaPipe pose model not found - pose detection disabled")
                logger.info("Download from: https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task")
                self.pose_detector = None
                return
            
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.PoseLandmarkerOptions(
                base_options=base_options,
                output_segmentation_masks=False,
                min_pose_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=0.5
            )
            self.pose_detector = vision.PoseLandmarker.create_from_options(options)
            
            logger.info("✓ MediaPipe Pose initialized (new API)")
            
        except ImportError:
            logger.warning("MediaPipe não instalado - pose detection desabilitado")
            self.pose_detector = None
        except Exception as e:
            logger.warning(f"MediaPipe pose detection não disponível: {e}")
            logger.info("Pose detection desabilitado - sistema funciona sem ele")
            self.pose_detector = None

    def detect_poses(self, frame: np.ndarray, person_bboxes: List[Tuple[int, int, int, int]] = None) -> List[np.ndarray]:
        """
        Detecta poses humanas no frame
        
        Args:
            frame: Frame BGR do OpenCV
            person_bboxes: Lista de bboxes (x1, y1, x2, y2) de pessoas detectadas
                          Se None, processa frame inteiro
        
        Returns:
            Lista de poses, cada uma shape (18, 2) com (x, y) normalized [0-1]
        """
        if self.pose_detector is None:
            return []

        poses = []

        try:
            # Se não tem bboxes, processa frame inteiro
            if person_bboxes is None or len(person_bboxes) == 0:
                pose = self._detect_single_pose(frame)
                if pose is not None:
                    poses.append(pose)
            else:
                # Processa cada pessoa detectada
                for bbox in person_bboxes:
                    x1, y1, x2, y2 = bbox
                    
                    # Crop pessoa com margem
                    margin = 10
                    x1 = max(0, x1 - margin)
                    y1 = max(0, y1 - margin)
                    x2 = min(frame.shape[1], x2 + margin)
                    y2 = min(frame.shape[0], y2 + margin)
                    
                    person_crop = frame[y1:y2, x1:x2]
                    
                    if person_crop.size == 0:
                        continue
                    
                    pose = self._detect_single_pose(person_crop, offset=(x1, y1))
                    if pose is not None:
                        poses.append(pose)

        except Exception as e:
            logger.error(f"Erro ao detectar poses: {e}")

        return poses

    def _detect_single_pose(self, image: np.ndarray, offset: Tuple[int, int] = (0, 0)) -> Optional[np.ndarray]:
        """
        Detecta pose em uma imagem
        
        Args:
            image: Imagem BGR
            offset: (x_offset, y_offset) para ajustar coordenadas
        
        Returns:
            Array (18, 2) com keypoints normalized ou None
        """
        # Converter BGR para RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Processar com MediaPipe
        results = self.pose_detector.process(image_rgb)
        
        if results.pose_landmarks is None:
            return None
        
        # Converter MediaPipe 33 landmarks para COCO 18 keypoints
        pose = self._mediapipe_to_coco18(results.pose_landmarks, image.shape, offset)
        
        return pose

    def _mediapipe_to_coco18(self, landmarks, image_shape, offset: Tuple[int, int]) -> np.ndarray:
        """
        Converte MediaPipe 33 landmarks para COCO 18 keypoints
        
        MediaPipe landmarks: 33 pontos
        COCO format: 18 pontos
        
        Returns:
            Array (18, 2) com (x, y) normalized [0-1]
        """
        h, w = image_shape[:2]
        x_offset, y_offset = offset
        
        # Mapping MediaPipe → COCO
        mp_to_coco = {
            0: 0,   # nose
            1: None,  # neck (calculado como média shoulders)
            2: 12,  # right_shoulder (MP: 12)
            3: 14,  # right_elbow (MP: 14)
            4: 16,  # right_wrist (MP: 16)
            5: 11,  # left_shoulder (MP: 11)
            6: 13,  # left_elbow (MP: 13)
            7: 15,  # left_wrist (MP: 15)
            8: 24,  # right_hip (MP: 24)
            9: 26,  # right_knee (MP: 26)
            10: 28, # right_ankle (MP: 28)
            11: 23, # left_hip (MP: 23)
            12: 25, # left_knee (MP: 25)
            13: 27, # left_ankle (MP: 27)
            14: 5,  # right_eye (MP: 5)
            15: 2,  # left_eye (MP: 2)
            16: 8,  # right_ear (MP: 8)
            17: 7   # left_ear (MP: 7)
        }
        
        keypoints = np.zeros((18, 2), dtype=np.float32)
        
        for coco_idx, mp_idx in mp_to_coco.items():
            if mp_idx is None:
                # Neck: média entre shoulders
                if coco_idx == 1:
                    right_shoulder = landmarks.landmark[12]
                    left_shoulder = landmarks.landmark[11]
                    x = (right_shoulder.x + left_shoulder.x) / 2
                    y = (right_shoulder.y + left_shoulder.y) / 2
                    keypoints[coco_idx] = [x, y]
            else:
                landmark = landmarks.landmark[mp_idx]
                # Coordenadas já estão normalized [0-1] no MediaPipe
                keypoints[coco_idx] = [landmark.x, landmark.y]
        
        return keypoints

    def visualize_pose(self, frame: np.ndarray, pose: np.ndarray) -> np.ndarray:
        """
        Desenha pose no frame
        
        Args:
            frame: Frame BGR
            pose: Array (18, 2) com keypoints normalized
        
        Returns:
            Frame com pose desenhada
        """
        h, w = frame.shape[:2]
        result = frame.copy()
        
        # Skeleton connections (COCO format)
        skeleton = [
            (0, 1),   # nose - neck
            (1, 2), (1, 5),  # neck - shoulders
            (2, 3), (3, 4),  # right arm
            (5, 6), (6, 7),  # left arm
            (1, 8), (1, 11), # neck - hips
            (8, 9), (9, 10), # right leg
            (11, 12), (12, 13), # left leg
            (0, 14), (0, 15), # nose - eyes
            (14, 16), (15, 17) # eyes - ears
        ]
        
        # Desenhar skeleton
        for start_idx, end_idx in skeleton:
            start = pose[start_idx]
            end = pose[end_idx]
            
            start_point = (int(start[0] * w), int(start[1] * h))
            end_point = (int(end[0] * w), int(end[1] * h))
            
            cv2.line(result, start_point, end_point, (0, 255, 0), 2)
        
        # Desenhar keypoints
        for kp in pose:
            point = (int(kp[0] * w), int(kp[1] * h))
            cv2.circle(result, point, 4, (0, 0, 255), -1)
        
        return result

    def close(self):
        """Libera recursos"""
        if self.pose_detector is not None:
            self.pose_detector.close()
            logger.info("✓ MediaPipe Pose closed")


class PoseSequenceBuffer:
    """Buffer para sequências de poses (temporal window)"""

    def __init__(self, sequence_length: int = 24, stride: int = 12):
        """
        Args:
            sequence_length: Número de frames na sequência
            stride: Step entre sequências
        """
        self.sequence_length = sequence_length
        self.stride = stride
        self.buffer = []  # Lista de (frame_id, poses)

    def add_frame(self, frame_id: int, poses: List[np.ndarray]):
        """
        Adiciona poses de um frame
        
        Args:
            frame_id: ID do frame
            poses: Lista de poses (18, 2) detectadas
        """
        self.buffer.append((frame_id, poses))
        
        # Manter apenas sequence_length frames
        if len(self.buffer) > self.sequence_length:
            self.buffer.pop(0)

    def get_sequences(self) -> List[np.ndarray]:
        """
        Retorna sequências prontas para inferência
        
        Returns:
            Lista de sequências, cada uma shape (sequence_length, 18, 2)
        """
        if len(self.buffer) < self.sequence_length:
            return []
        
        sequences = []
        
        # Extrair sequência para cada pessoa rastreada
        # Assumindo que ordem das poses é consistente (tracking)
        if len(self.buffer) > 0:
            num_persons = len(self.buffer[0][1])
            
            for person_idx in range(num_persons):
                sequence = []
                
                for frame_id, poses in self.buffer:
                    if person_idx < len(poses):
                        sequence.append(poses[person_idx])
                    else:
                        # Padding se pessoa desapareceu
                        sequence.append(np.zeros((18, 2)))
                
                if len(sequence) == self.sequence_length:
                    sequences.append(np.array(sequence))
        
        return sequences

    def clear(self):
        """Limpa buffer"""
        self.buffer.clear()
