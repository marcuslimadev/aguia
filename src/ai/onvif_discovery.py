"""
Descoberta e integração ONVIF de câmeras + Intelbras Cloud P2P
"""
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import socket
import threading
import time
import requests
import json
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def discover_intelbras_p2p(device_id: str, device_password: str, cloud_user: Optional[str] = None) -> Optional[str]:
    """
    Connect to Intelbras camera via Cloud/P2P
    
    Args:
        device_id: Device serial number (e.g., DTR0004547751)
        device_password: Admin password for device
        cloud_user: Optional Intelbras Cloud username
        
    Returns:
        RTSP URL if successful, None otherwise
    """
    try:
        logger.info(f"Connecting to Intelbras device {device_id}...")
        
        # Method 1: Try ONVIF discovery on local network first
        # Many Intelbras cameras support ONVIF
        onvif_cameras = discover_onvif_cameras(timeout=10)
        for cam in onvif_cameras:
            if device_id in str(cam.get('serial', '')):
                logger.info(f"✓ Found device {device_id} via ONVIF at {cam['ip']}")
                rtsp_url = f"rtsp://admin:{device_password}@{cam['ip']}:554/cam/realmonitor?channel=1&subtype=0"
                return rtsp_url
        
        # Method 2: Try Intelbras Cloud API
        # Note: This is reverse-engineered from Guardian app
        # The actual API endpoint might vary
        cloud_endpoints = [
            "https://cloud.intelbras.com.br/api/v1",
            "https://p2p.intelbras.com.br/api",
            "https://guardian.intelbras.com/api"
        ]
        
        for endpoint in cloud_endpoints:
            try:
                # Try to get device stream URL from cloud
                payload = {
                    "device_id": device_id,
                    "password": device_password
                }
                if cloud_user:
                    payload["username"] = cloud_user
                
                response = requests.post(
                    f"{endpoint}/device/stream",
                    json=payload,
                    timeout=10,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "rtsp_url" in data:
                        logger.info(f"✓ Got P2P URL from {endpoint}")
                        return data["rtsp_url"]
                    elif "p2p_url" in data:
                        return data["p2p_url"]
                        
            except requests.RequestException as e:
                logger.debug(f"Cloud endpoint {endpoint} failed: {e}")
                continue
        
        # Method 3: Try standard Intelbras RTSP formats with cloud domain
        # Some devices use cloud relay
        possible_urls = [
            f"rtsp://admin:{device_password}@{device_id}.intelbras.cloud:554/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://admin:{device_password}@p2p.intelbras.com.br:554/{device_id}/cam/realmonitor?channel=1&subtype=0",
            f"rtsp://admin:{device_password}@{device_id}.p2p.intelbras.com:554/stream"
        ]
        
        logger.warning(f"⚠ Cloud API unavailable. Try these URLs manually:")
        for url in possible_urls:
            logger.info(f"  • {url}")
        
        # Return first URL for user to test
        return possible_urls[0]
        
    except Exception as e:
        logger.error(f"✗ Failed to connect to Intelbras device: {e}", exc_info=True)
        return None


def discover_onvif_cameras(timeout: int = 5) -> List[Dict]:
    """
    Discover ONVIF cameras on local network
    
    Args:
        timeout: Discovery timeout in seconds
        
    Returns:
        List of discovered cameras with name, ip, serial
    """
    try:
        # Try WSDiscovery for ONVIF
        from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
        from wsdiscovery.scope import Scope
        
        logger.info(f"Scanning network for ONVIF cameras ({timeout}s)...")
        wsd = WSDiscovery()
        wsd.start()
        
        services = wsd.searchServices(timeout=timeout)
        cameras = []
        
        for service in services:
            try:
                # Check if it's an ONVIF device
                scopes = [str(s) for s in service.getScopes()]
                if any('onvif' in s.lower() for s in scopes):
                    # Extract info
                    xaddrs = service.getXAddrs()
                    if xaddrs:
                        url = urlparse(xaddrs[0])
                        ip = url.hostname
                        
                        # Try to extract name and serial from scopes
                        name = "ONVIF Camera"
                        serial = ""
                        for scope in scopes:
                            if 'name/' in scope.lower():
                                name = scope.split('name/')[-1].split('/')[0]
                            elif 'hardware/' in scope.lower():
                                serial = scope.split('hardware/')[-1].split('/')[0]
                        
                        cameras.append({
                            'name': name,
                            'ip': ip,
                            'serial': serial,
                            'scopes': scopes,
                            'xaddrs': xaddrs
                        })
                        logger.info(f"  ✓ Found {name} at {ip}")
                        
            except Exception as e:
                logger.debug(f"Error parsing service: {e}")
                continue
        
        wsd.stop()
        return cameras
        
    except ImportError:
        logger.warning("⚠ WSDiscovery not installed. Install with: pip install wsdiscovery")
        return []
    except Exception as e:
        logger.error(f"✗ ONVIF discovery failed: {e}", exc_info=True)
        return []


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
