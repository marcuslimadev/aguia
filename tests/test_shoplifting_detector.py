"""
Testes para Shoplifting Detector
"""
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.shoplifting_detector import ShopliftingDetector, ShopliftingEvent
from src.ai.pose_estimator import PoseEstimator, PoseSequenceBuffer


class TestShopliftingDetector:
    """Testes para ShopliftingDetector"""

    @pytest.fixture
    def detector(self):
        """Detector com heurísticas (sem modelo ONNX)"""
        return ShopliftingDetector(
            model_path=None,
            sequence_length=24,
            anomaly_threshold=0.7,
            use_onnx=False
        )

    @pytest.fixture
    def normal_sequence(self):
        """Sequência de pose normal (pessoa parada)"""
        # 24 frames, 18 keypoints, 2 coords (x, y)
        sequence = np.zeros((24, 18, 2), dtype=np.float32)
        
        # Pose em pé, parada
        for t in range(24):
            # Cabeça
            sequence[t, 0] = [0.5, 0.2]  # nose
            sequence[t, 1] = [0.5, 0.25] # neck
            
            # Braços
            sequence[t, 2] = [0.4, 0.25] # right shoulder
            sequence[t, 5] = [0.6, 0.25] # left shoulder
            sequence[t, 3] = [0.4, 0.4]  # right elbow
            sequence[t, 6] = [0.6, 0.4]  # left elbow
            sequence[t, 4] = [0.4, 0.5]  # right wrist
            sequence[t, 7] = [0.6, 0.5]  # left wrist
            
            # Corpo
            sequence[t, 8] = [0.45, 0.6]  # right hip
            sequence[t, 11] = [0.55, 0.6] # left hip
            
            # Pernas
            sequence[t, 9] = [0.45, 0.8]  # right knee
            sequence[t, 12] = [0.55, 0.8] # left knee
            sequence[t, 10] = [0.45, 0.95] # right ankle
            sequence[t, 13] = [0.55, 0.95] # left ankle
            
            # Olhos/orelhas
            sequence[t, 14] = [0.48, 0.18] # right eye
            sequence[t, 15] = [0.52, 0.18] # left eye
            sequence[t, 16] = [0.46, 0.2]  # right ear
            sequence[t, 17] = [0.54, 0.2]  # left ear
        
        return sequence

    @pytest.fixture
    def suspicious_sequence(self):
        """Sequência de pose suspeita (shoplifting)"""
        sequence = np.zeros((24, 18, 2), dtype=np.float32)
        
        for t in range(24):
            # Inclinação do corpo (bending down)
            bend_factor = min(1.0, t / 12)  # Aumenta até frame 12
            
            # Cabeça abaixa
            sequence[t, 0] = [0.5, 0.3 + bend_factor * 0.2]  # nose
            sequence[t, 1] = [0.5, 0.35 + bend_factor * 0.2] # neck
            
            # Braços se movem rapidamente (reaching)
            if t > 10:
                # Mão direita vai para baixo/frente (pegar objeto)
                sequence[t, 4] = [0.3 + (t - 10) * 0.02, 0.7]  # right wrist
                sequence[t, 7] = [0.6, 0.5]  # left wrist normal
            else:
                sequence[t, 4] = [0.4, 0.5]
                sequence[t, 7] = [0.6, 0.5]
            
            # Shoulders, elbows
            sequence[t, 2] = [0.4, 0.35]
            sequence[t, 5] = [0.6, 0.35]
            sequence[t, 3] = [0.35, 0.5]
            sequence[t, 6] = [0.6, 0.4]
            
            # Hips
            sequence[t, 8] = [0.45, 0.6]
            sequence[t, 11] = [0.55, 0.6]
            
            # Pernas
            sequence[t, 9] = [0.45, 0.75]
            sequence[t, 12] = [0.55, 0.75]
            sequence[t, 10] = [0.45, 0.9]
            sequence[t, 13] = [0.55, 0.9]
            
            # Eyes/ears
            sequence[t, 14] = [0.48, 0.28]
            sequence[t, 15] = [0.52, 0.28]
            sequence[t, 16] = [0.46, 0.3]
            sequence[t, 17] = [0.54, 0.3]
        
        return sequence

    def test_detector_initialization(self, detector):
        """Testa inicialização do detector"""
        assert detector is not None
        assert detector.sequence_length == 24
        assert detector.anomaly_threshold == 0.7
        assert detector.session is None  # Sem ONNX

    def test_normal_sequence_detection(self, detector, normal_sequence):
        """Testa que sequência normal NÃO gera alerta"""
        event = detector.detect(normal_sequence, track_id=1)
        
        # Pode retornar None ou evento com score baixo
        if event:
            assert event.anomaly_score < detector.anomaly_threshold

    def test_suspicious_sequence_detection(self, detector, suspicious_sequence):
        """Testa que sequência suspeita GERA alerta"""
        event = detector.detect(suspicious_sequence, track_id=1)
        
        # Deve detectar comportamento suspeito
        assert event is not None
        assert event.anomaly_score >= detector.anomaly_threshold
        assert event.track_id == 1
        assert event.severity in ['low', 'medium', 'high', 'critical']

    def test_hand_motion_analysis(self, detector, suspicious_sequence):
        """Testa análise de movimento de mãos"""
        score = detector._analyze_hand_motion(suspicious_sequence)
        
        assert 0 <= score <= 1
        # Sequência suspeita deve ter score alto
        assert score > 0.3

    def test_body_bend_analysis(self, detector, suspicious_sequence):
        """Testa análise de inclinação do corpo"""
        score = detector._analyze_body_bend(suspicious_sequence)
        
        assert 0 <= score <= 1

    def test_furtive_behavior_analysis(self, detector):
        """Testa análise de comportamento furtivo"""
        # Sequência com mãos perto da cintura
        sequence = np.zeros((24, 18, 2), dtype=np.float32)
        
        for t in range(24):
            sequence[t, 4] = [0.45, 0.6]  # right wrist perto right hip
            sequence[t, 8] = [0.45, 0.6]  # right hip
        
        score = detector._analyze_furtive_behavior(sequence)
        
        assert 0 <= score <= 1
        assert score > 0.5  # Mãos perto da cintura

    def test_velocity_analysis(self, detector, normal_sequence):
        """Testa análise de velocidade"""
        score = detector._analyze_velocity(normal_sequence)
        
        assert 0 <= score <= 1
        # Sequência parada deve ter score baixo
        assert score < 0.2

    def test_batch_detection(self, detector, normal_sequence, suspicious_sequence):
        """Testa detecção em batch"""
        sequences = [
            (1, normal_sequence),
            (2, suspicious_sequence),
            (3, normal_sequence)
        ]
        
        events = detector.batch_detect(sequences)
        
        # Apenas sequência suspeita deve gerar evento
        assert len(events) >= 1
        assert any(e.track_id == 2 for e in events)

    def test_get_stats(self, detector):
        """Testa estatísticas do detector"""
        stats = detector.get_stats()
        
        assert 'model_loaded' in stats
        assert 'sequence_length' in stats
        assert 'anomaly_threshold' in stats
        assert 'method' in stats
        assert stats['method'] == 'heuristic'

    def test_invalid_sequence_length(self, detector):
        """Testa sequência com tamanho inválido"""
        invalid_sequence = np.zeros((10, 18, 2))  # Apenas 10 frames
        
        event = detector.detect(invalid_sequence, track_id=1)
        
        assert event is None  # Deve rejeitar

    def test_event_dataclass(self):
        """Testa ShopliftingEvent dataclass"""
        from datetime import datetime
        
        event = ShopliftingEvent(
            track_id=1,
            anomaly_score=0.85,
            timestamp=datetime.now(),
            pose_sequence=np.zeros((24, 18, 2)),
            confidence=0.85,
            severity='high'
        )
        
        assert event.track_id == 1
        assert event.anomaly_score == 0.85
        assert event.severity == 'high'
        assert event.metadata is not None


class TestPoseEstimator:
    """Testes para PoseEstimator"""

    def test_pose_estimator_init(self):
        """Testa inicialização do pose estimator"""
        estimator = PoseEstimator(model_complexity=1)
        
        assert estimator is not None
        assert estimator.model_complexity == 1
        assert len(estimator.KEYPOINT_NAMES) == 18

    def test_pose_sequence_buffer(self):
        """Testa buffer de sequências"""
        buffer = PoseSequenceBuffer(sequence_length=24, stride=12)
        
        # Adicionar frames
        for i in range(30):
            pose = np.random.rand(18, 2).astype(np.float32)
            buffer.add_frame(i, [pose])
        
        # Buffer deve manter apenas 24 frames
        assert len(buffer.buffer) == 24
        
        # Obter sequências
        sequences = buffer.get_sequences()
        assert len(sequences) > 0
        assert sequences[0].shape == (24, 18, 2)

    def test_buffer_clear(self):
        """Testa limpeza do buffer"""
        buffer = PoseSequenceBuffer()
        
        for i in range(10):
            buffer.add_frame(i, [np.random.rand(18, 2)])
        
        buffer.clear()
        assert len(buffer.buffer) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
