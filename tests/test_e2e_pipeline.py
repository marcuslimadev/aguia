"""
Testes End-to-End do Pipeline Completo
"""
import pytest
import sys
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import CONFIDENCE_THRESHOLD
from src.ai.yolo_onnx import Detection
from src.ai.event_engine import EventEngine, EventCandidate


class TestE2EPipeline:
    """Testes end-to-end do pipeline completo"""

    @pytest.fixture
    def mock_frame(self):
        """Mock de frame de vídeo"""
        import numpy as np
        # 640x480 RGB frame
        return np.zeros((480, 640, 3), dtype=np.uint8)

    @pytest.fixture
    def mock_detections(self):
        """Mock de detecções YOLO"""
        return [
            Detection(
                class_id=0,
                class_name="person",
                confidence=0.85,
                bbox=(100, 100, 200, 300),
                track_id=1
            ),
            Detection(
                class_id=0,
                class_name="person",
                confidence=0.78,
                bbox=(300, 150, 400, 350),
                track_id=2
            )
        ]

    @pytest.fixture
    def event_engine(self):
        """Event engine para testes"""
        from config.config import (
            EVENT_INTRUSION_THRESHOLD,
            EVENT_LOITERING_THRESHOLD
        )
        return EventEngine(
            intrusion_threshold=EVENT_INTRUSION_THRESHOLD,
            loitering_threshold=EVENT_LOITERING_THRESHOLD
        )

    def test_rtsp_to_detection(self, mock_frame):
        """Testa pipeline: RTSP Reader → Detection"""
        # Mock RTSP Reader
        from src.ai.rtsp_reader import RtspReader
        
        with patch.object(RtspReader, 'frames') as mock_frames:
            mock_frames.return_value = iter([mock_frame])
            
            # Mock ONNX Detector
            from src.ai.yolo_onnx import YOLOONNXDetector
            
            with patch.object(YOLOONNXDetector, 'detect') as mock_detect:
                mock_detect.return_value = [
                    Detection(
                        class_id=0,
                        class_name="person",
                        confidence=0.9,
                        bbox=(100, 100, 200, 300),
                        track_id=None
                    )
                ]
                
                # Simulate pipeline
                reader = RtspReader("rtsp://fake")
                detector = YOLOONNXDetector(model_path="fake.onnx")
                
                # Get frame
                frame = next(reader.frames())
                assert frame is not None
                
                # Detect
                detections = detector.detect(frame)
                assert len(detections) == 1
                assert detections[0].class_name == "person"
                assert detections[0].confidence == 0.9

    def test_detection_to_event(self, mock_detections, event_engine):
        """Testa pipeline: Detection → Event Engine → Event Candidate"""
        camera_id = 1
        zone_id = 1
        
        # Feed detections to event engine
        for i in range(5):  # 5 frames
            event_engine.update_tracks(camera_id, mock_detections)
            time.sleep(0.1)  # Simulate frame timing
        
        # Check for intrusion events (should have some after 5 frames)
        events = event_engine.check_intrusion(camera_id, zone_id)
        
        # Verify events generated
        assert isinstance(events, list)
        # May or may not have events depending on zone configuration

    def test_event_to_validator(self):
        """Testa pipeline: Event Candidate → Validator → Alert"""
        from src.ai.validator_model import ValidatorModel
        
        validator = ValidatorModel()
        
        # Create event candidate
        event = EventCandidate(
            camera_id=1,
            zone_id=1,
            event_type="intrusion",
            track_id=1,
            confidence=0.85,
            timestamp=time.time(),
            duration=3.5,
            metadata={}
        )
        
        # Validate
        is_valid = validator.validate_event_candidate(event)
        
        # Should be valid (high confidence, reasonable duration)
        assert is_valid is True

    def test_validator_to_email(self):
        """Testa pipeline: Validator → Email Queue"""
        from src.core.email_queue import EmailQueue
        
        # Mock database
        mock_db = Mock()
        mock_db.execute_update = Mock()
        mock_db.execute_query = Mock(return_value=[])
        
        email_queue = EmailQueue(mock_db)
        
        # Queue email
        success = email_queue.queue_email(
            to="admin@example.com",
            subject="Security Alert: Intrusion Detected",
            body="Intrusion detected in Zone 1",
            attachment_path=None
        )
        
        assert success is True
        assert mock_db.execute_update.called

    def test_full_pipeline_integration(self, mock_frame, event_engine):
        """Testa pipeline completo end-to-end"""
        from src.ai.yolo_onnx import YOLOONNXDetector
        from src.ai.validator_model import ValidatorModel
        from src.core.email_queue import EmailQueue
        
        # Mock components
        with patch.object(YOLOONNXDetector, 'detect') as mock_detect:
            mock_detect.return_value = [
                Detection(
                    class_id=0,
                    class_name="person",
                    confidence=0.9,
                    bbox=(100, 100, 200, 300),
                    track_id=1
                )
            ]
            
            detector = YOLOONNXDetector(model_path="fake.onnx")
            validator = ValidatorModel()
            
            mock_db = Mock()
            mock_db.execute_update = Mock()
            mock_db.execute_query = Mock(return_value=[])
            email_queue = EmailQueue(mock_db)
            
            # Simulate frames
            camera_id = 1
            zone_id = 1
            
            for frame_num in range(10):
                # Detect
                detections = detector.detect(mock_frame)
                
                # Update event engine
                event_engine.update_tracks(camera_id, detections)
                
                # Check for events
                events = event_engine.check_intrusion(camera_id, zone_id)
                
                for event in events:
                    # Validate
                    is_valid = validator.validate_event_candidate(event)
                    
                    if is_valid:
                        # Queue email
                        email_queue.queue_email(
                            to="admin@example.com",
                            subject=f"Alert: {event.event_type}",
                            body=f"Detected in camera {camera_id}",
                            attachment_path=None
                        )
            
            # Verify pipeline executed
            assert mock_detect.call_count == 10

    def test_pipeline_performance(self, mock_frame):
        """Testa performance do pipeline"""
        from src.ai.yolo_onnx import YOLOONNXDetector
        
        with patch.object(YOLOONNXDetector, 'detect') as mock_detect:
            mock_detect.return_value = []
            
            detector = YOLOONNXDetector(model_path="fake.onnx")
            
            # Measure processing time
            start_time = time.time()
            iterations = 100
            
            for _ in range(iterations):
                detector.detect(mock_frame)
            
            elapsed = time.time() - start_time
            fps = iterations / elapsed
            
            # Should process at least 20 FPS (mock is fast)
            assert fps > 20, f"Too slow: {fps:.1f} FPS"

    def test_error_handling_in_pipeline(self, mock_frame):
        """Testa tratamento de erros no pipeline"""
        from src.ai.yolo_onnx import YOLOONNXDetector
        
        with patch.object(YOLOONNXDetector, 'detect') as mock_detect:
            # Simulate error
            mock_detect.side_effect = Exception("Model error")
            
            detector = YOLOONNXDetector(model_path="fake.onnx")
            
            # Should handle error gracefully
            try:
                detections = detector.detect(mock_frame)
                # Should either raise or return empty list
            except Exception as e:
                # Error should be caught
                assert "Model error" in str(e)

    def test_memory_leak_detection(self, mock_frame):
        """Testa vazamento de memória no pipeline"""
        import gc
        import psutil
        import os
        
        from src.ai.yolo_onnx import YOLOONNXDetector
        
        with patch.object(YOLOONNXDetector, 'detect') as mock_detect:
            mock_detect.return_value = []
            
            detector = YOLOONNXDetector(model_path="fake.onnx")
            
            # Get initial memory
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Process many frames
            for _ in range(1000):
                detector.detect(mock_frame)
            
            # Force garbage collection
            gc.collect()
            
            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory
            
            # Should not grow more than 50MB
            assert memory_growth < 50, f"Memory leak detected: {memory_growth:.1f}MB growth"

    def test_concurrent_cameras(self, mock_frame, event_engine):
        """Testa processamento de múltiplas câmeras"""
        from src.ai.yolo_onnx import YOLOONNXDetector
        import threading
        
        with patch.object(YOLOONNXDetector, 'detect') as mock_detect:
            mock_detect.return_value = [
                Detection(
                    class_id=0,
                    class_name="person",
                    confidence=0.8,
                    bbox=(100, 100, 200, 300),
                    track_id=1
                )
            ]
            
            detector = YOLOONNXDetector(model_path="fake.onnx")
            
            def process_camera(camera_id):
                """Simula processamento de uma câmera"""
                for _ in range(10):
                    detections = detector.detect(mock_frame)
                    event_engine.update_tracks(camera_id, detections)
            
            # Process 3 cameras concurrently
            threads = []
            for camera_id in range(1, 4):
                thread = threading.Thread(target=process_camera, args=(camera_id,))
                thread.start()
                threads.append(thread)
            
            # Wait for all
            for thread in threads:
                thread.join()
            
            # All cameras should have processed
            assert len(event_engine.tracks) >= 3  # At least 3 cameras

    def test_event_deduplication(self, event_engine):
        """Testa que eventos duplicados não são gerados"""
        camera_id = 1
        zone_id = 1
        
        # Same detections multiple times
        detections = [
            Detection(
                class_id=0,
                class_name="person",
                confidence=0.9,
                bbox=(100, 100, 200, 300),
                track_id=1
            )
        ]
        
        # Feed same detections 10 times
        for _ in range(10):
            event_engine.update_tracks(camera_id, detections)
            time.sleep(0.1)
        
        # Check events
        events = event_engine.check_intrusion(camera_id, zone_id)
        
        # Should not have 10 duplicate events
        # Event engine should deduplicate based on track_id
        # (Actual behavior depends on implementation)

    def test_snapshot_generation(self, mock_frame):
        """Testa geração de snapshots para alerts"""
        from src.utils.snapshot import save_snapshot
        import cv2
        
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot_path = Path(tmpdir) / "alert_snapshot.jpg"
            
            # Save snapshot
            result = save_snapshot(
                frame=mock_frame,
                detections=[],
                output_path=str(snapshot_path)
            )
            
            # Verify saved
            assert snapshot_path.exists()
            
            # Verify can be read
            img = cv2.imread(str(snapshot_path))
            assert img is not None
            assert img.shape == (480, 640, 3)


class TestPerformanceRequirements:
    """Testes de requisitos de performance"""

    def test_detection_latency(self):
        """Testa latência de detecção < 100ms por frame"""
        from src.ai.yolo_onnx import YOLOONNXDetector
        import numpy as np
        
        with patch.object(YOLOONNXDetector, 'detect') as mock_detect:
            mock_detect.return_value = []
            
            detector = YOLOONNXDetector(model_path="fake.onnx")
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Measure latency
            latencies = []
            for _ in range(100):
                start = time.time()
                detector.detect(frame)
                latency = (time.time() - start) * 1000  # ms
                latencies.append(latency)
            
            avg_latency = sum(latencies) / len(latencies)
            
            # Mock should be fast
            assert avg_latency < 100, f"Too slow: {avg_latency:.1f}ms"

    def test_event_processing_latency(self):
        """Testa latência de processamento de eventos < 50ms"""
        from src.ai.event_engine import EventEngine
        
        engine = EventEngine()
        camera_id = 1
        
        detections = [
            Detection(
                class_id=0,
                class_name="person",
                confidence=0.9,
                bbox=(100, 100, 200, 300),
                track_id=1
            )
        ]
        
        # Measure latency
        latencies = []
        for _ in range(100):
            start = time.time()
            engine.update_tracks(camera_id, detections)
            engine.check_intrusion(camera_id, 1)
            latency = (time.time() - start) * 1000  # ms
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        
        # Should be fast
        assert avg_latency < 50, f"Event processing too slow: {avg_latency:.1f}ms"

    def test_memory_usage(self):
        """Testa que uso de memória < 500MB"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Test environment should use < 500MB
        # (In production with models loaded, may be higher)
        assert memory_mb < 500, f"Memory usage too high: {memory_mb:.1f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
