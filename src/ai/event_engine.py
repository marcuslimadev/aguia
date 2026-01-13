"""
Event Engine com semântica de propriedade (Intrusion, Loitering, Theft)
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np
from config.config import (
    INTRUSION_DWELL_TIME,
    LOITERING_THRESHOLD,
    LOITERING_MOVEMENT_THRESHOLD,
    THEFT_DETECTION_FRAMES,
    CROWD_THRESHOLD,
    EVENT_WINDOW_SIZE,
    EVENT_TRACK_MAX_AGE
)

logger = logging.getLogger(__name__)


@dataclass
class EventCandidate:
    """Candidato a evento para validação"""
    event_type: str
    zone_id: Optional[int]
    track_id: int
    confidence: float
    severity: str
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)
    evidence_frames: List = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'event_type': self.event_type,
            'zone_id': self.zone_id,
            'track_id': self.track_id,
            'confidence': self.confidence,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class TrackState:
    """Estado de um track de objeto"""
    track_id: int
    class_name: str
    first_seen: datetime
    last_seen: datetime
    positions: List[Tuple[int, int]] = field(default_factory=list)
    zone_entries: Dict[int, datetime] = field(default_factory=dict)
    zone_exits: Dict[int, datetime] = field(default_factory=dict)
    confidence_history: List[float] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Duração do track em segundos"""
        return (self.last_seen - self.first_seen).total_seconds()

    @property
    def dwell_time_by_zone(self) -> Dict[int, float]:
        """Tempo de permanência por zona"""
        dwell_times = {}

        for zone_id, entry_time in self.zone_entries.items():
            exit_time = self.zone_exits.get(zone_id, self.last_seen)
            dwell_times[zone_id] = (exit_time - entry_time).total_seconds()

        return dwell_times

    def add_position(self, x: int, y: int):
        """Adiciona posição ao histórico"""
        self.positions.append((x, y))
        if len(self.positions) > 100:
            self.positions.pop(0)

    def get_movement_distance(self) -> float:
        """Calcula distância total de movimento"""
        if len(self.positions) < 2:
            return 0.0

        total_distance = 0.0
        for i in range(1, len(self.positions)):
            p1 = np.array(self.positions[i - 1])
            p2 = np.array(self.positions[i])
            total_distance += np.linalg.norm(p2 - p1)

        return total_distance


class EventEngine:
    """Engine de eventos com raciocínio temporal"""

    def __init__(self, window_size: int = None):
        """
        Inicializa event engine

        Args:
            window_size: Tamanho da janela de histórico em segundos
        """
        self.window_size = window_size or EVENT_WINDOW_SIZE
        self.tracks: Dict[int, TrackState] = {}
        self.events: List[EventCandidate] = []
        self.last_cleanup = datetime.now()

    def update_tracks(self, detections: List, frame_time: datetime = None):
        """
        Atualiza tracks com novas detecções

        Args:
            detections: Lista de detecções
            frame_time: Timestamp do frame
        """
        if frame_time is None:
            frame_time = datetime.now()

        # Atualizar tracks existentes
        detected_ids = set()

        for detection in detections:
            track_id = detection.track_id
            detected_ids.add(track_id)

            if track_id not in self.tracks:
                self.tracks[track_id] = TrackState(
                    track_id=track_id,
                    class_name=detection.class_name,
                    first_seen=frame_time,
                    last_seen=frame_time
                )

            track = self.tracks[track_id]
            track.last_seen = frame_time
            track.add_position(detection.center[0], detection.center[1])
            track.confidence_history.append(detection.confidence)

        # Remover tracks antigos
        self._cleanup_old_tracks(frame_time)

    def detect_intrusion(
        self,
        zone_id: int,
        zone_schedule: Optional[Dict] = None,
        dwell_threshold: int = None
    ) -> List[EventCandidate]:
        """
        Detecta intrusão (pessoa em zona fora do horário)

        Args:
            zone_id: ID da zona
            zone_schedule: Horários permitidos
            dwell_threshold: Threshold em segundos

        Returns:
            Lista de eventos de intrusão
        """
        events = []
        current_time = datetime.now()
        threshold = dwell_threshold or INTRUSION_DWELL_TIME

        # Verificar se está fora do horário permitido
        if zone_schedule and not self._is_within_schedule(zone_schedule):
            # Procurar pessoas na zona
            for track in self.tracks.values():
                if track.class_name != 'person':
                    continue

                if zone_id in track.zone_entries:
                    entry_time = track.zone_entries[zone_id]
                    duration = (current_time - entry_time).total_seconds()

                    if duration > threshold:
                        event = EventCandidate(
                            event_type='intrusion',
                            zone_id=zone_id,
                            track_id=track.track_id,
                            confidence=np.mean(track.confidence_history) if track.confidence_history else 0.0,
                            severity='high',
                            timestamp=current_time,
                            metadata={
                                'duration': duration,
                                'class_name': track.class_name
                            }
                        )
                        events.append(event)

        return events

    def detect_loitering(
        self,
        zone_id: int,
        loitering_threshold: int = None,
        movement_threshold: int = None
    ) -> List[EventCandidate]:
        """
        Detecta loitering (permanência prolongada)

        Args:
            zone_id: ID da zona
            loitering_threshold: Threshold em segundos
            movement_threshold: Movimento mínimo em pixels

        Returns:
            Lista de eventos de loitering
        """
        events = []
        current_time = datetime.now()
        time_threshold = loitering_threshold or LOITERING_THRESHOLD
        move_threshold = movement_threshold or LOITERING_MOVEMENT_THRESHOLD

        for track in self.tracks.values():
            if track.class_name != 'person':
                continue

            if zone_id not in track.zone_entries:
                continue

            dwell_time = track.dwell_time_by_zone.get(zone_id, 0)

            if dwell_time > time_threshold:
                # Verificar movimento mínimo (não é apenas estático)
                movement = track.get_movement_distance()

                if movement < move_threshold:
                    event = EventCandidate(
                        event_type='loitering',
                        zone_id=zone_id,
                        track_id=track.track_id,
                        confidence=np.mean(track.confidence_history) if track.confidence_history else 0.0,
                        severity='medium',
                        timestamp=current_time,
                        metadata={
                            'dwell_time': dwell_time,
                            'movement': movement,
                            'class_name': track.class_name
                        }
                    )
                    events.append(event)

        return events

    def detect_theft_pattern(
        self,
        protected_region: Tuple[int, int, int, int],
        exit_region: Tuple[int, int, int, int],
        theft_threshold: int = None
    ) -> List[EventCandidate]:
        """
        Detecta padrão de roubo

        Heurística:
        1. Objeto em região protegida
        2. Pessoa próxima
        3. Objeto desaparece
        4. Pessoa sai pela saída

        Args:
            protected_region: (x1, y1, x2, y2) da região protegida
            exit_region: (x1, y1, x2, y2) da saída
            theft_threshold: Threshold em frames

        Returns:
            Lista de eventos de roubo
        """
        events = []
        current_time = datetime.now()
        threshold = theft_threshold or THEFT_DETECTION_FRAMES

        # Procurar objetos que desapareceram da região protegida
        for track in self.tracks.values():
            if track.class_name == 'person':
                continue

            # Verificar se objeto estava na região protegida
            was_in_protected = any(
                self._is_in_region(pos, protected_region)
                for pos in track.positions[-threshold:]
            )

            if not was_in_protected:
                continue

            # Verificar se objeto saiu (não está mais lá)
            is_still_there = any(
                self._is_in_region(pos, protected_region)
                for pos in track.positions[-5:]
            )

            if is_still_there:
                continue

            # Procurar pessoa que saiu pela saída
            for person_track in self.tracks.values():
                if person_track.class_name != 'person':
                    continue

                # Verificar se pessoa estava perto do objeto
                was_nearby = any(
                    self._distance(pos, track.positions[-1]) < 100
                    for pos in person_track.positions[-threshold:]
                )

                if not was_nearby:
                    continue

                # Verificar se pessoa saiu pela saída
                exited = any(
                    self._is_in_region(pos, exit_region)
                    for pos in person_track.positions[-5:]
                )

                if exited:
                    event = EventCandidate(
                        event_type='theft',
                        zone_id=None,
                        track_id=track.track_id,
                        confidence=min(
                            np.mean(track.confidence_history) if track.confidence_history else 0.0,
                            np.mean(person_track.confidence_history) if person_track.confidence_history else 0.0
                        ),
                        severity='critical',
                        timestamp=current_time,
                        metadata={
                            'object_track_id': track.track_id,
                            'person_track_id': person_track.track_id,
                            'object_class': track.class_name
                        }
                    )
                    events.append(event)

        return events

    def detect_crowd_anomaly(
        self,
        zone_id: int,
        person_threshold: int = None
    ) -> List[EventCandidate]:
        """
        Detecta anomalia em multidão

        Args:
            zone_id: ID da zona
            person_threshold: Threshold de pessoas

        Returns:
            Lista de eventos
        """
        events = []
        current_time = datetime.now()
        threshold = person_threshold or CROWD_THRESHOLD

        # Contar pessoas na zona
        person_count = sum(
            1 for track in self.tracks.values()
            if track.class_name == 'person' and zone_id in track.zone_entries
        )

        if person_count > threshold:
            event = EventCandidate(
                event_type='crowd_anomaly',
                zone_id=zone_id,
                track_id=0,  # Evento de grupo, não de track específico
                confidence=0.8,
                severity='medium',
                timestamp=current_time,
                metadata={
                    'person_count': person_count,
                    'threshold': threshold
                }
            )
            events.append(event)

        return events

    def update_zone_presence(self, zone_id: int, zone_region: Tuple[int, int, int, int]):
        """Atualiza presença de tracks em zona"""
        current_time = datetime.now()

        for track in self.tracks.values():
            if not track.positions:
                continue

            current_pos = track.positions[-1]
            is_in_zone = self._is_in_region(current_pos, zone_region)

            if is_in_zone and zone_id not in track.zone_entries:
                track.zone_entries[zone_id] = current_time

            elif not is_in_zone and zone_id in track.zone_entries:
                if zone_id not in track.zone_exits:
                    track.zone_exits[zone_id] = current_time

    def _cleanup_old_tracks(self, current_time: datetime):
        """Remove tracks antigos"""
        max_age = timedelta(seconds=EVENT_TRACK_MAX_AGE)

        old_tracks = [
            track_id for track_id, track in self.tracks.items()
            if current_time - track.last_seen > max_age
        ]

        for track_id in old_tracks:
            del self.tracks[track_id]

    @staticmethod
    def _is_within_schedule(schedule: Dict) -> bool:
        """Verifica se está dentro do horário permitido"""
        # Implementar verificação de horário
        return True

    @staticmethod
    def _is_in_region(pos: Tuple[int, int], region: Tuple[int, int, int, int]) -> bool:
        """Verifica se posição está em região"""
        x, y = pos
        x1, y1, x2, y2 = region
        return x1 <= x <= x2 and y1 <= y <= y2

    @staticmethod
    def _distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Calcula distância entre dois pontos"""
        return np.linalg.norm(np.array(p1) - np.array(p2))
