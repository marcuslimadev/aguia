"""
Configurações centralizadas do Edge Property Security AI
"""
import os
from pathlib import Path
from typing import Dict

# Diretórios
if os.name == 'nt':  # Windows
    APP_DATA_DIR = Path("C:/ProgramData/EdgeAI")
else:  # Linux/Mac para desenvolvimento
    APP_DATA_DIR = Path.home() / ".EdgeAI"

APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = APP_DATA_DIR / "database.db"
SNAPSHOTS_DIR = APP_DATA_DIR / "snapshots"
LOGS_DIR = APP_DATA_DIR / "logs"
MODELS_DIR = APP_DATA_DIR / "models"

# Criar diretórios
for directory in [SNAPSHOTS_DIR, LOGS_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configurações de Aplicação
APP_NAME = "Edge Property Security AI"
APP_VERSION = "1.0.0"
COMPANY_NAME = "Edge Security"

# Licenciamento
TRIAL_DURATION_DAYS = 7
TRIAL_CAMERA_LIMIT = 2

# Store Licensing
FREE_CAMERA_LIMIT = 2  # Limite para versão trial/free
PREMIUM_CAMERA_LIMIT_TIER1 = 5  # Tier 1: 5 câmeras
PREMIUM_CAMERA_LIMIT_TIER2 = 10  # Tier 2: 10 câmeras
PREMIUM_CAMERA_LIMIT_TIER3 = 50  # Tier 3: 50 câmeras (empresas)
IS_STORE_BUILD = False  # True quando empacotado como MSIX para Store

# IA e Processamento
YOLO_MODEL = "yolov8m.pt"  # Medium model
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45
FRAME_SKIP = 2  # Processar a cada 2 frames

# Vídeo
RTSP_TIMEOUT = 10  # segundos
TARGET_FPS = 15
MAX_FRAME_WIDTH = 1920
MAX_FRAME_HEIGHT = 1080

# Alertas
ALERT_COOLDOWN = 30  # segundos entre alertas do mesmo tipo
MAX_SNAPSHOTS_PER_ALERT = 3
SNAPSHOT_QUALITY = 85

# Event Engine - Temporal Event Detection
INTRUSION_DWELL_TIME = 3  # segundos mínimos em zona proibida
LOITERING_THRESHOLD = 60  # segundos para considerar loitering
LOITERING_MOVEMENT_THRESHOLD = 100  # pixels de movimento mínimo
THEFT_DETECTION_FRAMES = 10  # frames para detectar padrão de roubo
CROWD_THRESHOLD = 10  # número de pessoas para anomalia de multidão
EVENT_WINDOW_SIZE = 10  # segundos de histórico para análise temporal
EVENT_TRACK_MAX_AGE = 30  # segundos para manter tracks inativos

# Pose Estimation Settings (MediaPipe)
POSE_MODEL_COMPLEXITY = 1  # 0=lite, 1=full, 2=heavy (default: 1)
POSE_MIN_DETECTION_CONFIDENCE = 0.5  # threshold de confiança
POSE_MIN_TRACKING_CONFIDENCE = 0.5  # threshold de tracking

# Shoplifting Detection Settings (Shopformer)
SHOPLIFTING_ENABLED = True  # habilitar detecção de shoplifting
SHOPLIFTING_SEQUENCE_LENGTH = 24  # frames por sequência (Shopformer usa 24)
SHOPLIFTING_SEQUENCE_STRIDE = 12  # step entre sequências
SHOPLIFTING_ANOMALY_THRESHOLD = 0.7  # threshold para considerar shoplifting
SHOPLIFTING_MODEL_PATH = None  # caminho para modelo ONNX (None = heurísticas)
SHOPLIFTING_USE_ONNX = False  # usar ONNX ou heurísticas (default: heurísticas)

# Validator Model - Thresholds por tipo de evento
VALIDATOR_THRESHOLD_INTRUSION = 0.7  # Threshold para validar intrusão
VALIDATOR_THRESHOLD_LOITERING = 0.6  # Threshold para validar loitering
VALIDATOR_THRESHOLD_THEFT = 0.8  # Threshold para validar roubo
VALIDATOR_THRESHOLD_CROWD = 0.65  # Threshold para anomalia de multidão
VALIDATOR_THRESHOLD_SHOPLIFTING = 0.75  # Threshold para validar shoplifting
VALIDATOR_THRESHOLD_FIRE_SMOKE = 0.85  # Threshold para fogo/fumaça
VALIDATOR_THRESHOLD_VANDALISM = 0.75  # Threshold para vandalismo
VALIDATOR_MODEL_PATH = "validator_v1.onnx"  # Nome do modelo validador

# Email
SMTP_TIMEOUT = 10
EMAIL_RETRY_COUNT = 3

# Email Queue
MAX_QUEUE_SIZE = 1000  # Máximo de mensagens na fila
EMAIL_RETRY_DELAY = 60  # Delay inicial em segundos para retry
EMAIL_MAX_RETRIES = 5  # Máximo de tentativas de envio
EMAIL_WORKER_INTERVAL = 30  # Intervalo do worker em segundos
EMAIL_CLEANUP_DAYS = 30  # Dias para manter mensagens antigas
EMAIL_VERIFICATION_TTL_MINUTES = 15

# Detecção de eventos
DETECTION_CLASSES = {
    "person": 0,
    "car": 2,
    "truck": 7,
    "backpack": 24,
    "handbag": 26,
    "suitcase": 28,
}

# Tipos de eventos
EVENT_TYPES = {
    "intrusion": "Intrusion detected",
    "theft": "Theft pattern detected",
    "loitering": "Loitering detected",
    "restricted_access": "Restricted area access",
    "crowd_anomaly": "Crowd anomaly detected",
    "fire_smoke": "Fire or smoke detected",
    "vandalism": "Vandalism detected",
}

# Configurações de UI
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
THEME_PRIMARY = "#2196F3"
THEME_SECONDARY = "#1976D2"
THEME_SUCCESS = "#4CAF50"
THEME_WARNING = "#FF9800"
THEME_ERROR = "#F44336"

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10485760  # 10MB
LOG_BACKUP_COUNT = 5

# Segurança
ENABLE_DRM = True
SIGNATURE_VERIFICATION = True
INTEGRITY_CHECK = True

# Desenvolvimento
DEBUG_MODE = False
ENABLE_MOCK_CAMERAS = False
