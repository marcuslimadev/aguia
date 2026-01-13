"""
Regras de detecção e análise de eventos
"""
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class DetectionRule:
    """Define uma regra de detecção"""
    rule_id: int
    zone_id: int
    event_type: str
    enabled: bool
    min_confidence: float
    min_duration: int  # segundos
    max_objects: int


class DetectionAnalyzer:
    """Analisa detecções e gera eventos baseado em regras"""

    def __init__(self):
        self.rules: Dict[int, DetectionRule] = {}
        self.object_history: Dict[int, List] = {}  # track_id -> histórico
        self.event_timestamps: Dict[str, datetime] = {}  # event_type -> último timestamp

    def add_rule(self, rule: DetectionRule):
        """Adiciona uma regra de detecção"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Regra adicionada: {rule.event_type}")

    def analyze_frame(self, detections, zone_id: int) -> List[Dict]:
        """Analisa um frame e retorna eventos detectados"""
        events = []

        for rule in self.rules.values():
            if not rule.enabled or rule.zone_id != zone_id:
                continue

            # Verificar detecções relevantes
            matching_detections = [
                d for d in detections
                if d.confidence >= rule.min_confidence
            ]

            if len(matching_detections) > 0:
                event = self._create_event(rule, matching_detections)
                if event:
                    events.append(event)

        return events

    def _create_event(self, rule: DetectionRule, detections) -> Dict:
        """Cria um evento baseado em detecções"""
        try:
            event_key = f"{rule.rule_id}_{rule.event_type}"

            # Verificar cooldown
            if event_key in self.event_timestamps:
                elapsed = (datetime.now() - self.event_timestamps[event_key]).total_seconds()
                if elapsed < rule.min_duration:
                    return None

            self.event_timestamps[event_key] = datetime.now()

            return {
                'rule_id': rule.rule_id,
                'event_type': rule.event_type,
                'severity': self._calculate_severity(rule, detections),
                'confidence': max(d.confidence for d in detections),
                'object_count': len(detections),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Erro ao criar evento: {e}")
            return None

    def _calculate_severity(self, rule: DetectionRule, detections) -> str:
        """Calcula a severidade do evento"""
        avg_confidence = sum(d.confidence for d in detections) / len(detections)

        if rule.event_type in ['fire_smoke', 'vandalism']:
            return 'critical'
        elif rule.event_type in ['intrusion', 'restricted_access']:
            return 'high'
        elif rule.event_type in ['theft', 'loitering']:
            return 'medium'
        else:
            return 'low'

    def track_object_behavior(self, track_id: int, class_name: str, duration: int) -> str:
        """Rastreia comportamento de objetos"""
        if track_id not in self.object_history:
            self.object_history[track_id] = []

        self.object_history[track_id].append({
            'class': class_name,
            'timestamp': datetime.now(),
            'duration': duration
        })

        # Detectar loitering (permanência prolongada)
        if duration > 60:  # Mais de 1 minuto
            return 'loitering'

        return None

    def detect_crowd_anomaly(self, detections) -> bool:
        """Detecta anomalias em multidão"""
        person_count = sum(1 for d in detections if d.class_name == 'person')

        # Anomalia se mais de 10 pessoas em área pequena
        if person_count > 10:
            return True

        return False

    def detect_fire_smoke(self, detections) -> bool:
        """Detecta fogo ou fumaça"""
        # Aqui você implementaria detecção específica de fogo/fumaça
        # Por enquanto, apenas verificar classes
        return False

    def detect_vandalism(self, frame_diff) -> bool:
        """Detecta vandalismo baseado em mudanças de frame"""
        # Aqui você implementaria análise de mudanças rápidas
        # Por enquanto, apenas retornar False
        return False


class EventValidator:
    """Valida eventos antes de gerar alertas"""

    def __init__(self):
        self.event_buffer: List[Dict] = []
        self.buffer_timeout = 5  # segundos

    def validate_event(self, event: Dict) -> bool:
        """Valida um evento"""
        try:
            # Verificar campos obrigatórios
            required_fields = ['rule_id', 'event_type', 'severity', 'confidence']
            for field in required_fields:
                if field not in event:
                    logger.warning(f"Campo obrigatório ausente: {field}")
                    return False

            # Verificar valores
            if not (0 <= event['confidence'] <= 1):
                logger.warning(f"Confiança inválida: {event['confidence']}")
                return False

            if event['severity'] not in ['low', 'medium', 'high', 'critical']:
                logger.warning(f"Severidade inválida: {event['severity']}")
                return False

            return True

        except Exception as e:
            logger.error(f"Erro ao validar evento: {e}")
            return False

    def buffer_event(self, event: Dict):
        """Adiciona evento ao buffer"""
        event['buffered_at'] = datetime.now()
        self.event_buffer.append(event)

    def flush_old_events(self):
        """Remove eventos antigos do buffer"""
        cutoff_time = datetime.now() - timedelta(seconds=self.buffer_timeout)
        self.event_buffer = [
            e for e in self.event_buffer
            if datetime.fromisoformat(e['buffered_at']) > cutoff_time
        ]

    def get_buffered_events(self) -> List[Dict]:
        """Retorna eventos do buffer"""
        self.flush_old_events()
        return self.event_buffer.copy()
