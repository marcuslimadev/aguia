"""
Testes para Validator Model
"""
import pytest
import numpy as np
from pathlib import Path
from datetime import datetime
from src.ai.validator_model import ValidatorModel
from src.ai.event_engine import EventCandidate


@pytest.fixture
def validator_model():
    """Fixture que cria um validator model (sem modelo ONNX, usa heurística)"""
    return ValidatorModel(model_path=None)


@pytest.fixture
def custom_validator():
    """Fixture com thresholds customizados"""
    custom_thresholds = {
        'intrusion': 0.9,
        'loitering': 0.8,
        'theft': 0.95
    }
    return ValidatorModel(model_path=None, custom_thresholds=custom_thresholds)


@pytest.fixture
def sample_snapshot():
    """Fixture com snapshot de exemplo"""
    return np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)


@pytest.fixture
def intrusion_event():
    """Fixture com evento de intrusão"""
    return EventCandidate(
        event_type='intrusion',
        zone_id=1,
        track_id=10,
        confidence=0.9,
        severity='high',
        timestamp=datetime.now(),
        metadata={'duration': 5.5, 'class_name': 'person'}
    )


@pytest.fixture
def loitering_event():
    """Fixture com evento de loitering"""
    return EventCandidate(
        event_type='loitering',
        zone_id=1,
        track_id=20,
        confidence=0.85,
        severity='medium',
        timestamp=datetime.now(),
        metadata={'dwell_time': 75.0, 'movement': 50, 'class_name': 'person'}
    )


class TestValidatorModel:
    """Testes para Validator Model"""

    def test_initialization_default(self, validator_model):
        """Testa inicialização com thresholds padrão"""
        assert validator_model.session is None  # Sem modelo ONNX
        assert validator_model.thresholds['intrusion'] == 0.7
        assert validator_model.thresholds['loitering'] == 0.6
        assert validator_model.thresholds['theft'] == 0.8

    def test_initialization_custom_thresholds(self, custom_validator):
        """Testa inicialização com thresholds customizados"""
        assert custom_validator.thresholds['intrusion'] == 0.9
        assert custom_validator.thresholds['loitering'] == 0.8
        assert custom_validator.thresholds['theft'] == 0.95

    def test_validate_heuristic_intrusion(self, validator_model):
        """Testa validação heurística de intrusão"""
        metadata = {'confidence': 0.8}
        is_valid, score = validator_model._validate_heuristic('intrusion', metadata)
        
        # Intrusion tem adjustment 1.0, então score = 0.8 * 1.0 = 0.8
        assert score == 0.8
        # Threshold padrão para intrusion é 0.7, então deve ser válido
        assert is_valid is True

    def test_validate_heuristic_loitering(self, validator_model):
        """Testa validação heurística de loitering"""
        metadata = {'confidence': 0.65}
        is_valid, score = validator_model._validate_heuristic('loitering', metadata)
        
        # Loitering tem adjustment 0.95, então score = 0.65 * 0.95 ≈ 0.6175
        assert 0.61 < score < 0.62
        # Threshold padrão para loitering é 0.6, então deve ser válido
        assert is_valid is True

    def test_validate_heuristic_below_threshold(self, validator_model):
        """Testa validação heurística abaixo do threshold"""
        metadata = {'confidence': 0.4}
        is_valid, score = validator_model._validate_heuristic('intrusion', metadata)
        
        # Score = 0.4 * 1.0 = 0.4, threshold = 0.7
        assert score == 0.4
        assert is_valid is False

    def test_validate_event_candidate_intrusion(self, validator_model, intrusion_event):
        """Testa validação de EventCandidate de intrusão"""
        is_valid, score = validator_model.validate_event_candidate(intrusion_event)
        
        # Confidence = 0.9, adjustment = 1.0, score = 0.9
        assert score == 0.9
        # Threshold = 0.7, então deve ser válido
        assert is_valid is True

    def test_validate_event_candidate_loitering(self, validator_model, loitering_event):
        """Testa validação de EventCandidate de loitering"""
        is_valid, score = validator_model.validate_event_candidate(loitering_event)
        
        # Confidence = 0.85, adjustment = 0.95, score ≈ 0.8075
        assert 0.80 < score < 0.81
        # Threshold = 0.6, então deve ser válido
        assert is_valid is True

    def test_validate_event_with_snapshot(self, validator_model, sample_snapshot):
        """Testa validação com snapshot (sem modelo ONNX, usa heurística)"""
        metadata = {'confidence': 0.85}
        is_valid, score = validator_model.validate_event('intrusion', sample_snapshot, metadata)
        
        # Deve usar heurística já que não há modelo ONNX
        assert score == 0.85  # Intrusion adjustment = 1.0
        assert is_valid is True

    def test_preprocess_snapshot(self, validator_model, sample_snapshot):
        """Testa preprocessamento de snapshot"""
        processed = validator_model._preprocess_snapshot(sample_snapshot)
        
        # Deve ter shape (1, 3, 224, 224) - NCHW format
        assert processed.shape == (1, 3, 224, 224)
        assert processed.dtype == np.float32
        # Valores devem estar normalizados [0, 1]
        assert processed.min() >= 0.0
        assert processed.max() <= 1.0

    def test_set_threshold(self, validator_model):
        """Testa alteração de threshold"""
        original = validator_model.get_threshold('intrusion')
        assert original == 0.7
        
        validator_model.set_threshold('intrusion', 0.85)
        
        new_threshold = validator_model.get_threshold('intrusion')
        assert new_threshold == 0.85

    def test_get_threshold_unknown_event(self, validator_model):
        """Testa obtenção de threshold para evento desconhecido"""
        threshold = validator_model.get_threshold('unknown_event')
        assert threshold == 0.7  # Threshold padrão

    def test_custom_threshold_enforcement(self, custom_validator):
        """Testa que thresholds customizados são aplicados corretamente"""
        # Evento com confidence 0.85
        metadata = {'confidence': 0.85}
        
        # Intrusion: threshold customizado = 0.9, score = 0.85
        is_valid, score = custom_validator._validate_heuristic('intrusion', metadata)
        assert score == 0.85
        assert is_valid is False  # Abaixo do threshold 0.9
        
        # Loitering: threshold customizado = 0.8, score = 0.85 * 0.95 ≈ 0.8075
        is_valid, score = custom_validator._validate_heuristic('loitering', metadata)
        assert 0.80 < score < 0.81
        assert is_valid is True  # Acima do threshold 0.8

    def test_validate_event_candidate_rejected(self, custom_validator):
        """Testa que evento é rejeitado quando abaixo do threshold customizado"""
        # Evento com confidence baixa
        event = EventCandidate(
            event_type='intrusion',
            zone_id=1,
            track_id=100,
            confidence=0.75,  # Abaixo do threshold customizado 0.9
            severity='high',
            timestamp=datetime.now(),
            metadata={'duration': 2.0}
        )
        
        is_valid, score = custom_validator.validate_event_candidate(event)
        
        assert score == 0.75  # Intrusion adjustment = 1.0
        assert is_valid is False  # Abaixo do threshold 0.9

    def test_validate_multiple_event_types(self, validator_model):
        """Testa validação de múltiplos tipos de eventos"""
        event_types = ['intrusion', 'loitering', 'theft', 'crowd_anomaly']
        metadata = {'confidence': 0.8}
        
        for event_type in event_types:
            is_valid, score = validator_model._validate_heuristic(event_type, metadata)
            assert score > 0.0
            assert isinstance(is_valid, bool)

    def test_validate_without_confidence_in_metadata(self, validator_model):
        """Testa validação quando metadata não tem confidence"""
        metadata = {}  # Sem confidence
        is_valid, score = validator_model._validate_heuristic('intrusion', metadata)
        
        # Deve usar confidence padrão de 0.5
        assert score == 0.5
        assert is_valid is False  # Abaixo do threshold 0.7

    def test_event_candidate_without_snapshot(self, validator_model, intrusion_event):
        """Testa validação de EventCandidate sem snapshot (usa heurística)"""
        # EventCandidate sem evidence_frames
        intrusion_event.evidence_frames = []
        
        is_valid, score = validator_model.validate_event_candidate(intrusion_event, snapshot=None)
        
        # Deve usar heurística
        assert score == 0.9  # Confidence do evento
        assert is_valid is True
