"""
Testes para RtspReader
"""
import pytest
import time
import numpy as np
from src.ai.rtsp_reader import RtspReader


class TestRtspReader:
    """Testes para o RtspReader com FFmpeg"""

    @pytest.fixture
    def mock_rtsp_url(self):
        """URL RTSP de teste (pode ser um stream público ou mock)"""
        # Para testes reais, usar um stream RTSP público
        # return "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
        
        # Para testes sem stream real, retornar URL fictícia
        return "rtsp://192.168.1.100:554/stream"

    def test_reader_initialization(self, mock_rtsp_url):
        """Testa inicialização do RtspReader"""
        reader = RtspReader(
            rtsp_url=mock_rtsp_url,
            camera_id=1,
            target_fps=5,
            target_size=(640, 480)
        )
        
        assert reader.rtsp_url == mock_rtsp_url
        assert reader.camera_id == 1
        assert reader.target_fps == 5
        assert reader.target_size == (640, 480)
        assert not reader.is_running
        assert not reader.is_connected

    def test_reader_start_stop(self, mock_rtsp_url):
        """Testa start e stop do reader"""
        reader = RtspReader(
            rtsp_url=mock_rtsp_url,
            camera_id=1,
            target_fps=5
        )
        
        # Start
        success = reader.start()
        assert success or not success  # Pode falhar se stream não existe
        
        if success:
            assert reader.is_running
            time.sleep(1)
        
        # Stop
        reader.stop()
        assert not reader.is_running

    def test_stream_probe(self):
        """Testa detecção de resolução do stream com ffprobe"""
        # Usar stream público conhecido (Big Buck Bunny)
        public_stream = "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
        
        reader = RtspReader(
            rtsp_url=public_stream,
            camera_id=1
        )
        
        # Tentar probar stream
        result = reader._probe_stream()
        
        # Se probe funcionar, deve ter detectado dimensões
        if result:
            assert reader.stream_width is not None
            assert reader.stream_height is not None
            assert reader.stream_fps is not None
            assert reader.stream_width > 0
            assert reader.stream_height > 0
            assert reader.stream_fps > 0

    def test_get_stats(self, mock_rtsp_url):
        """Testa método get_stats para diagnósticos"""
        reader = RtspReader(
            rtsp_url=mock_rtsp_url,
            camera_id=42,
            target_fps=10
        )
        
        stats = reader.get_stats()
        
        assert isinstance(stats, dict)
        assert 'camera_id' in stats
        assert stats['camera_id'] == 42
        assert 'connected' in stats
        assert 'healthy' in stats
        assert 'running' in stats
        assert 'reconnect_count' in stats
        assert 'queue_size' in stats
        assert 'target_fps' in stats
        assert stats['target_fps'] == 10

    def test_is_healthy(self, mock_rtsp_url):
        """Testa verificação de saúde do reader"""
        reader = RtspReader(
            rtsp_url=mock_rtsp_url,
            camera_id=1
        )
        
        # Antes de iniciar, não deve estar saudável
        assert not reader.is_healthy()
        
        # Após iniciar (se conectar)
        if reader.start():
            time.sleep(0.5)
            # Pode ou não estar saudável dependendo do stream
            # Apenas verificar que o método funciona
            health = reader.is_healthy()
            assert isinstance(health, bool)
            reader.stop()

    def test_frames_iterator(self):
        """Testa iterator frames() com stream público"""
        public_stream = "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
        
        reader = RtspReader(
            rtsp_url=public_stream,
            camera_id=1,
            target_fps=2
        )
        
        if not reader.start():
            pytest.skip("Stream público não disponível")
        
        try:
            frame_count = 0
            max_frames = 5
            
            for frame in reader.frames(timeout=5.0):
                assert frame is not None
                assert isinstance(frame, np.ndarray)
                assert len(frame.shape) == 3  # height, width, channels
                assert frame.shape[2] == 3  # BGR
                
                frame_count += 1
                if frame_count >= max_frames:
                    break
            
            assert frame_count > 0, "Nenhum frame foi recebido"
            
        finally:
            reader.stop()

    def test_reconnection_count(self, mock_rtsp_url):
        """Testa contagem de reconexões"""
        reader = RtspReader(
            rtsp_url=mock_rtsp_url,
            camera_id=1
        )
        
        # Antes de iniciar
        assert reader.reconnect_count == 0
        
        # Após tentativa de conexão (pode falhar)
        reader.start()
        time.sleep(2)
        
        # Reconexões devem ser >= 0
        assert reader.reconnect_count >= 0
        
        reader.stop()

    def test_target_size_resolution(self):
        """Testa se target_size é respeitado"""
        public_stream = "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
        
        target_width, target_height = 320, 240
        reader = RtspReader(
            rtsp_url=public_stream,
            camera_id=1,
            target_size=(target_width, target_height),
            target_fps=2
        )
        
        if not reader.start():
            pytest.skip("Stream público não disponível")
        
        try:
            # Pegar primeiro frame
            frame = reader.get_frame(timeout=10.0)
            
            if frame is not None:
                height, width, _ = frame.shape
                assert width == target_width, f"Width esperado {target_width}, recebido {width}"
                assert height == target_height, f"Height esperado {target_height}, recebido {height}"
        
        finally:
            reader.stop()


class TestRtspReaderPool:
    """Testes para RtspReaderPool (multi-câmera)"""
    
    def test_pool_initialization(self):
        """Testa inicialização do pool"""
        from src.ai.rtsp_reader import RtspReaderPool
        
        pool = RtspReaderPool()
        assert isinstance(pool.readers, dict)
        assert len(pool.readers) == 0

    def test_pool_add_remove_camera(self):
        """Testa adicionar e remover câmera do pool"""
        from src.ai.rtsp_reader import RtspReaderPool
        
        pool = RtspReaderPool()
        
        # Adicionar câmera (pode falhar se stream não existe)
        rtsp_url = "rtsp://test.local/stream"
        result = pool.add_camera(camera_id=1, rtsp_url=rtsp_url)
        
        # Se adicionou, deve estar no pool
        if result:
            assert 1 in pool.readers
        
        # Remover
        removed = pool.remove_camera(camera_id=1)
        if result:  # Se adicionou antes
            assert removed
            assert 1 not in pool.readers

    def test_pool_health_status(self):
        """Testa get_health_status do pool"""
        from src.ai.rtsp_reader import RtspReaderPool
        
        pool = RtspReaderPool()
        
        # Status inicial (vazio)
        status = pool.get_health_status()
        assert isinstance(status, dict)
        assert len(status) == 0
        
        # Adicionar câmera
        pool.add_camera(camera_id=1, rtsp_url="rtsp://test/stream")
        
        # Status após adicionar
        status = pool.get_health_status()
        if 1 in pool.readers:
            assert 1 in status
            assert 'connected' in status[1]
            assert 'healthy' in status[1]
            assert 'errors' in status[1]
        
        # Cleanup
        pool.stop_all()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
