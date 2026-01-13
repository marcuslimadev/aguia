"""
Shoplifting Detection baseado em Shopformer (CVPR 2025)
Usa pose sequences para detectar comportamento suspeito
"""
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import onnxruntime as ort

logger = logging.getLogger(__name__)


@dataclass
class ShopliftingEvent:
    """Evento de shoplifting detectado"""
    track_id: int
    anomaly_score: float
    timestamp: datetime
    pose_sequence: np.ndarray  # (24, 18, 2)
    confidence: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ShopliftingDetector:
    """
    Detector de shoplifting baseado em pose sequences
    Inspirado em Shopformer (CVPR 2025)
    
    Arquitetura:
    - Stage 1: GCAE tokenizer (pose → embeddings)
    - Stage 2: Transformer encoder-decoder
    - Output: Reconstruction error → Anomaly score
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        sequence_length: int = 24,
        anomaly_threshold: float = 0.7,
        use_onnx: bool = True
    ):
        """
        Args:
            model_path: Caminho para modelo ONNX (None = usar heurísticas)
            sequence_length: Número de frames na sequência
            anomaly_threshold: Threshold para considerar shoplifting
            use_onnx: Se True, usa modelo ONNX. Se False, heurísticas
        """
        self.model_path = model_path
        self.sequence_length = sequence_length
        self.anomaly_threshold = anomaly_threshold
        self.use_onnx = use_onnx
        
        self.model = None
        self.session = None
        
        if use_onnx and model_path:
            self._load_onnx_model()
        else:
            logger.info("Usando heurísticas para detecção de shoplifting (modelo ONNX não disponível)")

    def _load_onnx_model(self):
        """Carrega modelo ONNX Shopformer"""
        try:
            self.session = ort.InferenceSession(
                self.model_path,
                providers=['CPUExecutionProvider']
            )
            
            # Get input/output names
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            
            logger.info(f"✓ Shopformer ONNX model loaded: {self.model_path}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo ONNX: {e}")
            self.session = None

    def detect(self, pose_sequence: np.ndarray, track_id: int) -> Optional[ShopliftingEvent]:
        """
        Detecta shoplifting em sequência de poses
        
        Args:
            pose_sequence: Array (sequence_length, 18, 2) com keypoints
            track_id: ID do track da pessoa
        
        Returns:
            ShopliftingEvent se detectado, None caso contrário
        """
        if pose_sequence.shape[0] != self.sequence_length:
            logger.warning(f"Sequência tem {pose_sequence.shape[0]} frames, esperado {self.sequence_length}")
            return None

        # Compute anomaly score
        if self.session is not None:
            anomaly_score = self._compute_anomaly_onnx(pose_sequence)
        else:
            anomaly_score = self._compute_anomaly_heuristic(pose_sequence)

        # Verificar threshold
        if anomaly_score > self.anomaly_threshold:
            # Determinar severity
            if anomaly_score > 0.9:
                severity = 'critical'
            elif anomaly_score > 0.8:
                severity = 'high'
            elif anomaly_score > 0.7:
                severity = 'medium'
            else:
                severity = 'low'

            return ShopliftingEvent(
                track_id=track_id,
                anomaly_score=anomaly_score,
                timestamp=datetime.now(),
                pose_sequence=pose_sequence,
                confidence=anomaly_score,
                severity=severity,
                metadata={
                    'method': 'onnx' if self.session else 'heuristic'
                }
            )

        return None

    def _compute_anomaly_onnx(self, pose_sequence: np.ndarray) -> float:
        """
        Computa anomaly score usando modelo ONNX
        
        Args:
            pose_sequence: (sequence_length, 18, 2)
        
        Returns:
            Anomaly score [0-1]
        """
        try:
            # Normalizar input
            input_data = self._preprocess_sequence(pose_sequence)
            
            # Inferência
            outputs = self.session.run(
                [self.output_name],
                {self.input_name: input_data}
            )
            
            # Reconstruction error → Anomaly score
            reconstruction = outputs[0]
            mse = np.mean((input_data - reconstruction) ** 2)
            
            # Normalize MSE to [0-1]
            anomaly_score = min(1.0, mse * 10)  # Ajustar scaling conforme necessário
            
            return anomaly_score
            
        except Exception as e:
            logger.error(f"Erro na inferência ONNX: {e}")
            return 0.0

    def _compute_anomaly_heuristic(self, pose_sequence: np.ndarray) -> float:
        """
        Computa anomaly score usando heurísticas
        
        Heurísticas para shoplifting:
        1. Movimento brusco de mãos (reaching, grabbing)
        2. Inclinação do corpo (bending down)
        3. Movimentos furtivos (olhar ao redor, hands near pockets/bag)
        4. Velocidade de movimento anormal
        
        Args:
            pose_sequence: (sequence_length, 18, 2)
        
        Returns:
            Anomaly score [0-1]
        """
        scores = []

        # Heurística 1: Movimento brusco de mãos
        hand_motion_score = self._analyze_hand_motion(pose_sequence)
        scores.append(hand_motion_score)

        # Heurística 2: Inclinação do corpo
        body_bend_score = self._analyze_body_bend(pose_sequence)
        scores.append(body_bend_score)

        # Heurística 3: Movimentos furtivos
        furtive_score = self._analyze_furtive_behavior(pose_sequence)
        scores.append(furtive_score)

        # Heurística 4: Velocidade anormal
        velocity_score = self._analyze_velocity(pose_sequence)
        scores.append(velocity_score)

        # Combinar scores (weighted average)
        weights = [0.3, 0.25, 0.25, 0.2]
        anomaly_score = np.average(scores, weights=weights)

        return float(anomaly_score)

    def _analyze_hand_motion(self, pose_sequence: np.ndarray) -> float:
        """
        Analisa movimento das mãos
        
        Shoplifting: mãos se movem rapidamente para pegar objeto
        """
        # Wrist keypoints: right_wrist=4, left_wrist=7
        right_wrist = pose_sequence[:, 4, :]  # (T, 2)
        left_wrist = pose_sequence[:, 7, :]   # (T, 2)

        # Calcular velocidade das mãos
        right_velocity = np.linalg.norm(np.diff(right_wrist, axis=0), axis=1)
        left_velocity = np.linalg.norm(np.diff(left_wrist, axis=0), axis=1)

        # Picos de velocidade indicam movimento brusco
        right_peak = np.max(right_velocity) if len(right_velocity) > 0 else 0
        left_peak = np.max(left_velocity) if len(left_velocity) > 0 else 0

        max_peak = max(right_peak, left_peak)

        # Normalizar (valores típicos: 0.01-0.05 para movimento normal)
        score = min(1.0, max_peak / 0.1)

        return score

    def _analyze_body_bend(self, pose_sequence: np.ndarray) -> float:
        """
        Analisa inclinação do corpo
        
        Shoplifting: pessoa se inclina para pegar objeto em prateleira baixa
        """
        # Keypoints: nose=0, neck=1, hips=(8+11)/2
        nose = pose_sequence[:, 0, :]      # (T, 2)
        neck = pose_sequence[:, 1, :]      # (T, 2)
        right_hip = pose_sequence[:, 8, :]
        left_hip = pose_sequence[:, 11, :]
        hips = (right_hip + left_hip) / 2  # (T, 2)

        # Calcular ângulo de inclinação (nose-neck-hips)
        angles = []
        for i in range(len(pose_sequence)):
            # Vetores
            v1 = nose[i] - neck[i]
            v2 = hips[i] - neck[i]

            # Ângulo
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.arccos(np.clip(cos_angle, -1, 1))
            angles.append(angle)

        # Inclinação pronunciada: ângulo < 90° (1.57 rad)
        min_angle = np.min(angles)
        score = max(0, 1 - (min_angle / 1.57))  # Normalizar

        return score

    def _analyze_furtive_behavior(self, pose_sequence: np.ndarray) -> float:
        """
        Analisa comportamento furtivo
        
        Shoplifting: mãos perto de bolsos/cintura (esconder objeto)
        """
        # Wrists e hips
        right_wrist = pose_sequence[:, 4, :]  # (T, 2)
        left_wrist = pose_sequence[:, 7, :]   # (T, 2)
        right_hip = pose_sequence[:, 8, :]
        left_hip = pose_sequence[:, 11, :]

        # Distância mãos-cintura
        right_dist = np.linalg.norm(right_wrist - right_hip, axis=1)
        left_dist = np.linalg.norm(left_wrist - left_hip, axis=1)

        # Proporção de frames com mãos perto da cintura
        threshold = 0.15  # distância normalizada
        right_near = np.mean(right_dist < threshold)
        left_near = np.mean(left_dist < threshold)

        score = max(right_near, left_near)

        return score

    def _analyze_velocity(self, pose_sequence: np.ndarray) -> float:
        """
        Analisa velocidade geral de movimento
        
        Shoplifting: movimento pode ser rápido (grab) ou lento (furtivo)
        """
        # Center of mass (média de todos keypoints)
        center_of_mass = np.mean(pose_sequence, axis=1)  # (T, 2)

        # Velocidade
        velocity = np.linalg.norm(np.diff(center_of_mass, axis=0), axis=1)

        # Variância de velocidade (mudanças bruscas)
        velocity_variance = np.var(velocity) if len(velocity) > 0 else 0

        # Normalizar (valores típicos: 0.0001-0.001)
        score = min(1.0, velocity_variance / 0.002)

        return score

    def _preprocess_sequence(self, pose_sequence: np.ndarray) -> np.ndarray:
        """
        Preprocessa sequência para modelo ONNX
        
        Args:
            pose_sequence: (sequence_length, 18, 2)
        
        Returns:
            Preprocessed array com shape esperado pelo modelo
        """
        # Flatten to (sequence_length, 36) - 18 keypoints × 2 coords
        flattened = pose_sequence.reshape(self.sequence_length, -1)

        # Adicionar batch dimension: (1, sequence_length, 36)
        batched = flattened[np.newaxis, ...]

        return batched.astype(np.float32)

    def batch_detect(self, pose_sequences: List[Tuple[int, np.ndarray]]) -> List[ShopliftingEvent]:
        """
        Detecta shoplifting em múltiplas sequências
        
        Args:
            pose_sequences: Lista de (track_id, pose_sequence)
        
        Returns:
            Lista de ShopliftingEvents detectados
        """
        events = []

        for track_id, pose_sequence in pose_sequences:
            event = self.detect(pose_sequence, track_id)
            if event:
                events.append(event)

        return events

    def get_stats(self) -> Dict:
        """Retorna estatísticas do detector"""
        return {
            'model_loaded': self.session is not None,
            'model_path': self.model_path,
            'sequence_length': self.sequence_length,
            'anomaly_threshold': self.anomaly_threshold,
            'method': 'onnx' if self.session else 'heuristic'
        }
