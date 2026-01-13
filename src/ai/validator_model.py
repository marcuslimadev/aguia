"""
Validador de falsos positivos com modelo de IA
"""
import logging
from typing import Optional, Tuple, Dict
import numpy as np
import cv2
from pathlib import Path
from config.config import MODELS_DIR

logger = logging.getLogger(__name__)


class ValidatorModel:
    """Modelo validador para confirmar eventos"""

    def __init__(self, model_path: Optional[Path] = None, custom_thresholds: Optional[Dict[str, float]] = None):
        """
        Inicializa validador

        Args:
            model_path: Caminho para modelo ONNX (opcional)
            custom_thresholds: Thresholds customizados (opcional)
        """
        from config.config import (
            VALIDATOR_THRESHOLD_INTRUSION,
            VALIDATOR_THRESHOLD_LOITERING,
            VALIDATOR_THRESHOLD_THEFT,
            VALIDATOR_THRESHOLD_CROWD,
            VALIDATOR_THRESHOLD_FIRE_SMOKE,
            VALIDATOR_THRESHOLD_VANDALISM,
            VALIDATOR_MODEL_PATH
        )
        
        # Usar model_path fornecido ou padrão do config
        if model_path is None:
            model_path = MODELS_DIR / VALIDATOR_MODEL_PATH
        
        self.model_path = model_path
        self.session = None
        
        # Thresholds padrão do config.py
        self.thresholds = {
            'intrusion': VALIDATOR_THRESHOLD_INTRUSION,
            'loitering': VALIDATOR_THRESHOLD_LOITERING,
            'theft': VALIDATOR_THRESHOLD_THEFT,
            'crowd_anomaly': VALIDATOR_THRESHOLD_CROWD,
            'fire_smoke': VALIDATOR_THRESHOLD_FIRE_SMOKE,
            'vandalism': VALIDATOR_THRESHOLD_VANDALISM
        }
        
        # Sobrescrever com custom_thresholds se fornecido
        if custom_thresholds:
            self.thresholds.update(custom_thresholds)

        if self.model_path.exists():
            self._load_model()
        else:
            logger.warning(f"Modelo validador não encontrado: {self.model_path}, usando heurística")

    def _load_model(self):
        """Carrega modelo ONNX"""
        try:
            import onnxruntime as ort

            if not self.model_path.exists():
                logger.warning(f"Modelo não encontrado: {self.model_path}")
                return

            self.session = ort.InferenceSession(
                str(self.model_path),
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )

            logger.info(f"✓ Modelo validador carregado: {self.model_path}")

        except ImportError:
            logger.warning("onnxruntime não instalado")

        except Exception as e:
            logger.error(f"Erro ao carregar modelo validador: {e}")

    def validate_event(
        self,
        event_type: str,
        snapshot: np.ndarray,
        metadata: dict
    ) -> Tuple[bool, float]:
        """
        Valida um evento

        Args:
            event_type: Tipo de evento
            snapshot: Imagem do evento
            metadata: Metadados do evento

        Returns:
            (is_valid, confidence)
        """
        if self.session is None:
            # Usar heurística simples sem modelo
            return self._validate_heuristic(event_type, metadata)

        try:
            # Preprocessar snapshot
            input_data = self._preprocess_snapshot(snapshot)

            # Inferência
            outputs = self.session.run(None, {self.session.get_inputs()[0].name: input_data})

            # Pós-processar
            confidence = float(outputs[0][0])

            # Comparar com threshold
            threshold = self.thresholds.get(event_type, 0.7)
            is_valid = confidence >= threshold

            logger.debug(f"Validação {event_type}: {confidence:.2f} (threshold: {threshold})")

            return is_valid, confidence

        except Exception as e:
            logger.error(f"Erro ao validar evento: {e}")
            return self._validate_heuristic(event_type, metadata)

    def validate_event_candidate(
        self,
        event_candidate,
        snapshot: Optional[np.ndarray] = None
    ) -> Tuple[bool, float]:
        """
        Valida um EventCandidate

        Args:
            event_candidate: EventCandidate a validar
            snapshot: Imagem do evento (opcional, usa evidence_frames se None)

        Returns:
            (is_valid, validator_score)
        """
        # Extrair snapshot dos evidence_frames se não fornecido
        if snapshot is None and event_candidate.evidence_frames:
            snapshot = event_candidate.evidence_frames[0] if event_candidate.evidence_frames else None
        
        if snapshot is None:
            # Sem snapshot, usar apenas heurística
            return self._validate_heuristic(event_candidate.event_type, event_candidate.metadata)
        
        # Validar com snapshot
        return self.validate_event(
            event_type=event_candidate.event_type,
            snapshot=snapshot,
            metadata=event_candidate.metadata
        )

    def _validate_heuristic(self, event_type: str, metadata: dict) -> Tuple[bool, float]:
        """Validação heurística sem modelo"""
        base_confidence = metadata.get('confidence', 0.5)

        # Aplicar ajustes por tipo de evento
        adjustments = {
            'intrusion': 1.0,
            'loitering': 0.95,
            'theft': 0.85,
            'crowd_anomaly': 0.9,
            'fire_smoke': 0.8,
            'vandalism': 0.75
        }

        adjusted_confidence = base_confidence * adjustments.get(event_type, 1.0)

        threshold = self.thresholds.get(event_type, 0.7)
        is_valid = adjusted_confidence >= threshold

        return is_valid, adjusted_confidence

    def _preprocess_snapshot(self, snapshot: np.ndarray) -> np.ndarray:
        """Preprocessa snapshot para modelo"""
        # Redimensionar
        h, w = snapshot.shape[:2]
        size = 224

        resized = cv2.resize(snapshot, (size, size))

        # Normalizar
        normalized = resized.astype(np.float32) / 255.0
        normalized = np.transpose(normalized, (2, 0, 1))
        normalized = np.expand_dims(normalized, 0)

        return normalized

    def set_threshold(self, event_type: str, threshold: float):
        """Define threshold para tipo de evento"""
        self.thresholds[event_type] = threshold
        logger.info(f"Threshold {event_type} atualizado para {threshold}")

    def get_threshold(self, event_type: str) -> float:
        """Obtém threshold para tipo de evento"""
        return self.thresholds.get(event_type, 0.7)


class UserFeedbackCollector:
    """Coleta feedback do usuário para calibração"""

    def __init__(self, db_manager):
        self.db = db_manager

    def record_feedback(
        self,
        event_id: int,
        is_real: bool,
        event_type: str,
        user_notes: Optional[str] = None
    ) -> bool:
        """
        Registra feedback do usuário

        Args:
            event_id: ID do evento
            is_real: True se evento foi real, False se falso positivo
            event_type: Tipo de evento
            user_notes: Notas do usuário

        Returns:
            True se registrado com sucesso
        """
        try:
            query = """
                INSERT INTO user_feedback 
                (event_id, is_real, event_type, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
            """

            from datetime import datetime

            self.db.execute_update(
                query,
                (event_id, is_real, event_type, user_notes, datetime.now().isoformat())
            )

            logger.info(f"Feedback registrado para evento {event_id}: {'Real' if is_real else 'Falso Positivo'}")
            return True

        except Exception as e:
            logger.error(f"Erro ao registrar feedback: {e}")
            return False

    def get_false_positive_rate(self, event_type: str) -> float:
        """Calcula taxa de falsos positivos"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_real = 0 THEN 1 ELSE 0 END) as false_positives
                FROM user_feedback
                WHERE event_type = ?
            """

            result = self.db.execute_query(query, (event_type,))

            if result and result[0][0] > 0:
                total = result[0][0]
                false_positives = result[0][1] or 0
                return false_positives / total

            return 0.0

        except Exception as e:
            logger.error(f"Erro ao calcular taxa de falsos positivos: {e}")
            return 0.0

    def get_calibration_data(self, event_type: str) -> dict:
        """Obtém dados para calibração"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_real = 1 THEN 1 ELSE 0 END) as true_positives,
                    SUM(CASE WHEN is_real = 0 THEN 1 ELSE 0 END) as false_positives,
                    AVG(CASE WHEN is_real = 1 THEN confidence ELSE NULL END) as avg_tp_confidence,
                    AVG(CASE WHEN is_real = 0 THEN confidence ELSE NULL END) as avg_fp_confidence
                FROM user_feedback
                WHERE event_type = ?
            """

            result = self.db.execute_query(query, (event_type,))

            if result:
                row = result[0]
                return {
                    'total_samples': row[0] or 0,
                    'true_positives': row[1] or 0,
                    'false_positives': row[2] or 0,
                    'avg_tp_confidence': row[3] or 0.0,
                    'avg_fp_confidence': row[4] or 0.0,
                    'false_positive_rate': self.get_false_positive_rate(event_type)
                }

            return {}

        except Exception as e:
            logger.error(f"Erro ao obter dados de calibração: {e}")
            return {}

    def suggest_threshold_adjustment(self, event_type: str) -> Optional[float]:
        """Sugere ajuste de threshold baseado em feedback"""
        calibration = self.get_calibration_data(event_type)

        if calibration.get('total_samples', 0) < 10:
            return None  # Dados insuficientes

        avg_tp_conf = calibration.get('avg_tp_confidence', 0.5)
        avg_fp_conf = calibration.get('avg_fp_confidence', 0.5)

        # Sugerir threshold entre as médias
        suggested = (avg_tp_conf + avg_fp_conf) / 2

        logger.info(
            f"Threshold sugerido para {event_type}: {suggested:.2f} "
            f"(TP: {avg_tp_conf:.2f}, FP: {avg_fp_conf:.2f})"
        )

        return suggested
