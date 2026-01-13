# Passo 3 Concluído: Event Engine - Raciocínio Temporal

## ✅ Implementação Completa

### O que foi feito:

#### 1. **Melhorias no event_engine.py**
- ✅ Adicionado `EventCandidate` dataclass para eventos estruturados
- ✅ Importação de configurações do `config.py` (INTRUSION_DWELL_TIME, LOITERING_THRESHOLD, etc)
- ✅ Métodos retornam `List[EventCandidate]` em vez de `List[Dict]`
- ✅ Thresholds configuráveis em todos os métodos de detecção
- ✅ Metadata estruturado em eventos
- ✅ Cleanup usa `EVENT_TRACK_MAX_AGE` do config

#### 2. **Configurações adicionadas (config/config.py)**
```python
# Event Engine - Temporal Event Detection
INTRUSION_DWELL_TIME = 3  # segundos mínimos em zona proibida
LOITERING_THRESHOLD = 60  # segundos para considerar loitering
LOITERING_MOVEMENT_THRESHOLD = 100  # pixels de movimento mínimo
THEFT_DETECTION_FRAMES = 10  # frames para detectar padrão de roubo
CROWD_THRESHOLD = 10  # número de pessoas para anomalia de multidão
EVENT_WINDOW_SIZE = 10  # segundos de histórico para análise temporal
EVENT_TRACK_MAX_AGE = 30  # segundos para manter tracks inativos
```

#### 3. **Integração com VideoProcessor**
- ✅ `Detection.center` property adicionado (necessário para event engine)
- ✅ `Frame.events` campo adicionado
- ✅ `VideoProcessor.zones` parameter para definir zonas de detecção
- ✅ Pipeline completo:
  ```
  RtspReader → Motion → Detector → Tracker → EventEngine → EventCandidates
  ```
- ✅ `process_frame()` atualiza tracks e detecta eventos temporais:
  - Intrusion detection (pessoa em zona fora do horário)
  - Loitering detection (permanência >60s com pouco movimento)
  - Crowd anomaly detection (pessoas > threshold)

#### 4. **Schema do Banco de Dados**
Nova tabela `events` em `database.py`:
```sql
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id INTEGER NOT NULL,
    zone_id INTEGER,
    event_type TEXT NOT NULL,
    track_id INTEGER NOT NULL,
    confidence REAL NOT NULL,
    severity TEXT NOT NULL,
    metadata TEXT,
    evidence_frames TEXT,
    validated BOOLEAN DEFAULT 0,
    validator_score REAL DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras(id),
    FOREIGN KEY (zone_id) REFERENCES zones(id)
)
```

Métodos adicionados ao `DatabaseManager`:
- `add_event()` - Salva evento temporal
- `get_events()` - Recupera eventos com filtros
- `update_event_validation()` - Atualiza validação do evento
- `get_recent_events_by_type()` - Para cooldown de eventos

#### 5. **Testes Completos (test_event_engine.py)**
- ✅ `test_engine_initialization` - Inicialização do engine
- ✅ `test_update_tracks` - Atualização de tracks
- ✅ `test_intrusion_detection` - Detecção de intrusão (>3s threshold)
- ✅ `test_loitering_detection` - Detecção de loitering (>60s, <100px movimento)
- ✅ `test_loitering_not_detected_with_movement` - Loitering NÃO detectado com movimento
- ✅ `test_crowd_anomaly_detection` - Anomalia de multidão (>10 pessoas)
- ✅ `test_track_cleanup` - Limpeza de tracks antigos
- ✅ `test_event_candidate_to_dict` - Conversão para dict
- ✅ `test_track_state_duration` - Cálculo de duração
- ✅ `test_track_state_dwell_time` - Tempo de permanência em zona
- ✅ `test_track_state_movement_distance` - Distância de movimento

## 🎯 Eventos Temporais Implementados

### 1. **Intrusion (Intrusão)**
- **Gatilho**: Pessoa em zona proibida por >3 segundos fora do horário permitido
- **Severidade**: HIGH
- **Uso**: Detectar invasões em zonas restritas

### 2. **Loitering (Rondando)**
- **Gatilho**: Pessoa em zona por >60 segundos com movimento <100 pixels
- **Severidade**: MEDIUM
- **Uso**: Detectar pessoas suspeitas paradas/rondando

### 3. **Crowd Anomaly (Anomalia de Multidão)**
- **Gatilho**: Mais de 10 pessoas simultaneamente em zona
- **Severidade**: MEDIUM
- **Uso**: Detectar aglomerações anormais

### 4. **Theft Pattern (Padrão de Roubo)**
- **Gatilho**: Objeto em região protegida desaparece + pessoa próxima sai pela saída
- **Severidade**: CRITICAL
- **Uso**: Detectar padrões de furto

## 📊 Fluxo de Dados

```
Frame → Motion Detection → YOLO Detection → ByteTrack Tracking
                                                    ↓
                                            EventEngine.update_tracks()
                                                    ↓
                                            EventEngine.update_zone_presence()
                                                    ↓
                            ┌──────────────────────┴───────────────────────┐
                            ↓                      ↓                       ↓
                    detect_intrusion()    detect_loitering()    detect_crowd_anomaly()
                            ↓                      ↓                       ↓
                            └──────────────────────┬───────────────────────┘
                                                   ↓
                                          List[EventCandidate]
                                                   ↓
                                          Frame.events (para próximo passo)
```

## 🔗 Próximo Passo: Passo 4 - Validator Gating

Com eventos temporais agora detectados, o próximo passo é integrar o **Validator Model** para:

1. **Filtrar falsos positivos**: Eventos devem passar por validação antes de gerar alertas
2. **Adicionar thresholds por evento**: `validator_threshold_intrusion`, `validator_threshold_loitering`, etc
3. **Integrar validator no pipeline**: EventEngine → Validator → EmailQueue
4. **Atualizar AlertManager**: Usar `validator_score` antes de enviar email

## 📝 Arquivos Modificados/Criados

### Modificados:
- `config/config.py` - Adicionadas 7 novas configurações de eventos
- `src/ai/event_engine.py` - EventCandidate dataclass, imports de config, métodos melhorados
- `src/ai/video_processor.py` - Integration com EventEngine, Detection.center, Frame.events
- `src/core/database.py` - Tabela events, 4 novos métodos

### Criados:
- `tests/test_event_engine.py` - 11 testes completos

## ✅ Critérios de Aceitação (Passo 3)

- [x] EventEngine integrado no VideoProcessor
- [x] Eventos temporais (Intrusion, Loitering) com thresholds configuráveis
- [x] Tabela events no database com campos corretos
- [x] Testes unitários passando
- [x] Pipeline: RtspReader → Detector → Tracker → EventEngine → EventCandidates
- [x] Configurações centralizadas em config.py

**Duração real**: ~30 minutos
**Status**: ✅ CONCLUÍDO

---

Pronto para **Passo 4: Validator Gating** 🚀
