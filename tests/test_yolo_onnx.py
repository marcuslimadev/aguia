"""
Testes para YoloOnnxDetector
"""
import pytest
import numpy as np
from pathlib import Path
from config.config import MODELS_DIR


class TestYoloOnnxDetector:
    """Testes para detector YOLO ONNX"""

    @pytest.fixture
    def detector(self):
        """Fixture para criar detector"""
        from src.ai.yolo_onnx import YoloOnnxDetector
        
        model_path = MODELS_DIR / "yolov8m.onnx"
        detector = YoloOnnxDetector(model_path, conf_threshold=0.5)
        
        return detector

    def test_detector_initialization(self, detector):
        """Testa inicialização do detector"""
        assert detector is not None
        assert detector.conf_threshold == 0.5
        assert len(detector.COCO_CLASSES) == 80

    def test_detector_loads_model_if_exists(self, detector):
        """Testa se modelo é carregado quando existe"""
        model_path = MODELS_DIR / "yolov8m.onnx"
        
        if model_path.exists():
            assert detector.session is not None
            assert detector.input_name is not None
            assert detector.output_names is not None
        else:
            # Modo mock se modelo não existe
            assert detector.session is None

    def test_detect_on_empty_frame(self, detector):
        """Testa detecção em frame vazio"""
        # Frame preto
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        detections = detector.detect(frame)
        
        # Deve retornar lista (pode estar vazia ou ter detecções mock)
        assert isinstance(detections, list)

    def test_detect_on_synthetic_frame(self, detector):
        """Testa detecção em frame sintético"""
        # Frame com algum conteúdo
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        detections = detector.detect(frame)
        
        assert isinstance(detections, list)
        
        # Verificar estrutura das detecções
        for det in detections:
            assert hasattr(det, 'class_id')
            assert hasattr(det, 'class_name')
            assert hasattr(det, 'confidence')
            assert hasattr(det, 'bbox')
            assert 0 <= det.confidence <= 1.0

    def test_detection_attributes(self, detector):
        """Testa atributos das detecções"""
        from src.ai.yolo_onnx import Detection
        
        det = Detection(
            class_id=0,
            class_name="person",
            confidence=0.95,
            x1=100,
            y1=100,
            x2=200,
            y2=300
        )
        
        # Testar propriedades
        assert det.bbox == (100, 100, 200, 300)
        assert det.center == (150, 200)
        assert det.area == 100 * 200

    def test_preprocess(self, detector):
        """Testa preprocessamento de frame"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        preprocessed = detector._preprocess(frame)
        
        # Deve ter shape correto para YOLO
        assert preprocessed.shape == (1, 3, 640, 640)
        assert preprocessed.dtype == np.float32
        assert preprocessed.min() >= 0.0
        assert preprocessed.max() <= 1.0

    def test_nms(self, detector):
        """Testa Non-Maximum Suppression"""
        # Criar boxes sobrepostas
        boxes = [
            [100, 100, 200, 200],  # Box 1
            [110, 110, 210, 210],  # Box 2 - sobrepõe Box 1
            [300, 300, 400, 400],  # Box 3 - não sobrepõe
        ]
        scores = [0.9, 0.8, 0.95]
        
        # Aplicar NMS
        indices = detector._nms(boxes, scores, iou_threshold=0.45)
        
        # Deve manter Box 1 (score mais alto que Box 2) e Box 3
        assert len(indices) == 2
        assert 0 in indices  # Box 1
        assert 2 in indices  # Box 3

    def test_mock_detector(self, detector):
        """Testa detector mock quando modelo não existe"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Forçar uso do mock
        detector.session = None
        
        detections = detector._mock_detect(frame)
        
        assert isinstance(detections, list)
        assert len(detections) > 0  # Mock sempre retorna pelo menos 1 detecção


class TestObjectTracker:
    """Testes para rastreador de objetos"""

    @pytest.fixture
    def tracker(self):
        """Fixture para criar tracker"""
        from src.ai.yolo_onnx import ObjectTracker
        return ObjectTracker(max_distance=50, max_disappeared=30)

    @pytest.fixture
    def sample_detections(self):
        """Fixture para criar detecções de exemplo"""
        from src.ai.yolo_onnx import Detection
        
        return [
            Detection(0, "person", 0.9, 100, 100, 150, 200),
            Detection(0, "person", 0.85, 300, 150, 350, 250),
        ]

    def test_tracker_initialization(self, tracker):
        """Testa inicialização do tracker"""
        assert tracker.max_distance == 50
        assert tracker.max_disappeared == 30
        assert len(tracker.tracks) == 0
        assert tracker.next_id == 0

    def test_tracker_first_update(self, tracker, sample_detections):
        """Testa primeira atualização (criar tracks)"""
        detections = tracker.update(sample_detections)
        
        # Deve ter atribuído IDs
        assert len(detections) == 2
        assert detections[0].track_id is not None
        assert detections[1].track_id is not None
        assert detections[0].track_id != detections[1].track_id
        
        # Deve ter criado tracks
        assert len(tracker.tracks) == 2

    def test_tracker_update_same_objects(self, tracker, sample_detections):
        """Testa atualização com mesmos objetos (rastreamento)"""
        from src.ai.yolo_onnx import Detection
        
        # Primeira atualização
        detections1 = tracker.update(sample_detections)
        track_id_1 = detections1[0].track_id
        track_id_2 = detections1[1].track_id
        
        # Segunda atualização com objetos na mesma posição
        detections2 = [
            Detection(0, "person", 0.9, 105, 105, 155, 205),  # Moveu pouco
            Detection(0, "person", 0.85, 305, 155, 355, 255),  # Moveu pouco
        ]
        
        tracked = tracker.update(detections2)
        
        # Deve manter os mesmos IDs
        assert tracked[0].track_id == track_id_1
        assert tracked[1].track_id == track_id_2

    def test_tracker_disappeared_objects(self, tracker, sample_detections):
        """Testa remoção de objetos desaparecidos"""
        # Adicionar objetos
        tracker.update(sample_detections)
        assert len(tracker.tracks) == 2
        
        # Atualizar com lista vazia por mais de max_disappeared frames
        for _ in range(35):
            tracker.update([])
        
        # Tracks devem ter sido removidos
        assert len(tracker.tracks) == 0

    def test_tracker_new_object_appears(self, tracker, sample_detections):
        """Testa aparecimento de novo objeto"""
        from src.ai.yolo_onnx import Detection
        
        # Primeira atualização
        tracker.update(sample_detections)
        initial_count = len(tracker.tracks)
        
        # Nova detecção em posição diferente
        new_detections = sample_detections + [
            Detection(2, "car", 0.95, 500, 300, 600, 400)
        ]
        
        tracked = tracker.update(new_detections)
        
        # Deve ter criado novo track
        assert len(tracker.tracks) == initial_count + 1
        assert len(tracked) == 3


class TestIntegrationONNX:
    """Testes de integração ONNX"""

    def test_end_to_end_detection(self):
        """Testa fluxo completo de detecção com ONNX"""
        from src.ai.yolo_onnx import YoloOnnxDetector, ObjectTracker
        
        model_path = MODELS_DIR / "yolov8m.onnx"
        
        if not model_path.exists():
            pytest.skip("Modelo ONNX não disponível")
        
        # Criar detector e tracker
        detector = YoloOnnxDetector(model_path, conf_threshold=0.3)
        tracker = ObjectTracker()
        
        # Frame de teste
        frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        # Detectar
        detections = detector.detect(frame)
        
        # Rastrear
        tracked = tracker.update(detections)
        
        # Verificar que pipeline funciona
        assert isinstance(detections, list)
        assert isinstance(tracked, list)
        
        for det in tracked:
            assert hasattr(det, 'track_id')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
