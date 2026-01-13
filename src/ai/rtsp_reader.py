"""
Leitor RTSP robusto com FFmpeg e reconexão automática
"""
import logging
import subprocess
import threading
import time
from typing import Optional, Tuple
from queue import Queue
import numpy as np
import cv2

logger = logging.getLogger(__name__)


class RtspReader:
    """Leitor RTSP robusto com reconexão automática e buffering"""

    def __init__(
        self,
        rtsp_url: str,
        camera_id: int = 0,
        target_fps: int = 5,
        target_size: Optional[Tuple[int, int]] = None,
        max_latency: int = 5,
        reconnect_timeout: int = 30,
        buffer_size: int = 2
    ):
        """
        Inicializa leitor RTSP

        Args:
            rtsp_url: URL RTSP da câmera
            camera_id: ID único da câmera
            target_fps: FPS alvo para processamento (faz downsampling se necessário)
            target_size: Tamanho alvo (width, height) ou None para usar resolução original
            max_latency: Latência máxima em segundos
            reconnect_timeout: Timeout de reconexão em segundos
            buffer_size: Tamanho do buffer de frames
        """
        self.rtsp_url = rtsp_url
        self.camera_id = camera_id
        self.target_fps = target_fps
        self.target_size = target_size
        self.max_latency = max_latency
        self.reconnect_timeout = reconnect_timeout
        self.buffer_size = buffer_size

        self.frame_queue: Queue = Queue(maxsize=buffer_size)
        self.is_running = False
        self.is_connected = False
        self.last_frame_time = None
        self.error_count = 0
        self.max_errors = 5
        self.reconnect_count = 0
        
        # Resolução detectada (será preenchida pelo ffprobe)
        self.stream_width: Optional[int] = None
        self.stream_height: Optional[int] = None
        self.stream_fps: Optional[float] = None

        self.reader_thread: Optional[threading.Thread] = None
        self.watchdog_thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Inicia o leitor RTSP"""
        if self.is_running:
            logger.warning(f"Leitor já está rodando para câmera {self.camera_id}")
            return False

        self.is_running = True
        self.error_count = 0

        # Iniciar thread de leitura
        self.reader_thread = threading.Thread(
            target=self._reader_loop,
            daemon=True,
            name=f"RtspReader-{self.camera_id}"
        )
        self.reader_thread.start()

        # Iniciar thread de watchdog
        self.watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name=f"RtspWatchdog-{self.camera_id}"
        )
        self.watchdog_thread.start()

        logger.info(f"Leitor RTSP iniciado para câmera {self.camera_id}")
        return True

    def stop(self):
        """Para o leitor RTSP"""
        self.is_running = False
        self.is_connected = False

        if self.reader_thread:
            self.reader_thread.join(timeout=5)

        if self.watchdog_thread:
            self.watchdog_thread.join(timeout=5)

        logger.info(f"Leitor RTSP parado para câmera {self.camera_id}")

    def get_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Obtém próximo frame do buffer

        Args:
            timeout: Timeout em segundos

        Returns:
            Frame numpy array ou None se timeout
        """
        try:
            frame = self.frame_queue.get(timeout=timeout)
            self.last_frame_time = time.time()
            return frame
        except:
            return None
    
    def frames(self, timeout: float = 1.0):
        """
        Iterator para obter frames continuamente
        
        Uso:
            for frame in reader.frames():
                # processar frame
        """
        while self.is_running:
            frame = self.get_frame(timeout=timeout)
            if frame is not None:
                yield frame
            else:
                # Se timeout, verificar se ainda está rodando
                if not self.is_running:
                    break

    def is_healthy(self) -> bool:
        """Verifica se o leitor está saudável"""
        if not self.is_running:
            return False

        if not self.is_connected:
            return False

        # Verificar timeout de frame
        if self.last_frame_time is None:
            return False

        elapsed = time.time() - self.last_frame_time
        if elapsed > self.max_latency:
            logger.warning(
                f"Câmera {self.camera_id}: timeout de frame ({elapsed:.1f}s)"
            )
            return False

        return True
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do leitor para diagnósticos"""
        return {
            'camera_id': self.camera_id,
            'connected': self.is_connected,
            'healthy': self.is_healthy(),
            'running': self.is_running,
            'reconnect_count': self.reconnect_count,
            'error_count': self.error_count,
            'queue_size': self.frame_queue.qsize(),
            'last_frame_time': self.last_frame_time,
            'stream_resolution': f"{self.stream_width}x{self.stream_height}" if self.stream_width else None,
            'stream_fps': self.stream_fps,
            'target_fps': self.target_fps,
        }
    
    def _probe_stream(self) -> bool:
        """Detecta resolução e FPS do stream RTSP com ffprobe"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate",
            "-of", "default=noprint_wrappers=1",
            self.rtsp_url
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"ffprobe falhou para câmera {self.camera_id}: {result.stderr}")
                return False
            
            # Parse output
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key == 'width':
                        self.stream_width = int(value)
                    elif key == 'height':
                        self.stream_height = int(value)
                    elif key == 'r_frame_rate':
                        # Formato: "30/1" ou "30000/1001"
                        if '/' in value:
                            num, den = value.split('/')
                            self.stream_fps = float(num) / float(den)
            
            if self.stream_width and self.stream_height:
                logger.info(
                    f"Stream detectado para câmera {self.camera_id}: "
                    f"{self.stream_width}x{self.stream_height} @ {self.stream_fps:.1f} FPS"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao detectar stream câmera {self.camera_id}: {e}")
            return False

    def _reader_loop(self):
        """Loop principal de leitura com reconexão automática"""
        backoff = 1
        max_backoff = 60

        while self.is_running:
            try:
                # Detectar resolução do stream antes de ler
                if self.stream_width is None or self.stream_height is None:
                    logger.info(f"Detectando parâmetros do stream câmera {self.camera_id}...")
                    if not self._probe_stream():
                        # Fallback para resolução comum se probe falhar
                        logger.warning(f"Usando resolução padrão 1280x720 para câmera {self.camera_id}")
                        self.stream_width = 1280
                        self.stream_height = 720
                        self.stream_fps = 30.0
                
                self._ffmpeg_read_loop()
                backoff = 1  # Reset backoff on successful connection
                self.error_count = 0  # Reset error count on success

            except Exception as e:
                self.is_connected = False
                self.error_count += 1
                self.reconnect_count += 1

                logger.error(
                    f"Erro ao ler RTSP câmera {self.camera_id}: {e} "
                    f"(tentativa {self.error_count}/{self.max_errors}, reconexões: {self.reconnect_count})"
                )

                if self.error_count >= self.max_errors:
                    logger.critical(
                        f"Câmera {self.camera_id}: limite de erros consecutivos atingido"
                    )
                    # Aguardar mais tempo antes de tentar novamente
                    time.sleep(max_backoff)
                    self.error_count = 0  # Reset para tentar novamente
                    continue

                # Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, 60s (max)
                logger.info(f"Reconectando câmera {self.camera_id} em {backoff}s...")
                time.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

    def _ffmpeg_read_loop(self):
        """Loop de leitura com FFmpeg"""
        # Usar resolução detectada ou target_size
        if self.target_size:
            output_width, output_height = self.target_size
            scale_filter = f"scale={output_width}:{output_height}"
        else:
            output_width = self.stream_width
            output_height = self.stream_height
            scale_filter = None
        
        # Calcular frame skip para atingir target_fps
        if self.stream_fps and self.target_fps:
            frame_skip = max(1, int(self.stream_fps / self.target_fps))
        else:
            frame_skip = 1
        
        # Comando FFmpeg para ler RTSP
        cmd = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", self.rtsp_url,
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
        ]
        
        # Adicionar filtro de escala se necessário
        if scale_filter:
            cmd.extend(["-vf", scale_filter])
        
        cmd.extend([
            "-an",  # Sem áudio
            "-"
        ])

        logger.info(
            f"Iniciando FFmpeg para câmera {self.camera_id}: {self.rtsp_url} "
            f"({output_width}x{output_height}, skip={frame_skip})"
        )

        # CRÍTICO: stderr para DEVNULL para evitar deadlock
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # FIX: evita deadlock
            bufsize=10 * 1024 * 1024
        )

        self.is_connected = True
        frame_count = 0
        processed_count = 0
        last_frame_time = time.time()

        try:
            frame_size = output_width * output_height * 3

            while self.is_running:
                # Ler frame bruto
                frame_data = process.stdout.read(frame_size)

                if len(frame_data) != frame_size:
                    if len(frame_data) == 0:
                        logger.info(f"Stream encerrado para câmera {self.camera_id}")
                    else:
                        logger.warning(
                            f"Frame incompleto para câmera {self.camera_id}: "
                            f"{len(frame_data)} bytes (esperado {frame_size})"
                        )
                    break

                frame_count += 1
                
                # FPS pacing: pular frames se necessário
                if frame_count % frame_skip != 0:
                    continue
                
                # Converter para numpy array
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = frame.reshape((output_height, output_width, 3))

                # Adicionar ao buffer (descartar se cheio)
                try:
                    self.frame_queue.put_nowait(frame)
                    processed_count += 1
                    
                    # Log periódico com FPS real
                    if processed_count % 50 == 0:
                        elapsed = time.time() - last_frame_time
                        actual_fps = 50 / elapsed if elapsed > 0 else 0
                        logger.debug(
                            f"Câmera {self.camera_id}: {processed_count} frames processados "
                            f"({frame_count} capturados, {actual_fps:.1f} FPS)"
                        )
                        last_frame_time = time.time()

                except:
                    # Buffer cheio, descartar frame antigo e adicionar novo
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except:
                        pass

        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()

            self.is_connected = False
            logger.info(
                f"Conexão FFmpeg fechada para câmera {self.camera_id} "
                f"({processed_count} processados / {frame_count} capturados, "
                f"reconexões: {self.reconnect_count})"
            )

    def _watchdog_loop(self):
        """Loop de watchdog para monitorar saúde"""
        check_interval = 5

        while self.is_running:
            time.sleep(check_interval)

            if not self.is_healthy():
                logger.warning(
                    f"Watchdog: câmera {self.camera_id} não está saudável"
                )

            # Limpar buffer se muito grande
            if self.frame_queue.qsize() > self.buffer_size * 2:
                logger.warning(
                    f"Buffer cheio para câmera {self.camera_id}: "
                    f"{self.frame_queue.qsize()} frames"
                )
                try:
                    while self.frame_queue.qsize() > self.buffer_size:
                        self.frame_queue.get_nowait()
                except:
                    pass


class RtspReaderPool:
    """Pool de leitores RTSP para múltiplas câmeras"""

    def __init__(self):
        self.readers: dict = {}
        self.lock = threading.Lock()

    def add_camera(self, camera_id: int, rtsp_url: str) -> bool:
        """Adiciona câmera ao pool"""
        with self.lock:
            if camera_id in self.readers:
                logger.warning(f"Câmera {camera_id} já existe no pool")
                return False

            reader = RtspReader(rtsp_url, camera_id)
            if reader.start():
                self.readers[camera_id] = reader
                return True

            return False

    def remove_camera(self, camera_id: int) -> bool:
        """Remove câmera do pool"""
        with self.lock:
            if camera_id not in self.readers:
                return False

            reader = self.readers[camera_id]
            reader.stop()
            del self.readers[camera_id]
            return True

    def get_frame(self, camera_id: int, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Obtém frame de câmera"""
        with self.lock:
            if camera_id not in self.readers:
                return None

            return self.readers[camera_id].get_frame(timeout)

    def get_health_status(self) -> dict:
        """Retorna status de saúde de todas as câmeras"""
        status = {}
        with self.lock:
            for camera_id, reader in self.readers.items():
                status[camera_id] = {
                    'connected': reader.is_connected,
                    'healthy': reader.is_healthy(),
                    'errors': reader.error_count,
                    'queue_size': reader.frame_queue.qsize()
                }
        return status

    def stop_all(self):
        """Para todos os leitores"""
        with self.lock:
            for reader in self.readers.values():
                reader.stop()
            self.readers.clear()
