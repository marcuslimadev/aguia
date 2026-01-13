# Edge Property Security AI - Copilot Instructions

## Project Overview
This is a **Windows-native desktop application** for AI-powered property security with real-time RTSP video processing. Built for Microsoft Store distribution with PySide6 (Qt) UI, YOLOv8 object detection, and SQLite persistence. All video processing is done locally - **no cloud uploads**.

## ⚠️ CRITICAL: Current State vs Target Architecture

**The codebase contains TWO architectures:**
1. **Current runtime** (legacy): Uses `cv2.VideoCapture` + Torch/Ultralytics - **fragile, not Store-ready**
2. **Target modules** (Lexius-class): FFmpeg RTSP reader, ONNX detector, event engine, validator - **exist but NOT integrated**

**Your mission**: Migrate from #1 to #2 following the priorities in [edge_ai_lexius_complete_corrections_and_implementations.md](edge_ai_lexius_complete_corrections_and_implementations.md).

## Architecture

### Target Data Flow Pipeline (P0 work in progress)
```
FFmpeg RTSP Reader → ONNX Detection → Object Tracking → Event Engine (temporal) →
Validator Model → Email Queue → Database
```

### Component Boundaries
- **`src/ai/`**: Video processing pipeline
  - **Legacy (active)**: `video_processor.py` with cv2 + Ultralytics
  - **Target (to integrate)**: `rtsp_reader.py`, `yolo_onnx.py`, `event_engine.py`, `validator_model.py`
- **`src/core/`**: Business logic (auth, database, alerts, licensing, camera management)
  - **Target (to integrate)**: `email_queue.py`, `dpapi_security.py`, `store_licensing.py`
- **`src/ui/`**: PySide6 UI with page-based navigation (login, dashboard, cameras, alerts, etc.)
- **`config/config.py`**: **Single source of truth** for ALL constants (paths, thresholds, app metadata)

### Critical Architectural Decisions
- **Windows-first**: All paths use `C:/ProgramData/EdgeAI` on Windows (see [config/config.py](config/config.py#L9-L13))
- **Centralized configuration**: Import from `config.config`, never hardcode values
- **Dependency injection**: `main.py` initializes core managers (`DatabaseManager`, `AuthManager`, `AlertManager`) and passes them to UI components
- **Page-based UI**: `MainWindow` uses `QStackedWidget` for page navigation; all pages in `src/ui/pages/`
- **⚠️ Runtime is in transition**: Current code uses cv2/Torch, but target uses FFmpeg/ONNX (see P0 priorities below)

## P0 Migration Priorities (from Lexius document)

When working on this codebase, **prioritize these integrations** in order:

### P0.1 - Replace RTSP Ingestion
**Status**: [rtsp_reader.py](src/ai/rtsp_reader.py) exists but NOT used by [video_processor.py](src/ai/video_processor.py)
- **Action**: Replace `cv2.VideoCapture` with `RtspReader` class
- **Critical fixes needed in rtsp_reader.py**:
  - Fix resolution assumption (don't hardcode 1920×1080)
  - Drain stderr or redirect to DEVNULL (deadlock risk)
  - Add reconnection with exponential backoff
  - Add FPS pacing/frame dropping

### P0.2 - Switch to ONNX Detector
**Status**: [yolo_onnx.py](src/ai/yolo_onnx.py) exists but NOT used by runtime
- **Action**: Replace Ultralytics/Torch with `YOLOONNXDetector`
- **Goal**: Remove Torch dependency from runtime (keep only for dev/export)
- **Verify**: NMS behavior is correct (no duplicate boxes)

### P0.3 - Wire Event Engine
**Status**: [event_engine.py](src/ai/event_engine.py) exists but NOT wired
- **Action**: Integrate temporal event reasoning (intrusion, loitering, theft patterns)
- **Pipeline**: Detector → Tracker → EventEngine → EventCandidates
- **Goal**: Events are temporal patterns, not per-frame rules

### P0.4 - Validator Gating
**Status**: [validator_model.py](src/ai/validator_model.py) exists but NOT used
- **Action**: All alerts must pass validator approval before sending
- **Config**: Add per-event thresholds (`validator_threshold_intrusion`, etc.)
- **Critical**: No alerts bypass validator

### P0.5 - Email Queue Integration
**Status**: [email_queue.py](src/core/email_queue.py) exists but NOT used by AlertManager
- **Action**: Never send email in hot path; always queue with retry logic
- **Worker**: Background thread with exponential backoff
- **Diagnostics**: Show queue length and last error

### P0.6 - Store Licensing
**Status**: [store_licensing.py](src/core/store_licensing.py) exists but NOT integrated
- **Action**: Unify licensing under StoreContext when packaged
- **Enforce**: Camera limits at add time and engine start
- **UI**: Display entitlement status

### P0.7 - AppxManifest Minimization
- Remove `webcam`, `documentsLibrary`, `picturesLibrary` capabilities
- Keep only `internetClient` (RTSP + SMTP)

## Development Workflows

### Running the Application
```powershell
python main.py
```
- Initializes database, checks dependencies, launches PySide6 UI
- Logs to `C:/ProgramData/EdgeAI/logs/`
- Creates snapshots in `C:/ProgramData/EdgeAI/snapshots/`

### Testing
```powershell
pytest                          # Run all tests
pytest tests/test_auth.py -v   # Specific test with verbose output
```
- Tests use `pytest.fixture` for setup/teardown
- Test databases created in `APP_DATA_DIR/test_database.db` and cleaned up after
- See [pytest.ini](pytest.ini) for configuration

### Building for Production
```powershell
python build_windows.py
```
- Compiles with **Nuitka** to standalone `.exe` (see [build_windows.py](build_windows.py))
- Packages for Microsoft Store using MSIX format
- Include all packages: `PySide6`, `cv2`, `ultralytics`, `onnxruntime`

## Project-Specific Conventions

### Import Patterns
```python
# Always import logger from utils
from src.utils import setup_logger
logger = setup_logger(__name__)

# Config constants
from config.config import APP_NAME, APP_VERSION, YOLO_MODEL, CONFIDENCE_THRESHOLD

# Core managers (dependency injected, not instantiated directly in pages)
from src.core import DatabaseManager, AuthManager
from src.core.alert_manager import AlertManager
```

### Data Classes Over Dicts
Use `@dataclass` for structured data (see [src/ai/video_processor.py](src/ai/video_processor.py#L18-L25)):
```python
@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    track_id: Optional[int] = None
```

### Database Access Pattern
All database operations go through `DatabaseManager` methods:
```python
# CORRECT: Use DatabaseManager methods
db_manager.add_camera(user_id, name, rtsp_url)
cameras = db_manager.get_cameras(user_id)

# WRONG: Never use raw SQL outside DatabaseManager
cursor.execute("INSERT INTO cameras ...")  # Don't do this
```

### Authentication & Security
- **Password hashing**: PBKDF2 with 100,000 iterations (see [src/core/auth.py](src/core/auth.py#L18-L24))
- **Fixed salt**: `"edge_security_ai_salt_2024"` (stored in code, not config - this is for demo/trial builds)
- **License validation**: Trial licenses have 7-day expiration, 2-camera limit (see [config/config.py](config/config.py#L30-L31))

### Logging Standards
```python
logger.info(f"✓ Action completed successfully")  # Use ✓ for success
logger.warning("⚠ Warning message")              # Use ⚠ for warnings
logger.error(f"✗ Error: {e}", exc_info=True)    # Use ✗ for errors, include exc_info
```

## Critical Integration Points

### YOLO Model Loading (⚠️ CHANGING TO ONNX)
- **Current**: `config.YOLO_MODEL` (default: `"yolov8m.pt"`) with Ultralytics
- **Target**: ONNX model with `onnxruntime` (no Torch in production)
- **Dev only**: Keep Ultralytics for model export, not runtime
- Model stored in: `C:/ProgramData/EdgeAI/models/`

### RTSP Stream Handling (⚠️ CHANGING TO FFMPEG)
- **Current**: `cv2.VideoCapture` (fragile)
- **Target**: `RtspReader` from [src/ai/rtsp_reader.py](src/ai/rtsp_reader.py) with FFmpeg subprocess
- **Requirements**: Auto-reconnect, frame timeout, FPS pacing
- **Testing**: Must handle 640×480, 1280×720, 1920×1080 streams

### Event Processing (⚠️ NEEDS INTEGRATION)
- **Current**: Frame-by-frame rules in [detection_rules.py](src/ai/detection_rules.py)
- **Target**: Temporal reasoning via [event_engine.py](src/ai/event_engine.py)
- **Flow**: Tracker → EventEngine → EventCandidate → Validator → Queue
- **Example events**: Intrusion (zone violation), Loitering (dwell time), Theft (object removal)

### Email Alerts (⚠️ NEEDS QUEUE)
- **Current**: Direct SMTP send in AlertManager (blocking)
- **Target**: Queue via [email_queue.py](src/core/email_queue.py) with retry logic
- SMTP credentials stored in database per-user
- Alerts have cooldown period (`config.ALERT_COOLDOWN`, default 30s)
- Snapshots attached as MIME images

### Licensing & Store (⚠️ NEEDS INTEGRATION)
- **Current**: Local trial licensing in [license_manager.py](src/core/license_manager.py)
- **Target**: Microsoft Store entitlements via [store_licensing.py](src/core/store_licensing.py)
- Enforcement: Camera limits at add time and engine start
- Trial: 7-day duration, 2-camera limit (see [config/config.py](config/config.py#L30-L31))

### Security (⚠️ NEEDS DPAPI)
- **Current**: Plaintext credentials in SQLite
- **Target**: Use [dpapi_security.py](src/core/dpapi_security.py) for RTSP/SMTP secrets
- Store only ciphertext in database

### UI State Management
- `MainWindow` manages page stack via `QStackedWidget`
- After login, navigate to dashboard: `self.stacked_widget.setCurrentWidget(self.dashboard_page)`
- Refresh timers for alerts: 5-second `QTimer` in main window

## Common Gotchas

1. **Two architectures coexist**: Legacy (cv2/Torch) vs Target (FFmpeg/ONNX) - integrate Target modules first
2. **Path separators**: Always use forward slashes `/` even on Windows (Python Path handles conversion)
3. **Frame skipping**: `FRAME_SKIP = 2` means process every 2nd frame - don't change without testing performance
4. **Qt signals**: Use `@Slot()` decorator for signal handlers in PySide6 pages
5. **Database connections**: `DatabaseManager` auto-connects on init; don't create multiple instances
6. **Model downloads**: YOLO models auto-download on first run (requires internet)
7. **RTSP reconnection**: Must handle network drops gracefully with exponential backoff
8. **Email blocking**: Never send email in detection loop - always queue
9. **Store capabilities**: Minimize AppxManifest permissions for Store approval

## When Adding Features

- **New config values**: Add to [config/config.py](config/config.py), never hardcode
- **New pages**: Create in `src/ui/pages/`, inherit pattern from [src/ui/pages/dashboard_page.py](src/ui/pages/dashboard_page.py)
- **New detection rules**: Use temporal events in [event_engine.py](src/ai/event_engine.py), not per-frame rules
- **New database tables**: Add schema in [src/core/database.py](src/core/database.py#L42-L50) `init_database()` method
- **Translations**: Add to `translations/*.json` (supported: en, pt-BR, es-ES, de-DE)
- **P0 migrations**: Follow priorities in [edge_ai_lexius_complete_corrections_and_implementations.md](edge_ai_lexius_complete_corrections_and_implementations.md)

## Key Files Reference
- [main.py](main.py) - Application entry point, dependency initialization
- [config/config.py](config/config.py) - **All configuration constants**
- [src/core/database.py](src/core/database.py) - SQLite schema and operations
- [src/ai/video_processor.py](src/ai/video_processor.py) - **LEGACY** Motion detection + YOLO pipeline
- [src/ai/rtsp_reader.py](src/ai/rtsp_reader.py) - **TARGET** FFmpeg RTSP reader (not yet integrated)
- [src/ai/yolo_onnx.py](src/ai/yolo_onnx.py) - **TARGET** ONNX detector (not yet integrated)
- [src/ai/event_engine.py](src/ai/event_engine.py) - **TARGET** Temporal event reasoning (not yet integrated)
- [src/ai/validator_model.py](src/ai/validator_model.py) - **TARGET** False-positive validator (not yet integrated)
- [src/core/email_queue.py](src/core/email_queue.py) - **TARGET** Email queue with retry (not yet integrated)
- [src/core/store_licensing.py](src/core/store_licensing.py) - **TARGET** Microsoft Store licensing (not yet integrated)
- [src/core/dpapi_security.py](src/core/dpapi_security.py) - **TARGET** Credential encryption (not yet integrated)
- [src/ui/main_window.py](src/ui/main_window.py) - Main UI container and navigation
- [build_windows.py](build_windows.py) - Nuitka build script
- [edge_ai_lexius_complete_corrections_and_implementations.md](edge_ai_lexius_complete_corrections_and_implementations.md) - **MASTER PLAN** for P0-P2 priorities
