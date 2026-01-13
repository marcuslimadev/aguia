# Edge Property Security AI — Deep Status Audit & Required Corrections (Lexius Complete)

**Build under review:** `edge_property_security_ai_lexius_complete.zip`  
**Audit date:** 2026-01-12  
**Goal:** Produce a concrete, engineering-ready list of **corrections + implementations** to reach a **Lexius‑class, Store‑grade, zero-touch** product.

---

## 0) Executive Summary (What’s good vs what’s missing)

### What’s already strong
- Product-like repo structure (UI, core, AI, tests, build, manifest, docs).
- Dedicated modules already exist for:
  - FFmpeg RTSP ingestion (`src/ai/rtsp_reader.py`)
  - ONNX detector (`src/ai/yolo_onnx.py`)
  - Temporal event reasoning (`src/ai/event_engine.py`)
  - Validator model (`src/ai/validator_model.py`)
  - Email outbox queue (`src/core/email_queue.py`)
  - DPAPI utilities (`src/core/dpapi_security.py`)
  - Store licensing provider (`src/core/store_licensing.py`)
  - ONVIF discovery (`src/ai/onvif_discovery.py`)
- UI pages exist for:
  - Cameras, alerts history, diagnostics, feedback.

### The hard truth (current runtime is not using the best modules)
The running pipeline is still wired to:
- `cv2.VideoCapture(rtsp_url)` (fragile RTSP)
- `ultralytics.YOLO(...)` / Torch runtime (Store-unfriendly)

**Critical gap:** the “Lexius-class” modules exist but are mostly **not integrated** into the active runtime path.

---

## 1) Concrete Findings (Wiring / Integration)

### 1.1 Video ingestion path
- `src/ai/video_processor.py` uses `cv2.VideoCapture` and imports `ultralytics`.
- `src/ai/rtsp_reader.py` exists but is **not referenced** by runtime components.

**Required:** switch runtime ingestion to FFmpeg-based reader.

### 1.2 ONNX detector path
- `src/ai/yolo_onnx.py` exists (onnxruntime), but is **not used** by `video_processor.py`.
- Runtime still uses Torch.

**Required:** switch runtime detector to ONNX.

### 1.3 Event semantics / temporal reasoning
- `src/ai/event_engine.py` exists but is **not wired**.
- Without temporal state, “loitering / intrusion / theft patterns” will have high false positives.

**Required:** event engine becomes the source of “events” (not per-frame rules).

### 1.4 False-positive validation
- `src/ai/validator_model.py` exists but is **not wired** into the alert pipeline.
- You explicitly decided: **alerts only after validator approves**.

**Required:** validator gates every alert.

### 1.5 Licensing / Store entitlements
- `src/core/store_licensing.py` exists.
- `src/core/license_manager.py` currently implements local licensing and does not call Store entitlements.

**Required:** unify licensing under StoreContext when packaged.

### 1.6 Credential protection
- `src/core/dpapi_security.py` exists but is **not used** to protect stored RTSP/SMTP secrets.

**Required:** encrypt secrets at rest.

### 1.7 ONVIF discovery
- `src/ai/onvif_discovery.py` exists but is **not used** by UI camera onboarding.

**Required:** add “Detect cameras” flow to match Lexius plug‑and‑play.

---

## 2) Required Corrections & Implementations (Prioritized)

> Use this as the authoritative engineering TODO.  
> Each item includes **what**, **where**, and **acceptance criteria**.

---

# P0 — Must fix (Reliability + Store feasibility)

## P0.1 Replace RTSP ingestion (VideoCapture → FFmpeg reader)
**Why:** RTSP robustness is the #1 operational failure source.

### Implementation
- Refactor `src/ai/video_processor.py` to use `RtspReader`:
  - `reader = RtspReader(rtsp_url, desired_fps, target_size)`
  - iterate `for frame in reader.frames(): ...`

### Fixes required inside `src/ai/rtsp_reader.py`
- **Resolution bug:** do not assume 1920×1080. Either:
  1) enforce output size using FFmpeg `-vf scale=W:H`, **or**
  2) probe actual width/height from stream and dynamically adapt.
- **Deadlock risk:** if `stderr=PIPE`, drain it (thread) or redirect to `DEVNULL`.
- Add:
  - frame timeout detection
  - reconnection with exponential backoff
  - FPS pacing / frame dropping strategy

### Acceptance Criteria
- Works reliably with:
  - 640×480, 1280×720, 1920×1080 streams
  - intermittent network drops (auto-recovers)
- No CPU runaway when camera outputs high FPS.

---

## P0.2 Switch runtime detector to ONNX (remove Torch dependency)
**Why:** Torch/Ultralytics in runtime makes MSIX size and stability unacceptable.

### Implementation
- Introduce a detector interface: `Detector.detect(frame) -> detections`.
- Replace Ultralytics in `video_processor.py` with `YOLOONNXDetector` from `src/ai/yolo_onnx.py`.
- Keep Ultralytics/Torch only in **dev tooling** (model export), not runtime.

### Acceptance Criteria
- App runs without Torch installed.
- ONNX model loads and detects persons/objects consistently.
- NMS behavior correct (no duplicate boxes). If NMS isn’t baked into model, implement it.

---

## P0.3 Wire the correct event pipeline (temporal events)
**Why:** “Security events” are temporal patterns. Frame-only rules are not enough.

### Implementation
Refactor processing chain to:
1. Reader yields frame
2. Detector outputs boxes/classes/conf
3. Tracker assigns `track_id` over time (SORT/ByteTrack)
4. EventEngine consumes tracks + zones + schedule
5. EventEngine emits `EventCandidate` (type, confidence, evidence frames)
6. ValidatorModel scores candidate
7. If approved → enqueue email (not send inline)

### Files
- `src/ai/video_processor.py` (main wiring)
- `src/ai/event_engine.py` (event definitions)
- Add or integrate tracker (if missing / placeholder)

### Acceptance Criteria
- At least one “hero event” is stable:
  - Intrusion OR Loitering
- Events are emitted only after temporal threshold conditions.

---

## P0.4 Validator gating (alerts only after validator approval)
**Why:** Your business requires low false positives.

### Implementation
- Integrate `src/ai/validator_model.py` as a gate:
  - candidate snapshot crop + metadata → validator score
  - compare against per-event threshold
- Add per-event thresholds in config:
  - `validator_threshold_intrusion`, `..._loitering`, etc.

### Acceptance Criteria
- No alerts bypass validator.
- Feedback UI can label events; labels stored.

---

## P0.5 Email delivery must be queued (never send in hot path)
**Why:** SMTP failures must not drop alerts; also avoid blocking inference threads.

### Implementation
- Ensure `src/core/email_queue.py` is used by AlertManager.
- Worker loop pulls queue and sends:
  - retries with exponential backoff
  - stores last error, next_retry_at

### Acceptance Criteria
- If SMTP fails, alert remains queued and retries automatically.
- Diagnostics show queue length and last error.

---

## P0.6 Microsoft Store licensing enforcement (camera limits + duration)
**Why:** monetization requires hard enforcement.

### Implementation
- Update `src/core/license_manager.py`:
  - When packaged/store context available → use `src/core/store_licensing.py`
  - Otherwise dev fallback local license
- Enforce camera limits:
  - at camera add time (UI)
  - at engine start (do not start processors beyond limit)
- Display entitlement status in UI

### Acceptance Criteria
- Cannot exceed purchased camera count.
- Expired license disables processing, but app stays usable for configuration.

---

## P0.7 AppxManifest permissions minimization
**Why:** Store review often rejects over-broad capabilities.

### Implementation
- Remove unnecessary capabilities:
  - `webcam` (RTSP IP cameras do not require webcam)
  - `documentsLibrary`, `picturesLibrary` (store under app private storage)
- Keep:
  - `internetClient` (RTSP + SMTP)

### Acceptance Criteria
- Store submission uses least-privilege manifest.

---

# P1 — Lexius-class UX and “Zero-touch” Operations

## P1.1 Plug-and-play onboarding (ONVIF discovery + presets)
**Why:** Lexius wins by low-friction setup.

### Implementation
- Add “Detect Cameras on Network” button in Cameras page:
  - Uses `src/ai/onvif_discovery.py`
  - Lists discovered cameras and generates RTSP templates
- Add brand RTSP presets in UI (Hikvision/Dahua/Uniview/Axis/Generic).

### Acceptance Criteria
- Non-technical user can add at least one camera without manual RTSP knowledge.

---

## P1.2 Alert UX upgrades (actionability)
### Implementation
- Alert record must include:
  - camera name, zone name, timestamp, event type, confidence
  - snapshot + optional short clip (future)
- Alert history page:
  - filters by date/camera/type
  - export CSV

### Acceptance Criteria
- Email contains all context needed for action in <10 seconds.

---

## P1.3 Feedback loop integration (training data capture)
### Implementation
- Feedback page writes labels to DB:
  - event_id, label, timestamp
- Use feedback to:
  - adjust thresholds (local calibration)
  - optionally fine-tune validator (later)

### Acceptance Criteria
- User can reduce false positives over time without contacting support.

---

## P1.4 Diagnostics page must be “support replacement”
### Implementation
Show:
- per-camera: online/offline, last_frame_ts, fps, reconnect_count
- system: CPU/RAM usage, engine status
- email: queue length, last send, last error
- licensing: entitlement + expiry
- “Export diagnostics bundle” (logs + config + anonymized stats)

### Acceptance Criteria
- A user can self-diagnose camera failures and email config issues.

---

# P2 — Performance, Security, and Store polish

## P2.1 DPAPI for secrets at rest (RTSP + SMTP)
### Implementation
- Use `src/core/dpapi_security.py` in:
  - camera credential storage
  - email credential storage
- Store only ciphertext in SQLite.

### Acceptance Criteria
- No plaintext credentials are stored on disk.

---

## P2.2 Performance tuning for multi-camera scaling
### Implementation
- Add per-camera frame sampling (e.g., 2–5 FPS for detection)
- Use separate threads/processes per camera with backpressure
- Add GPU optional path (ONNX Runtime GPU) as a future SKU

### Acceptance Criteria
- Stable operation with 1–10 cameras on typical SMB Windows PC (define baseline).

---

## P2.3 Internationalization completion
### Implementation
- Ensure all UI strings go through `src/utils/i18n.py`
- Verify translations exist in:
  - `translations/en.json` (base)
  - `pt-BR.json`, `es-ES.json`, `de-DE.json`

### Acceptance Criteria
- English is default.
- Language switch persists and fully updates UI.

---

## P2.4 Store packaging end-to-end (signing, MSIX, updates)
### Implementation
- `build_windows.py` should produce:
  - built executable
  - MSIX package
  - signed package (CI if possible)
- Add pre-flight checks:
  - verify ONNX files exist
  - verify manifest capabilities
  - verify versioning and identity

### Acceptance Criteria
- One command produces Store-ready MSIX.

---

## 3) Implementation Order (Recommended)
1. P0.1 RTSP FFmpeg integration + rtsp_reader fixes  
2. P0.2 ONNX detector integration  
3. P0.3 Tracker + EventEngine wiring (hero event)  
4. P0.4 Validator gating  
5. P0.5 Email queue wiring  
6. P0.6 Store licensing enforcement  
7. P0.7 Manifest minimization  
8. P1 onboarding (ONVIF + presets)  
9. P1 diagnostics + feedback improvements  
10. P2 DPAPI secrets + performance + Store pipeline polish  

---

## 4) Definition of “Done” (Perfect v1)
A “perfect v1” is achieved when:
- RTSP ingestion is robust (no freeze, auto-reconnect)
- Runtime has **no Torch**
- Events are temporal and low-noise
- Validator gates alerts (precision-first)
- Email is queued + reliable
- Store licensing enforces camera limits and expiry
- Onboarding is plug-and-play (ONVIF + presets)
- Diagnostics replaces support

---

## 5) Deliverables Requested (for the next engineering cycle)
- Updated `video_processor.py` using RtspReader + ONNX + tracker + event engine + validator
- Fixed `rtsp_reader.py` (resolution + stderr + reconnect + pacing)
- Store licensing integration in `license_manager.py`
- Alert pipeline uses `email_queue.py`
- ONVIF discovery wired into Cameras UI
- Manifest minimized + documented
- Regression tests:
  - license gating
  - email queue retry
  - event engine thresholds
