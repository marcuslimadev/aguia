"""
Testes para Event Engine
"""
import pytest
from datetime import datetime, timedelta
from src.ai.event_engine import EventEngine, EventCandidate, TrackState
from src.ai.video_processor import Detection


@pytest.fixture
def event_engine():
    """Fixture que cria um event engine"""
    return EventEngine(window_size=10)


@pytest.fixture
def sample_detections():
    """Fixture com detecções de exemplo"""
    return [
        Detection(
            class_id=0,
            class_name="person",
            confidence=0.9,
            bbox=(100, 100, 200, 200),
            track_id=1
        ),
        Detection(
            class_id=0,
            class_name="person",
            confidence=0.85,
            bbox=(300, 300, 400, 400),
            track_id=2
        )
    ]


class TestEventEngine:
    """Testes para Event Engine"""

    def test_engine_initialization(self, event_engine):
        """Testa inicialização do engine"""
        assert event_engine.window_size == 10
        assert len(event_engine.tracks) == 0
        assert len(event_engine.events) == 0

    def test_update_tracks(self, event_engine, sample_detections):
        """Testa atualização de tracks"""
        event_engine.update_tracks(sample_detections)
        
        assert len(event_engine.tracks) == 2
        assert 1 in event_engine.tracks
        assert 2 in event_engine.tracks
        
        track1 = event_engine.tracks[1]
        assert track1.class_name == "person"
        assert track1.track_id == 1
        assert len(track1.positions) == 1

    def test_intrusion_detection(self, event_engine, sample_detections):
        """Testa detecção de intrusão"""
        # Atualizar tracks
        event_engine.update_tracks(sample_detections)
        
        # Simular entrada em zona
        zone_id = 1
        zone_region = (0, 0, 500, 500)
        event_engine.update_zone_presence(zone_id, zone_region)
        
        # Simular passagem de tempo (>3s threshold)
        for track in event_engine.tracks.values():
            track.zone_entries[zone_id] = datetime.now() - timedelta(seconds=5)
        
        # Detectar intrusão (fora do horário - schedule None)
        events = event_engine.detect_intrusion(zone_id=zone_id, zone_schedule={})
        
        # Deve detectar intrusão para ambos os tracks
        assert len(events) >= 1
        assert all(isinstance(e, EventCandidate) for e in events)
        assert all(e.event_type == "intrusion" for e in events)
        assert all(e.severity == "high" for e in events)

    def test_loitering_detection(self, event_engine, sample_detections):
        """Testa detecção de loitering"""
        # Atualizar tracks
        event_engine.update_tracks(sample_detections)
        
        # Simular entrada em zona
        zone_id = 1
        zone_region = (0, 0, 500, 500)
        event_engine.update_zone_presence(zone_id, zone_region)
        
        # Simular permanência prolongada (>60s threshold)
        for track in event_engine.tracks.values():
            track.zone_entries[zone_id] = datetime.now() - timedelta(seconds=70)
            # Adicionar posições com movimento mínimo (<100 pixels)
            track.positions = [(150, 150), (155, 155), (160, 160)]
        
        # Detectar loitering
        events = event_engine.detect_loitering(zone_id=zone_id)
        
        # Deve detectar loitering
        assert len(events) >= 1
        assert all(isinstance(e, EventCandidate) for e in events)
        assert all(e.event_type == "loitering" for e in events)
        assert all(e.severity == "medium" for e in events)

    def test_loitering_not_detected_with_movement(self, event_engine, sample_detections):
        """Testa que loitering NÃO é detectado com muito movimento"""
        event_engine.update_tracks(sample_detections)
        
        zone_id = 1
        zone_region = (0, 0, 500, 500)
        event_engine.update_zone_presence(zone_id, zone_region)
        
        # Simular permanência prolongada MAS com muito movimento
        for track in event_engine.tracks.values():
            track.zone_entries[zone_id] = datetime.now() - timedelta(seconds=70)
            # Adicionar posições com movimento grande (>100 pixels)
            track.positions = [(100, 100), (200, 200), (300, 300), (400, 400)]
        
        # Detectar loitering
        events = event_engine.detect_loitering(zone_id=zone_id)
        
        # NÃO deve detectar loitering (pessoa está se movendo)
        assert len(events) == 0

    def test_crowd_anomaly_detection(self, event_engine):
        """Testa detecção de anomalia de multidão"""
        # Criar muitas detecções de pessoas
        many_people = [
            Detection(
                class_id=0,
                class_name="person",
                confidence=0.8,
                bbox=(i*50, i*50, i*50+50, i*50+50),
                track_id=i
            )
            for i in range(15)  # 15 pessoas (threshold padrão é 10)
        ]
        
        event_engine.update_tracks(many_people)
        
        # Simular todas em mesma zona
        zone_id = 1
        zone_region = (0, 0, 1000, 1000)
        event_engine.update_zone_presence(zone_id, zone_region)
        
        # Marcar todas como presentes na zona
        for track in event_engine.tracks.values():
            track.zone_entries[zone_id] = datetime.now()
        
        # Detectar anomalia
        events = event_engine.detect_crowd_anomaly(zone_id=zone_id)
        
        # Deve detectar anomalia
        assert len(events) == 1
        event = events[0]
        assert event.event_type == "crowd_anomaly"
        assert event.metadata['person_count'] == 15
        assert event.severity == "medium"

    def test_track_cleanup(self, event_engine, sample_detections):
        """Testa limpeza de tracks antigos"""
        # Adicionar tracks
        event_engine.update_tracks(sample_detections)
        assert len(event_engine.tracks) == 2
        
        # Simular passagem de tempo (>30s EVENT_TRACK_MAX_AGE)
        old_time = datetime.now() - timedelta(seconds=35)
        for track in event_engine.tracks.values():
            track.last_seen = old_time
        
        # Chamar cleanup
        event_engine._cleanup_old_tracks(datetime.now())
        
        # Tracks devem ter sido removidos
        assert len(event_engine.tracks) == 0

    def test_event_candidate_to_dict(self):
        """Testa conversão de EventCandidate para dict"""
        timestamp = datetime.now()
        event = EventCandidate(
            event_type="intrusion",
            zone_id=1,
            track_id=10,
            confidence=0.95,
            severity="high",
            timestamp=timestamp,
            metadata={"duration": 5.5}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_type'] == "intrusion"
        assert event_dict['zone_id'] == 1
        assert event_dict['track_id'] == 10
        assert event_dict['confidence'] == 0.95
        assert event_dict['severity'] == "high"
        assert event_dict['metadata']['duration'] == 5.5
        assert 'timestamp' in event_dict

    def test_track_state_duration(self):
        """Testa cálculo de duração do track"""
        now = datetime.now()
        track = TrackState(
            track_id=1,
            class_name="person",
            first_seen=now - timedelta(seconds=10),
            last_seen=now
        )
        
        assert 9.9 < track.duration < 10.1  # ~10 segundos

    def test_track_state_dwell_time(self):
        """Testa cálculo de dwell time por zona"""
        now = datetime.now()
        track = TrackState(
            track_id=1,
            class_name="person",
            first_seen=now - timedelta(seconds=100),
            last_seen=now
        )
        
        # Simular entrada e saída de zona
        track.zone_entries[1] = now - timedelta(seconds=50)
        track.zone_exits[1] = now - timedelta(seconds=20)
        
        dwell_times = track.dwell_time_by_zone
        assert 1 in dwell_times
        assert 29 < dwell_times[1] < 31  # ~30 segundos na zona

    def test_track_state_movement_distance(self):
        """Testa cálculo de distância de movimento"""
        track = TrackState(
            track_id=1,
            class_name="person",
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
        
        # Adicionar posições em linha reta
        track.add_position(0, 0)
        track.add_position(100, 0)
        track.add_position(200, 0)
        
        distance = track.get_movement_distance()
        assert 199 < distance < 201  # 200 pixels total
