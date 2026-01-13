"""
Testes para VideoProcessor com RtspReader
"""
import pytest
import time
import numpy as np
from src.ai.video_processor import VideoProcessor, Detection, Frame


class TestVideoProcessor:
    """Testes para VideoProcessor refatorado com RtspReader"""

    @pytest.fixture
    def mock_rtsp_url(self):
        """URL RTSP de teste"""
        # Stream público para testes
        return "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"

    @pytest.fixture
    def processor(self, mock_rtsp_url):
        """Fixture para criar VideoProcessor"""
        proc = VideoProcessor(
            rtsp_url=mock_rtsp_url,
            camera_id=1,
            target_fps=2,
            target_size=(640, 480)
        )
        yield proc
        # Cleanup
        if proc.is_running:
            proc.stop()
            proc.disconnect()

    def test_processor_initialization(self, processor):
        """Testa inicialização do VideoProcessor"""
        assert processor.camera_id == 1
        assert processor.target_fps == 2
        assert processor.target_size == (640, 480)
        assert not processor.is_running
        assert processor.rtsp_reader is not None

    def test_processor_connect_disconnect(self, processor):
        """Testa conexão e desconexão"""
        # Conectar
        connected = processor.connect()
        
        if connected:
            assert processor.rtsp_reader.is_running
            time.sleep(1)
            
            # Desconectar
            processor.disconnect()
            time.sleep(0.5)
            assert not processor.rtsp_reader.is_running

    def test_processor_health_check(self, processor):
        """Testa verificação de saúde do processador"""
        # Antes de conectar
        assert not processor.is_healthy()
        
        # Após conectar
        if processor.connect():
            time.sleep(1)
            # Saúde depende se stream está funcionando
            health = processor.is_healthy()
            assert isinstance(health, bool)
            processor.disconnect()

    def test_processor_get_stats(self, processor):
        """Testa obtenção de estatísticas"""
        stats = processor.get_stats()
        
        assert isinstance(stats, dict)
        assert 'camera_id' in stats
        assert stats['camera_id'] == 1
        assert 'running' in stats
        assert 'frame_id' in stats

    def test_process_frame(self, processor):
        """Testa processamento de um frame"""
        # Criar frame de teste
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Processar
        processed = processor.process_frame(test_frame)
        
        assert isinstance(processed, Frame)
        assert processed.frame_id >= 0
        assert isinstance(processed.detections, list)
        assert isinstance(processed.motion_detected, bool)
        assert processed.raw_frame is not None

    def test_processor_start_stop(self, processor):
        """Testa iniciar e parar processamento em thread"""
        # Iniciar
        processor.start()
        time.sleep(2)
        
        assert processor.is_running
        
        # Parar
        processor.stop()
        time.sleep(1)
        
        assert not processor.is_running

    def test_processor_get_frame(self, processor):
        """Testa obtenção de frames processados da fila"""
        processor.start()
        
        try:
            # Aguardar alguns frames
            time.sleep(3)
            
            # Tentar obter frame processado
            frame = processor.get_frame(timeout=5.0)
            
            if frame:
                assert isinstance(frame, Frame)
                assert frame.timestamp is not None
                assert isinstance(frame.detections, list)
        
        finally:
            processor.stop()

    def test_processor_runs_continuously(self, processor):
        """Testa que processador roda continuamente e não trava"""
        processor.start()
        
        try:
            frame_count = 0
            max_wait = 10  # segundos
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                frame = processor.get_frame(timeout=2.0)
                if frame:
                    frame_count += 1
                    if frame_count >= 5:
                        break
                time.sleep(0.1)
            
            # Deve ter recebido pelo menos alguns frames
            assert frame_count > 0, "Nenhum frame foi processado"
        
        finally:
            processor.stop()


class TestDetection:
    """Testes para dataclass Detection"""

    def test_detection_creation(self):
        """Testa criação de Detection"""
        det = Detection(
            class_id=0,
            class_name="person",
            confidence=0.95,
            bbox=(100, 100, 200, 200),
            track_id=42
        )
        
        assert det.class_id == 0
        assert det.class_name == "person"
        assert det.confidence == 0.95
        assert det.bbox == (100, 100, 200, 200)
        assert det.track_id == 42


class TestFrame:
    """Testes para dataclass Frame"""

    def test_frame_creation(self):
        """Testa criação de Frame"""
        from datetime import datetime
        
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        frame = Frame(
            timestamp=datetime.now(),
            frame_id=123,
            detections=[],
            motion_detected=True,
            raw_frame=test_frame
        )
        
        assert frame.frame_id == 123
        assert frame.motion_detected == True
        assert len(frame.detections) == 0
        assert frame.raw_frame is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
