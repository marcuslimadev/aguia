# Passo 4 Concluído: Validator Gating - Filtragem de Falsos Positivos

## ✅ Implementação Completa

### O que foi feito:

#### 1. **Melhorias no validator_model.py**
- ✅ Importação de configurações do `config.py` (VALIDATOR_THRESHOLD_*)
- ✅ Thresholds configuráveis por tipo de evento
- ✅ Suporte a custom_thresholds no __init__
- ✅ Método `validate_event_candidate()` para validar EventCandidates
- ✅ Heurística robusta quando modelo ONNX não está disponível
- ✅ Preprocessamento de imagens (224×224, normalização)

#### 2. **Configurações adicionadas (config/config.py)**
```python
# Validator Model - Thresholds por tipo de evento
VALIDATOR_THRESHOLD_INTRUSION = 0.7  # Threshold para validar intrusão
VALIDATOR_THRESHOLD_LOITERING = 0.6  # Threshold para validar loitering
VALIDATOR_THRESHOLD_THEFT = 0.8  # Threshold para validar roubo
VALIDATOR_THRESHOLD_CROWD = 0.65  # Threshold para anomalia de multidão
VALIDATOR_THRESHOLD_FIRE_SMOKE = 0.85  # Threshold para fogo/fumaça
VALIDATOR_THRESHOLD_VANDALISM = 0.75  # Threshold para vandalismo
VALIDATOR_MODEL_PATH = "validator_v1.onnx"  # Nome do modelo validador
```

#### 3. **Integração com AlertManager**
- ✅ `AlertManager.__init__` aceita `validator_model` como parâmetro
- ✅ Novo método `process_event_candidate()`:
  1. Valida evento com ValidatorModel
  2. Salva evento no database com `validator_score`
  3. Cria alerta **apenas se validado**
  4. Envia email **apenas para eventos aprovados**
- ✅ Método `_create_event_description()` para gerar descrições legíveis
- ✅ Logging detalhado de aprovações/rejeições

#### 4. **Schema do Banco de Dados**
Nova tabela `user_feedback` em `database.py`:
```sql
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    is_real BOOLEAN NOT NULL,
    event_type TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id)
)
```

Métodos adicionados ao `DatabaseManager`:
- `add_user_feedback()` - Registra feedback do usuário
- `get_feedback_stats()` - Estatísticas de falsos positivos

#### 5. **Testes Completos (test_validator_model.py)**
- ✅ `test_initialization_default` - Thresholds padrão
- ✅ `test_initialization_custom_thresholds` - Thresholds customizados
- ✅ `test_validate_heuristic_intrusion` - Validação heurística
- ✅ `test_validate_heuristic_loitering` - Loitering com ajuste 0.95
- ✅ `test_validate_heuristic_below_threshold` - Rejeição abaixo do threshold
- ✅ `test_validate_event_candidate_intrusion` - EventCandidate intrusion
- ✅ `test_validate_event_candidate_loitering` - EventCandidate loitering
- ✅ `test_validate_event_with_snapshot` - Validação com imagem
- ✅ `test_preprocess_snapshot` - Preprocessamento 224×224
- ✅ `test_set_threshold` - Alteração de threshold
- ✅ `test_get_threshold_unknown_event` - Threshold padrão para eventos desconhecidos
- ✅ `test_custom_threshold_enforcement` - Enforcement de thresholds customizados
- ✅ `test_validate_event_candidate_rejected` - Evento rejeitado
- ✅ `test_validate_multiple_event_types` - Múltiplos tipos
- ✅ `test_validate_without_confidence_in_metadata` - Sem confidence
- ✅ `test_event_candidate_without_snapshot` - Sem snapshot (usa heurística)

## 🎯 Fluxo de Validação Implementado

### Pipeline Completo:
```
EventEngine → EventCandidate → ValidatorModel.validate_event_candidate()
                                        ↓
                            is_valid=True/False, validator_score
                                        ↓
                    ┌───────────────────┴────────────────────┐
                    ↓                                        ↓
            is_valid=True                              is_valid=False
                    ↓                                        ↓
        AlertManager.create_alert()               LOG: Evento rejeitado
                    ↓                                        ↓
            EmailQueue → SMTP                      Salvar no DB com score
```

### Heurística de Validação (sem modelo ONNX):
```python
# Ajustes por tipo de evento
adjustments = {
    'intrusion': 1.0,      # Sem ajuste
    'loitering': 0.95,     # Redução de 5%
    'theft': 0.85,         # Redução de 15%
    'crowd_anomaly': 0.9,  # Redução de 10%
    'fire_smoke': 0.8,     # Redução de 20%
    'vandalism': 0.75      # Redução de 25%
}

adjusted_score = event.confidence * adjustments[event_type]
is_valid = adjusted_score >= threshold
```

## 📊 Exemplo de Uso

### Validar Evento no AlertManager:
```python
# Criar validator
validator = ValidatorModel()

# Criar alert manager com validator
alert_manager = AlertManager(db_manager, validator_model=validator)

# Processar evento do EventEngine
event_candidate = EventCandidate(
    event_type='intrusion',
    zone_id=1,
    track_id=10,
    confidence=0.85,
    severity='high',
    timestamp=datetime.now(),
    metadata={'duration': 5.5}
)

# Validar e criar alerta se aprovado
alert_created = alert_manager.process_event_candidate(
    event_candidate,
    camera_id=1,
    snapshot=Path("snapshot.jpg")
)

# alert_created=True se aprovado pelo validator
# alert_created=False se rejeitado (falso positivo)
```

### Customizar Thresholds:
```python
# Thresholds mais rigorosos
custom_thresholds = {
    'intrusion': 0.9,    # Aumentar para reduzir falsos positivos
    'loitering': 0.85,
    'theft': 0.95
}

validator = ValidatorModel(custom_thresholds=custom_thresholds)
```

## 🔧 Configuração de Feedback do Usuário

O sistema inclui `UserFeedbackCollector` para calibração contínua:

```python
from src.ai.validator_model import UserFeedbackCollector

collector = UserFeedbackCollector(db_manager)

# Usuário confirma evento
collector.record_feedback(event_id=123, is_real=True, event_type='intrusion')

# Usuário marca como falso positivo
collector.record_feedback(event_id=124, is_real=False, event_type='loitering')

# Obter estatísticas
stats = collector.get_calibration_data('intrusion')
# {'total_samples': 50, 'true_positives': 45, 'false_positives': 5, 'false_positive_rate': 0.1}

# Sugerir ajuste de threshold
suggested = collector.suggest_threshold_adjustment('intrusion')
# Retorna threshold ideal baseado em feedback
```

## ✅ Critérios de Aceitação (Passo 4)

- [x] ValidatorModel carrega thresholds do config.py
- [x] Método `validate_event_candidate()` implementado
- [x] AlertManager integrado com validator
- [x] Eventos salvos no database com `validator_score`
- [x] Alertas criados **apenas** para eventos validados
- [x] Tabela `user_feedback` para calibração
- [x] Testes unitários passando (16 testes)
- [x] Logging detalhado de aprovações/rejeições

## 📝 Arquivos Modificados/Criados

### Modificados:
- `config/config.py` - Adicionadas 7 configurações de validator
- `src/ai/validator_model.py` - Imports de config, validate_event_candidate(), custom_thresholds
- `src/core/alert_manager.py` - Validator integration, process_event_candidate()
- `src/core/database.py` - Tabela user_feedback, métodos de feedback

### Criados:
- `tests/test_validator_model.py` - 16 testes completos

## 🚀 Próximo Passo: Passo 5 - Email Queue Integration

Com validator gating funcionando, o próximo passo é integrar **email_queue.py** para:

1. **Remover email do hot path**: AlertManager não bloqueia enviando emails
2. **Retry logic**: Reenviar automaticamente em caso de falha SMTP
3. **Background worker**: Thread separada processando fila
4. **Diagnostics**: Mostrar tamanho da fila e último erro

**Duração real**: ~25 minutos  
**Status**: ✅ CONCLUÍDO

---

Pronto para **Passo 5: Email Queue** 🚀
