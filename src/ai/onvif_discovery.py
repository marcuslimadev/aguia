"""
Descoberta e integração ONVIF de câmeras
"""
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import socket
import threading
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class OnvifCamera:
    """Câmera ONVIF descoberta"""
    hostname: str
    ip_address: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    rtsp_uri: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    firmware: Optional[str] = None
    mac_address: Optional[str] = None

    @property
    def onvif_url(self) -> str:
        """URL ONVIF do dispositivo"""
        return f"http://{self.ip_address}:{self.port}/onvif/device_service"

    @property
    def stream_uri(self) -> str:
        """URI de stream RTSP"""
        if self.rtsp_uri:
            return self.rtsp_uri
        return f"rtsp://{self.ip_address}:554/stream1"

    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'rtsp_uri': self.rtsp_uri,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'firmware': self.firmware,
            'mac_address': self.mac_address,
            'onvif_url': self.onvif_url,
            'stream_uri': self.stream_uri
        }


class OnvifDiscovery:
    """Descoberta de câmeras ONVIF na rede"""

    def __init__(self, timeout: int = 5):
        """
        Inicializa descoberta ONVIF

        Args:
            timeout: Timeout para descoberta em segundos
        """
        self.timeout = timeout
        self.discovered_cameras: List[OnvifCamera] = []
        self.is_running = False

    def discover_cameras(self, subnet: Optional[str] = None) -> List[OnvifCamera]:
        """
        Descobre câmeras ONVIF na rede

        Args:
            subnet: Subnet para scan (ex: 192.168.1.0/24)
                   Se None, usa subnet local

        Returns:
            Lista de câmeras descobertas
        """
        try:
            logger.info("Iniciando descoberta ONVIF...")

            if subnet is None:
                subnet = self._get_local_subnet()

            if not subnet:
                logger.warning("Não foi possível determinar subnet local")
                return []

            # Gerar IPs para scan
            ips = self._generate_ips(subnet)

            # Scan paralelo
            cameras = []
            threads = []

            for ip in ips:
                thread = threading.Thread(
                    target=self._scan_ip,
                    args=(ip, cameras),
                    daemon=True
                )
                threads.append(thread)
                thread.start()

                # Limitar threads simultâneas
                if len(threads) >= 10:
                    for t in threads:
                        t.join(timeout=1)
                    threads = [t for t in threads if t.is_alive()]

            # Aguardar conclusão
            for thread in threads:
                thread.join(timeout=self.timeout)

            self.discovered_cameras = cameras
            logger.info(f"✓ Descoberta concluída: {len(cameras)} câmeras encontradas")

            return cameras

        except Exception as e:
            logger.error(f"Erro ao descobrir câmeras: {e}")
            return []

    def _scan_ip(self, ip: str, cameras: List):
        """Tenta conectar a IP e obter informações ONVIF"""
        try:
            # Tentar conectar na porta ONVIF padrão (8080)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            result = sock.connect_ex((ip, 8080))
            sock.close()

            if result == 0:
                # Porta aberta, tentar obter informações
                camera = self._get_camera_info(ip)

                if camera:
                    cameras.append(camera)
                    logger.info(f"✓ Câmera encontrada: {ip}")

        except Exception as e:
            logger.debug(f"Erro ao scanear {ip}: {e}")

    def _get_camera_info(self, ip: str) -> Optional[OnvifCamera]:
        """Obtém informações de câmera ONVIF"""
        try:
            # Aqui você implementaria a chamada real ao ONVIF
            # Por enquanto, retorna câmera mock

            camera = OnvifCamera(
                hostname=f"camera-{ip.split('.')[-1]}",
                ip_address=ip,
                port=8080,
                model="Generic ONVIF Camera",
                manufacturer="Unknown",
                firmware="1.0.0"
            )

            return camera

        except Exception as e:
            logger.debug(f"Erro ao obter info de {ip}: {e}")
            return None

    def _get_local_subnet(self) -> Optional[str]:
        """Obtém subnet local"""
        try:
            # Conectar a um servidor externo para determinar IP local
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()

            # Extrair subnet
            parts = local_ip.split('.')
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

            logger.info(f"Subnet local: {subnet}")
            return subnet

        except Exception as e:
            logger.error(f"Erro ao obter subnet local: {e}")
            return None

    @staticmethod
    def _generate_ips(subnet: str) -> List[str]:
        """Gera lista de IPs para subnet"""
        try:
            # Parse subnet (ex: 192.168.1.0/24)
            parts = subnet.split('/')
            base_ip = parts[0]
            cidr = int(parts[1]) if len(parts) > 1 else 24

            # Calcular range
            base_parts = base_ip.split('.')
            base_num = (int(base_parts[0]) << 24) + (int(base_parts[1]) << 16) + \
                       (int(base_parts[2]) << 8) + int(base_parts[3])

            # Para /24, gerar IPs de .1 a .254
            if cidr == 24:
                ips = []
                for i in range(1, 255):
                    ip_num = (base_num & 0xFFFFFF00) + i
                    ip = f"{(ip_num >> 24) & 0xFF}.{(ip_num >> 16) & 0xFF}." \
                         f"{(ip_num >> 8) & 0xFF}.{ip_num & 0xFF}"
                    ips.append(ip)
                return ips

            return []

        except Exception as e:
            logger.error(f"Erro ao gerar IPs: {e}")
            return []

    def add_camera_manually(
        self,
        ip_address: str,
        port: int = 8080,
        username: Optional[str] = None,
        password: Optional[str] = None,
        rtsp_uri: Optional[str] = None
    ) -> OnvifCamera:
        """Adiciona câmera manualmente"""
        camera = OnvifCamera(
            hostname=f"camera-{ip_address.split('.')[-1]}",
            ip_address=ip_address,
            port=port,
            username=username,
            password=password,
            rtsp_uri=rtsp_uri
        )

        self.discovered_cameras.append(camera)
        logger.info(f"✓ Câmera adicionada manualmente: {ip_address}")

        return camera

    def get_discovered_cameras(self) -> List[OnvifCamera]:
        """Retorna câmeras descobertas"""
        return self.discovered_cameras

    def clear_discovered_cameras(self):
        """Limpa lista de câmeras descobertas"""
        self.discovered_cameras.clear()


class OnvifPresets:
    """Presets de câmeras ONVIF"""

    PRESETS = {
        'hikvision': {
            'name': 'Hikvision',
            'ports': [8080, 8000],
            'default_user': 'admin',
            'default_pass': '12345',
            'rtsp_path': '/Streaming/Channels/101'
        },
        'dahua': {
            'name': 'Dahua',
            'ports': [8080, 8000],
            'default_user': 'admin',
            'default_pass': 'admin',
            'rtsp_path': '/stream/ch0'
        },
        'uniview': {
            'name': 'Uniview',
            'ports': [8080, 8000],
            'default_user': 'admin',
            'default_pass': 'admin',
            'rtsp_path': '/stream/ch0'
        },
        'axis': {
            'name': 'Axis',
            'ports': [80, 8080],
            'default_user': 'root',
            'default_pass': 'pass',
            'rtsp_path': '/axis-media/media.amp'
        },
        'generic': {
            'name': 'Generic ONVIF',
            'ports': [8080, 8000, 80],
            'default_user': 'admin',
            'default_pass': 'admin',
            'rtsp_path': '/stream1'
        }
    }

    @classmethod
    def get_preset(cls, brand: str) -> Optional[dict]:
        """Obtém preset para marca"""
        return cls.PRESETS.get(brand.lower())

    @classmethod
    def get_all_presets(cls) -> dict:
        """Retorna todos os presets"""
        return cls.PRESETS

    @classmethod
    def try_preset(
        cls,
        ip_address: str,
        brand: str,
        custom_user: Optional[str] = None,
        custom_pass: Optional[str] = None
    ) -> Optional[OnvifCamera]:
        """Tenta conectar usando preset"""
        preset = cls.get_preset(brand)

        if not preset:
            return None

        username = custom_user or preset.get('default_user')
        password = custom_pass or preset.get('default_pass')

        # Tentar portas
        for port in preset.get('ports', [8080]):
            try:
                camera = OnvifCamera(
                    hostname=f"{brand}-{ip_address.split('.')[-1]}",
                    ip_address=ip_address,
                    port=port,
                    username=username,
                    password=password,
                    rtsp_uri=f"rtsp://{ip_address}:{554}{preset.get('rtsp_path', '/stream1')}",
                    manufacturer=preset.get('name')
                )

                # Verificar conectividade
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip_address, port))
                sock.close()

                if result == 0:
                    logger.info(f"✓ Preset {brand} funcionou para {ip_address}:{port}")
                    return camera

            except Exception as e:
                logger.debug(f"Erro ao tentar preset {brand} em {ip_address}:{port}: {e}")

        return None
