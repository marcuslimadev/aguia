# Plano de 10 Passos para Publicação na Microsoft Store

**Objetivo:** Completar o desenvolvimento do Edge Property Security AI e prepará-lo para publicação na Microsoft Store  
**Status atual:** Módulos avançados existem mas não estão integrados (runtime usa cv2/Torch legacy)  
**Meta:** Sistema Lexius-class, Store-grade, zero-touch  

---

## 📋 Visão Geral dos Passos

| Passo | Prioridade | Descrição | Tempo Estimado | Dependências |
|-------|-----------|-----------|----------------|--------------|
| 1 | P0.1 | Integrar FFmpeg RTSP Reader | 3-4 dias | - |
| 2 | P0.2 | Migrar para ONNX Detector | 2-3 dias | Passo 1 |
| 3 | P0.3 | Integrar Event Engine Temporal | 4-5 dias | Passos 1-2 |
| 4 | P0.4 | Implementar Validator Gating | 2-3 dias | Passo 3 |
| 5 | P0.5 | Integrar Email Queue | 1-2 dias | Passo 4 |
| 6 | P0.6 | Integrar Store Licensing | 2-3 dias | - |
| 7 | P1 | ONVIF Discovery + UX Polish | 3-4 dias | Passos 1-6 |
| 8 | P2 | DPAPI Security + Diagnostics | 2-3 dias | Passo 6 |
| 9 | P2 | Testes End-to-End + Performance | 3-4 dias | Passos 1-8 |
| 10 | P2 | Build Pipeline + Store Package | 2-3 dias | Passos 1-9 |

**Tempo total estimado:** 24-34 dias (4-6 semanas)

---

## 🚀 Passo 1: Integrar FFmpeg RTSP Reader

**Prioridade:** P0.1 - CRÍTICO  
**Objetivo:** Substituir `cv2.VideoCapture` por `RtspReader` com FFmpeg

### Tarefas

#### 1.1 Corrigir bugs no `src/ai/rtsp_reader.py`
- [ ] **Problema de resolução:** Remover hardcode de 1920×1080
  - Probar resolução do stream com `ffprobe` ou adaptar dinamicamente
  - Ou usar `-vf scale=W:H` no FFmpeg para forçar tamanho de saída
  
- [ ] **Risco de deadlock:** stderr do subprocess
  - Drenar stderr em thread separada OU redirecionar para `DEVNULL`
  - Testar com streams que geram muito log

- [ ] **Reconexão automática:**
  - Implementar exponential backoff: 1s, 2s, 4s, 8s, max 60s
  - Detectar timeout de frame (ex: 5 segundos sem frame)
  - Logging claro de tentativas de reconexão

- [ ] **FPS pacing / frame dropping:**
  - Implementar controle de taxa: se stream é 30 FPS mas queremos 5 FPS
  - Evitar acúmulo de frames (buffer runaway)
  - Calcular timestamps para frame skip inteligente

#### 1.2 Refatorar `src/ai/video_processor.py`
- [ ] Substituir inicialização:
  ```python
  # REMOVER
  cap = cv2.VideoCapture(rtsp_url)
  
  # ADICIONAR
  from src.ai.rtsp_reader import RtspReader
  reader = RtspReader(rtsp_url, target_fps=5, target_size=(1280, 720))
  ```

- [ ] Substituir loop de captura:
  ```python
  # REMOVER
  ret, frame = cap.read()
  
  # ADICIONAR
  for frame in reader.frames():
      # processar frame
  ```

- [ ] Adicionar tratamento de reconexão no UI
  - Mostrar status "Reconnecting..." na UI de câmeras
  - Contador de reconexões em diagnósticos

#### 1.3 Testes de validação
- [ ] Testar com resoluções diferentes: 640×480, 1280×720, 1920×1080
- [ ] Simular queda de rede (desconectar/reconectar cabo)
- [ ] Testar com stream de FPS alto (30fps) e verificar pacing
- [ ] Verificar consumo de CPU e memória (não deve vazar)

**Critério de aceite:** Sistema conecta/reconecta automaticamente em todas as resoluções sem travamento.

---

## 🤖 Passo 2: Migrar para ONNX Detector

**Prioridade:** P0.2 - CRÍTICO  
**Objetivo:** Remover Torch/Ultralytics do runtime, usar apenas ONNX

### Tarefas

#### 2.1 Preparar modelo ONNX
- [ ] Exportar YOLOv8m para ONNX (ferramenta de dev):
  ```python
  from ultralytics import YOLO
  model = YOLO("yolov8m.pt")
  model.export(format="onnx", imgsz=640, half=False)
  ```

- [ ] Verificar NMS no modelo exportado:
  - Se NMS não está no modelo, implementar em `yolo_onnx.py`
  - Testar que não gera boxes duplicadas

- [ ] Copiar modelo para `C:/ProgramData/EdgeAI/models/yolov8m.onnx`

#### 2.2 Refatorar `src/ai/video_processor.py`
- [ ] Criar interface de detector:
  ```python
  class Detector(ABC):
      @abstractmethod
      def detect(self, frame: np.ndarray) -> List[Detection]:
          pass
  ```

- [ ] Substituir Ultralytics:
  ```python
  # REMOVER
  from ultralytics import YOLO
  self.model = YOLO(model_path)
  
  # ADICIONAR
  from src.ai.yolo_onnx import YOLOONNXDetector
  self.detector = YOLOONNXDetector(
      model_path="C:/ProgramData/EdgeAI/models/yolov8m.onnx",
      conf_threshold=0.5
  )
  ```

- [ ] Atualizar chamadas de detecção:
  ```python
  # REMOVER
  results = self.model(frame)
  
  # ADICIONAR
  detections = self.detector.detect(frame)
  ```

#### 2.3 Atualizar requirements
- [ ] Mover `torch` e `ultralytics` para `requirements-dev.txt`
- [ ] Manter apenas `onnxruntime` em `requirements.txt`
- [ ] Atualizar `build_windows.py` para incluir `onnxruntime`, excluir `torch`

#### 2.4 Testes de validação
- [ ] Verificar que app **não importa torch** em runtime
- [ ] Comparar resultados ONNX vs Ultralytics (devem ser idênticos)
- [ ] Testar performance (ONNX deve ser similar ou melhor)
- [ ] Verificar tamanho do build (deve reduzir significativamente)

**Critério de aceite:** App roda sem Torch instalado, detecções são precisas e consistentes.

---

## ⚡ Passo 3: Integrar Event Engine Temporal

**Prioridade:** P0.3 - CRÍTICO  
**Objetivo:** Eventos são padrões temporais, não regras por frame

### Tarefas

#### 3.1 Integrar tracker de objetos
- [ ] Verificar se ByteTrack está funcionando em `video_processor.py`
- [ ] Garantir que detecções têm `track_id` persistente
- [ ] Implementar ou ajustar configurações de tracker:
  - Track age mínimo: 5 frames
  - IOU threshold: 0.3
  - Lost track timeout: 30 frames

#### 3.2 Conectar Event Engine
- [ ] Instanciar EventEngine em `video_processor.py`:
  ```python
  from src.ai.event_engine import EventEngine
  self.event_engine = EventEngine(zones_config, schedules)
  ```

- [ ] Pipeline de processamento:
  ```python
  # 1. Detector
  detections = self.detector.detect(frame)
  
  # 2. Tracker
  tracked = self.tracker.update(detections)
  
  # 3. Event Engine
  events = self.event_engine.process_frame(tracked, timestamp, camera_id)
  
  # 4. Para cada evento candidato
  for event in events:
      # Próximo passo: validator
      pass
  ```

#### 3.3 Implementar eventos "hero"
- [ ] **Intrusion (Invasão):**
  - Pessoa detectada em zona proibida por > 3 segundos
  - Config: `intrusion_dwell_time`, `intrusion_zones`

- [ ] **Loitering (Rondando):**
  - Pessoa na mesma área por > 60 segundos
  - Config: `loitering_threshold`, `loitering_zones`

- [ ] Adicionar configs em `config/config.py`:
  ```python
  # Event thresholds
  INTRUSION_DWELL_TIME = 3  # segundos
  LOITERING_THRESHOLD = 60  # segundos
  ```

#### 3.4 Atualizar database schema
- [ ] Criar tabela `events`:
  ```sql
  CREATE TABLE events (
      id INTEGER PRIMARY KEY,
      camera_id INTEGER,
      event_type TEXT,
      confidence REAL,
      timestamp TIMESTAMP,
      evidence_frames TEXT,  -- JSON array de paths
      validated BOOLEAN,
      validator_score REAL,
      FOREIGN KEY (camera_id) REFERENCES cameras(id)
  )
  ```

#### 3.5 Testes de validação
- [ ] Testar cenário de intrusion: pessoa entra em zona por 5 segundos
- [ ] Testar loitering: pessoa fica parada por 70 segundos
- [ ] Verificar que eventos NÃO são gerados por detecções momentâneas
- [ ] Logs devem mostrar estados intermediários do EventEngine

**Critério de aceite:** Pelo menos 1 tipo de evento (intrusion ou loitering) funciona com precisão temporal.

---

## ✅ Passo 4: Implementar Validator Gating

**Prioridade:** P0.4 - CRÍTICO  
**Objetivo:** Nenhum alerta é enviado sem aprovação do validator

### Tarefas

#### 4.1 Integrar ValidatorModel
- [ ] Carregar modelo validator em `video_processor.py`:
  ```python
  from src.ai.validator_model import ValidatorModel
  self.validator = ValidatorModel(
      model_path="C:/ProgramData/EdgeAI/models/validator.onnx"
  )
  ```

- [ ] Para cada evento candidato:
  ```python
  # Crop do frame com bbox
  crop = frame[y1:y2, x1:x2]
  
  # Score do validator
  score = self.validator.validate(crop, event_type, metadata)
  
  # Comparar com threshold
  threshold = config.get(f"validator_threshold_{event_type}", 0.7)
  
  if score >= threshold:
      # Aprovar evento
      self.send_to_alert_queue(event)
  else:
      # Rejeitar (log para análise)
      logger.info(f"Evento rejeitado pelo validator: {event_type} score={score}")
  ```

#### 4.2 Adicionar thresholds em config
- [ ] Em `config/config.py`:
  ```python
  # Validator thresholds per event type
  VALIDATOR_THRESHOLD_INTRUSION = 0.70
  VALIDATOR_THRESHOLD_LOITERING = 0.65
  VALIDATOR_THRESHOLD_THEFT = 0.80
  ```

#### 4.3 Atualizar database
- [ ] Salvar score do validator nos eventos:
  ```python
  db_manager.add_event(
      camera_id=camera_id,
      event_type=event_type,
      confidence=event_confidence,
      validator_score=score,
      validated=(score >= threshold)
  )
  ```

#### 4.4 UI de feedback
- [ ] Adicionar campo em Alerts History Page:
  - Mostrar validator score (0-100%)
  - Botão "Report False Positive" / "Report Miss"

- [ ] Salvar feedback do usuário:
  ```python
  db_manager.add_feedback(
      event_id=event_id,
      user_label="false_positive" | "true_positive" | "miss",
      timestamp=datetime.now()
  )
  ```

#### 4.5 Testes de validação
- [ ] Testar que eventos com score baixo NÃO geram alertas
- [ ] Testar que eventos com score alto SIM geram alertas
- [ ] Verificar que todos os eventos são salvos no DB (mesmo rejeitados)
- [ ] UI mostra feedback corretamente

**Critério de aceite:** Zero alertas enviados sem passar pelo validator; feedback é capturado.

---

## 📧 Passo 5: Integrar Email Queue

**Prioridade:** P0.5 - CRÍTICO  
**Objetivo:** Nunca enviar email no hot path de detecção

### Tarefas

#### 5.1 Refatorar AlertManager
- [ ] Instanciar EmailQueue em `alert_manager.py`:
  ```python
  from src.core.email_queue import EmailQueue
  self.email_queue = EmailQueue(db_manager)
  ```

- [ ] Substituir envio direto por enqueue:
  ```python
  # REMOVER
  self._send_email_smtp(to, subject, body, attachments)
  
  # ADICIONAR
  self.email_queue.enqueue(
      to=recipient_email,
      subject=f"Security Alert: {event_type}",
      body=alert_body,
      attachments=snapshot_paths,
      priority="high"
  )
  ```

#### 5.2 Implementar worker thread
- [ ] Iniciar worker em `main.py`:
  ```python
  # Após inicializar alert_manager
  email_queue = alert_manager.email_queue
  email_queue.start_worker()  # Thread em background
  ```

- [ ] Worker loop em `email_queue.py`:
  ```python
  def worker_loop(self):
      while self.running:
          # Pegar próximo email da fila
          email = self.get_next()
          if email:
              try:
                  self._send_smtp(email)
                  self.mark_sent(email.id)
              except Exception as e:
                  self.mark_failed(email.id, str(e))
                  self.schedule_retry(email.id)
          time.sleep(1)
  ```

#### 5.3 Implementar retry logic
- [ ] Exponential backoff:
  - Tentativa 1: imediato
  - Tentativa 2: +1 min
  - Tentativa 3: +5 min
  - Tentativa 4: +15 min
  - Tentativa 5: +1 hora
  - Máximo: 5 tentativas

- [ ] Salvar estado no database:
  ```sql
  CREATE TABLE email_queue (
      id INTEGER PRIMARY KEY,
      to_address TEXT,
      subject TEXT,
      body TEXT,
      attachments TEXT,  -- JSON
      status TEXT,  -- pending, sending, sent, failed
      retry_count INTEGER,
      next_retry_at TIMESTAMP,
      last_error TEXT,
      created_at TIMESTAMP
  )
  ```

#### 5.4 Diagnostics UI
- [ ] Adicionar em Diagnostics Page:
  - **Email Queue Status:**
    - Queue length: X mensagens pendentes
    - Last sent: timestamp
    - Last error: mensagem de erro
    - Retry queue: X mensagens aguardando retry

#### 5.5 Testes de validação
- [ ] Testar envio bem-sucedido
- [ ] Simular falha SMTP (servidor down) e verificar retry
- [ ] Verificar que detecção NÃO trava se email falhar
- [ ] Diagnostics mostram estado correto da fila

**Critério de aceite:** Falhas de email não afetam detecção; alertas são retentados automaticamente.

---

## 🔐 Passo 6: Integrar Store Licensing

**Prioridade:** P0.6 - CRÍTICO  
**Objetivo:** Enforcement de limites de câmeras e duração via Microsoft Store

### Tarefas

#### 6.1 Unificar LicenseManager
- [ ] Refatorar `src/core/license_manager.py`:
  ```python
  class LicenseManager:
      def __init__(self, db_manager):
          self.db = db_manager
          
          # Detectar se está em ambiente Store
          if self._is_store_package():
              from src.core.store_licensing import StoreContext
              self.store = StoreContext()
          else:
              self.store = None  # Dev mode: usar licença local
      
      def get_camera_limit(self, user_id):
          if self.store:
              # Produção: consultar Store
              return self.store.get_camera_limit()
          else:
              # Dev: usar trial local
              license = self.db.get_license(user_id)
              return license['camera_limit']
  ```

#### 6.2 Enforcement na UI
- [ ] Em `cameras_page.py`, ao adicionar câmera:
  ```python
  def add_camera(self):
      current_count = len(self.db_manager.get_cameras(self.user_id))
      limit = self.license_manager.get_camera_limit(self.user_id)
      
      if current_count >= limit:
          QMessageBox.warning(
              self,
              "Camera Limit Reached",
              f"Your license allows {limit} cameras.\n"
              f"Upgrade your plan to add more."
          )
          return
      
      # Prosseguir com adição
  ```

#### 6.3 Enforcement no engine
- [ ] Em `video_processor.py`, ao iniciar processamento:
  ```python
  def start_processing(self, camera_ids):
      limit = self.license_manager.get_camera_limit(self.user_id)
      
      if len(camera_ids) > limit:
          logger.error(f"Cannot process {len(camera_ids)} cameras (limit: {limit})")
          raise LicenseError(f"License allows only {limit} cameras")
      
      # Iniciar processamento
  ```

#### 6.4 UI de status de licença
- [ ] Adicionar em Settings Page:
  - **License Status:**
    - Type: Trial / Pro / Enterprise
    - Camera limit: 2 / 10 / Unlimited
    - Expires: date ou "Never"
    - Status: Active / Expired
  - Botão: "Upgrade License" (link para Store ou web)

#### 6.5 Testes de validação
- [ ] Testar modo dev (local trial): 2 câmeras, 7 dias
- [ ] Simular Store entitlement (se possível com sandbox)
- [ ] Verificar que UI bloqueia adição de câmeras além do limite
- [ ] Verificar que engine não processa câmeras além do limite
- [ ] Licença expirada: UI mostra status mas não trava app

**Critério de aceite:** Limites são enforçados tanto na UI quanto no engine; status é visível.

---

## 🎨 Passo 7: ONVIF Discovery + UX Polish

**Prioridade:** P1 - UX Zero-Touch  
**Objetivo:** Onboarding plug-and-play + experiência polida

### Tarefas

#### 7.1 Integrar ONVIF Discovery
- [ ] Adicionar botão em Cameras Page:
  - "🔍 Detect Cameras on Network"

- [ ] Implementar ação:
  ```python
  def detect_cameras(self):
      from src.ai.onvif_discovery import discover_cameras
      
      # Mostrar loading
      progress = QProgressDialog("Scanning network...", "Cancel", 0, 0, self)
      progress.show()
      
      # Descobrir câmeras (thread separada)
      cameras = discover_cameras(timeout=10)
      
      # Mostrar dialog com resultados
      dialog = CameraDiscoveryDialog(cameras, self)
      if dialog.exec():
          selected = dialog.get_selected_cameras()
          for cam in selected:
              self.db_manager.add_camera(
                  user_id=self.user_id,
                  name=cam['name'],
                  rtsp_url=cam['rtsp_url']
              )
  ```

#### 7.2 RTSP URL Presets
- [ ] Adicionar dropdown em Add Camera dialog:
  - **Camera Brand:**
    - Hikvision: `rtsp://{ip}:554/Streaming/Channels/101`
    - Dahua: `rtsp://{ip}:554/cam/realmonitor?channel=1&subtype=0`
    - Uniview: `rtsp://{ip}:554/media/video1`
    - Axis: `rtsp://{ip}/axis-media/media.amp`
    - Generic RTSP: `rtsp://{ip}:554/`

- [ ] Auto-preencher URL baseado na seleção

#### 7.3 Alert UX melhorado
- [ ] Email template profissional:
  - Logo do app
  - Detalhes: Camera name, Zone, Event type, Timestamp
  - Snapshot inline (não anexo)
  - Botões: "View All Alerts" (link para app), "Report Issue"

- [ ] Alert History Page filtros:
  - Date range picker
  - Camera selector (multi-select)
  - Event type selector
  - Status: All / Acknowledged / Unacknowledged

- [ ] Export to CSV:
  - Botão "Export"
  - Colunas: timestamp, camera, zone, event_type, confidence, validator_score

#### 7.4 Dashboard melhorado
- [ ] Cards com estatísticas:
  - Total Alerts (24h, 7d, 30d)
  - Cameras Online/Offline
  - Top Event Types (chart)
  - System Health (CPU/RAM/Disk)

- [ ] Live preview thumbnails:
  - Miniaturas das câmeras ativas
  - Click para ver detalhes

#### 7.5 Testes de validação
- [ ] ONVIF discovery encontra pelo menos 1 câmera em rede de teste
- [ ] Presets geram URLs corretas
- [ ] Email template renderiza corretamente em Gmail/Outlook
- [ ] Filtros e export funcionam corretamente

**Critério de aceite:** Usuário não-técnico consegue adicionar câmera em < 2 minutos.

---

## 🔒 Passo 8: DPAPI Security + Diagnostics

**Prioridade:** P2 - Security & Supportability  
**Objetivo:** Credenciais seguras + diagnósticos completos

### Tarefas

#### 8.1 Implementar DPAPI para credenciais
- [ ] Refatorar armazenamento de credenciais RTSP:
  ```python
  from src.core.dpapi_security import encrypt_data, decrypt_data
  
  # Ao salvar câmera
  username_encrypted = encrypt_data(username)
  password_encrypted = encrypt_data(password)
  
  db_manager.add_camera(
      user_id=user_id,
      name=name,
      rtsp_url=rtsp_url,
      username=username_encrypted,  # ciphertext
      password=password_encrypted   # ciphertext
  )
  
  # Ao ler câmera
  camera = db_manager.get_camera(camera_id)
  username = decrypt_data(camera['username'])
  password = decrypt_data(camera['password'])
  ```

- [ ] Refatorar armazenamento de credenciais SMTP:
  ```python
  # Similar para email settings
  smtp_password_encrypted = encrypt_data(smtp_password)
  db_manager.save_email_settings(
      user_id=user_id,
      smtp_server=smtp_server,
      smtp_username=smtp_username,
      smtp_password=smtp_password_encrypted
  )
  ```

#### 8.2 Atualizar database schema
- [ ] Migração para renomear colunas:
  ```sql
  -- Renomear para deixar claro que é ciphertext
  ALTER TABLE cameras RENAME COLUMN username TO username_encrypted;
  ALTER TABLE cameras RENAME COLUMN password TO password_encrypted;
  ALTER TABLE email_settings RENAME COLUMN smtp_password TO smtp_password_encrypted;
  ```

#### 8.3 Diagnostics Page completa
- [ ] **Camera Status Section:**
  - Para cada câmera:
    - Name, Status (Online/Offline/Reconnecting)
    - Last frame: timestamp
    - FPS atual
    - Reconnection count
    - Last error

- [ ] **System Health Section:**
  - CPU usage (%)
  - RAM usage (MB / %)
  - Disk space: C:/ProgramData/EdgeAI (MB usado / livre)
  - Engine status: Running / Stopped
  - Active threads count

- [ ] **Email Queue Section:**
  - Queue length (pending)
  - Last sent: timestamp
  - Last error: mensagem completa
  - Retry queue length
  - Botão: "Test Email" (envia email de teste)

- [ ] **Licensing Section:**
  - License type
  - Camera limit
  - Expiration date
  - Days remaining

- [ ] **Export Bundle:**
  - Botão: "Export Diagnostics Bundle"
  - Gera ZIP com:
    - Logs (últimas 24h)
    - Config (anonymizado - sem senhas)
    - System info (Windows version, Python version, etc.)
    - Stats (camera count, alert count, etc.)

#### 8.4 Testes de validação
- [ ] Credenciais são armazenadas como ciphertext no SQLite
- [ ] App consegue decriptar e usar credenciais
- [ ] Diagnostics mostra todas as métricas corretamente
- [ ] Export bundle é gerado e contém arquivos corretos

**Critério de aceite:** Zero credenciais em plaintext; diagnostics substituem 80% dos casos de suporte.

---

## 🧪 Passo 9: Testes End-to-End + Performance

**Prioridade:** P2 - Quality Assurance  
**Objetivo:** Sistema estável e performático

### Tarefas

#### 9.1 Testes de integração E2E
- [ ] **Fluxo completo 1: Onboarding → Alert**
  1. Novo usuário se registra
  2. Adiciona câmera via ONVIF discovery
  3. Configura zona e regras
  4. Configura email
  5. Simula evento (pessoa em zona proibida)
  6. Verifica que email é recebido com snapshot correto

- [ ] **Fluxo completo 2: Multi-câmera**
  1. Adicionar 3 câmeras
  2. Iniciar processamento simultâneo
  3. Gerar eventos em câmeras diferentes
  4. Verificar que todos são detectados e alertados

- [ ] **Fluxo completo 3: Reconexão**
  1. Câmera conectada e processando
  2. Simular queda de rede (desconectar)
  3. Aguardar 10 segundos
  4. Reconectar rede
  5. Verificar que câmera reconecta automaticamente

#### 9.2 Testes de limites de licença
- [ ] Testar limite de 2 câmeras (trial):
  - Adicionar 2 câmeras: OK
  - Tentar adicionar 3ª: bloqueado na UI
  - Tentar processar 3 câmeras: bloqueado no engine

- [ ] Testar expiração:
  - Simular licença expirada (alterar data no DB)
  - Verificar que processamento para
  - Verificar que UI mostra status correto
  - Verificar que configuração continua acessível

#### 9.3 Testes de performance
- [ ] **Baseline single camera (1920×1080):**
  - Medir: CPU %, RAM MB, FPS de processamento
  - Target: < 30% CPU, < 1GB RAM, 5 FPS estável
  - Duração: 30 minutos contínuos

- [ ] **Multi-camera (3 câmeras simultâneas):**
  - Medir: CPU %, RAM MB, FPS por câmera
  - Target: < 60% CPU, < 2GB RAM, 5 FPS por câmera
  - Duração: 30 minutos contínuos

- [ ] **Memory leak test:**
  - Executar por 2 horas contínuas
  - Verificar que RAM não cresce indefinidamente
  - Target: crescimento < 100MB após estabilização

- [ ] **Email queue stress test:**
  - Gerar 100 alertas rapidamente
  - SMTP server offline
  - Verificar que todos são enfileirados
  - Ligar SMTP
  - Verificar que todos são enviados com retry

#### 9.4 Testes de robustez
- [ ] Câmera com stream ruim (pacotes perdidos)
- [ ] Câmera com credenciais inválidas
- [ ] Câmera com URL incorreta
- [ ] SMTP com senha errada
- [ ] Disk cheio (simular)
- [ ] Database corrompido (backup/restore)

#### 9.5 Testes de UI
- [ ] Todas as páginas navegam corretamente
- [ ] Formulários validam entrada
- [ ] Botões têm feedback visual
- [ ] Loading states aparecem quando apropriado
- [ ] Mensagens de erro são claras e acionáveis

#### 9.6 Criar suite de testes automatizados
- [ ] Expandir `tests/` com testes unitários:
  - `test_rtsp_reader.py`
  - `test_onnx_detector.py`
  - `test_event_engine.py`
  - `test_validator.py`
  - `test_email_queue.py`
  - `test_license_manager.py`

- [ ] Configurar pytest-cov para coverage:
  - Target: > 70% coverage em módulos core

- [ ] CI/CD (opcional):
  - GitHub Actions para rodar testes em cada commit

**Critério de aceite:** Todos os fluxos E2E funcionam; performance atende targets; coverage > 70%.

---

## 📦 Passo 10: Build Pipeline + Store Package

**Prioridade:** P2 - Deployment  
**Objetivo:** Build automatizado pronto para Microsoft Store

### Tarefas

#### 10.1 Finalizar build_windows.py
- [ ] Script completo de build:
  ```python
  # 1. Pre-flight checks
  check_onnx_models_exist()
  check_manifest_capabilities()
  check_version_consistency()
  
  # 2. Build com Nuitka
  build_executable()
  
  # 3. Copiar assets
  copy_models_to_dist()
  copy_translations_to_dist()
  
  # 4. Criar MSIX package
  create_msix_package()
  
  # 5. Assinar package (se certificado disponível)
  sign_package()
  
  # 6. Validar package
  validate_msix()
  ```

- [ ] Pre-flight checks:
  ```python
  def check_onnx_models_exist():
      required = ['yolov8m.onnx', 'validator.onnx']
      for model in required:
          path = MODELS_DIR / model
          if not path.exists():
              raise FileNotFoundError(f"Model missing: {model}")
  
  def check_manifest_capabilities():
      # Ler AppxManifest.xml
      # Verificar que só tem internetClient
      # Warn se tiver webcam, documentsLibrary, etc.
  
  def check_version_consistency():
      # Version em config.py == AppxManifest.xml
  ```

#### 10.2 Minimizar AppxManifest.xml
- [ ] Remover capabilities desnecessárias:
  ```xml
  <Capabilities>
    <!-- MANTER -->
    <Capability Name="internetClient" />
    
    <!-- REMOVER (se existir) -->
    <!-- <DeviceCapability Name="webcam" /> -->
    <!-- <rescap:Capability Name="documentsLibrary" /> -->
    <!-- <rescap:Capability Name="picturesLibrary" /> -->
  </Capabilities>
  ```

- [ ] Verificar Identity:
  ```xml
  <Identity
    Name="EdgeSecurity.EdgePropertySecurityAI"
    Publisher="CN=EdgeSecurity"
    Version="1.0.0.0" />
  ```

- [ ] Verificar TargetDeviceFamily:
  ```xml
  <TargetDeviceFamily 
    Name="Windows.Desktop" 
    MinVersion="10.0.19041.0" 
    MaxVersionTested="10.0.22621.0" />
  ```

#### 10.3 Otimizar tamanho do package
- [ ] Excluir do build:
  - Torch (já removido em P0.2)
  - CUDA libs (se não usar GPU)
  - Dev tools (pytest, etc.)
  - Arquivos .pyc desnecessários

- [ ] Comprimir assets:
  - Modelos ONNX (verificar se já comprimidos)
  - Imagens UI (otimizar PNGs)

- [ ] Target: < 500 MB total

#### 10.4 Documentação de build
- [ ] Atualizar `SETUP_WINDOWS.md`:
  - Requisitos de build (Windows SDK, certificado)
  - Passo a passo de build completo
  - Troubleshooting comum

- [ ] Criar `BUILD_CHECKLIST.md`:
  - [ ] Version bump
  - [ ] CHANGELOG atualizado
  - [ ] Testes passando
  - [ ] Models presentes
  - [ ] Build clean
  - [ ] MSIX validado
  - [ ] Package assinado

#### 10.5 Store submission prep
- [ ] Preparar assets da Store:
  - Screenshots (1920×1080): Dashboard, Cameras, Alerts
  - App icon (512×512)
  - Promotional images
  - App description (EN, PT-BR)
  - Privacy policy URL
  - Support contact

- [ ] Atualizar `MICROSOFT_STORE_GUIDE.md`:
  - Link para Partner Center
  - Instruções de submission passo a passo
  - Requisitos de certificação
  - Timeline esperado

#### 10.6 Testes finais do package
- [ ] Instalar MSIX em máquina limpa (VM)
- [ ] Verificar que app inicia corretamente
- [ ] Verificar que todos os assets estão presentes
- [ ] Testar fluxo completo no package instalado
- [ ] Desinstalar e verificar que limpa arquivos

**Critério de aceite:** Um comando gera MSIX pronto para Store; documentação permite reprodução.

---

## ✅ Critérios de "Pronto para Publicação"

O sistema está pronto quando:

- [x] **P0 Completo:**
  - ✅ FFmpeg RTSP com auto-reconexão
  - ✅ ONNX runtime (sem Torch)
  - ✅ Event Engine integrado (eventos temporais)
  - ✅ Validator gateia todos os alertas
  - ✅ Email queue com retry
  - ✅ Store licensing enforçado
  - ✅ AppxManifest minimalista

- [x] **P1 Completo:**
  - ✅ ONVIF discovery funcional
  - ✅ UX polida e responsiva
  - ✅ Diagnostics auto-suficiente

- [x] **P2 Completo:**
  - ✅ DPAPI para credenciais
  - ✅ Testes E2E passando
  - ✅ Performance dentro dos targets
  - ✅ Build automatizado
  - ✅ MSIX assinado e validado

- [x] **Documentação:**
  - ✅ README atualizado
  - ✅ Store guide completo
  - ✅ Build checklist
  - ✅ Copilot instructions (já feito!)

---

## 📊 Tracking de Progresso

Use este checklist para marcar o progresso:

```
Fase 1 - Core Runtime (Passos 1-3):  ⬜ 0/3
  ⬜ Passo 1: FFmpeg RTSP Reader
  ⬜ Passo 2: ONNX Detector
  ⬜ Passo 3: Event Engine

Fase 2 - Alertas & Segurança (Passos 4-6):  ⬜ 0/3
  ⬜ Passo 4: Validator Gating
  ⬜ Passo 5: Email Queue
  ⬜ Passo 6: Store Licensing

Fase 3 - UX & Polish (Passos 7-8):  ⬜ 0/2
  ⬜ Passo 7: ONVIF + UX
  ⬜ Passo 8: DPAPI + Diagnostics

Fase 4 - QA & Deploy (Passos 9-10):  ⬜ 0/2
  ⬜ Passo 9: Testes E2E
  ⬜ Passo 10: Build & Package

TOTAL: ⬜ 0/10 passos completos
```

---

## 🎯 Próximos Passos Imediatos

**Recomendação:** Começar pelo Passo 1 (FFmpeg RTSP Reader)

**Ação:**
1. Abrir `src/ai/rtsp_reader.py`
2. Corrigir os 4 bugs críticos (resolução, stderr, reconnect, pacing)
3. Refatorar `src/ai/video_processor.py` para usar RtspReader
4. Testar com câmeras reais em diferentes resoluções

**Comando para começar:**
```bash
# Criar branch de feature
git checkout -b feature/p0-1-ffmpeg-rtsp-reader

# Rodar testes existentes
pytest tests/ -v

# Começar desenvolvimento
code src/ai/rtsp_reader.py
```

---

**Dúvidas ou quer ajuda para começar algum passo específico? Estou pronto para auxiliar!**
