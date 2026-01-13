# Edge Property Security AI

Professional property security software with AI-powered video analysis for Windows.

## Overview

**Edge Property Security AI** is a Windows-based application that performs real-time local video analysis using artificial intelligence to protect physical assets. The application processes video locally without sending any data to external servers, ensuring maximum privacy and security.

### Key Features

- **Real-time Video Analysis**: Process RTSP video streams with AI-powered detection
- **Local Processing**: All video analysis happens on the user's machine - no cloud uploads
- **Security Events Detection**:
  - Intrusion detection
  - Theft pattern recognition
  - Loitering detection
  - Restricted area access
  - Crowd anomalies
  - Fire and smoke detection
  - Vandalism detection

- **Email Alerts**: Instant notifications with snapshots when security events occur
- **Multi-Camera Support**: Manage multiple cameras with flexible licensing
- **Zone Management**: Define custom zones for specific security rules
- **Trial License**: 7-day trial with 2 cameras included

## System Requirements

- **OS**: Windows 10 or later (64-bit)
- **RAM**: 8GB minimum (16GB recommended)
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster processing)
- **Storage**: 2GB free space for application and models
- **Network**: Internet connection for email alerts

## Installation

### From Microsoft Store

1. Search for "Edge Property Security AI" in Microsoft Store
2. Click "Install"
3. Launch the application

### From Source (Development)

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Getting Started

### 1. Register/Login

- Create a new account or login with existing credentials
- Trial license is automatically activated for new users

### 2. Add Cameras

- Navigate to "Cameras" tab
- Enter camera name and RTSP URL
- Click "Add Camera"

### 3. Configure Zones

- Go to "Zones" tab
- Define security zones within camera views
- Set detection rules for each zone

### 4. Setup Email Alerts

- Go to "Settings"
- Enter SMTP server details
- Configure recipient email addresses
- Save settings

### 5. Monitor Alerts

- View real-time alerts in "Alerts" tab
- Acknowledge alerts to mark them as reviewed
- Check alert history

## Architecture

### Components

- **Video Processor**: Handles RTSP stream capture and frame processing
- **Motion Detector**: Detects movement to optimize processing
- **YOLO Detector**: AI-powered object detection using YOLOv8
- **Object Tracker**: Tracks objects across frames using ByteTrack
- **Alert Manager**: Manages security rules and alert generation
- **Database**: SQLite for local data storage
- **Email Notifier**: Sends alerts via SMTP

### Technology Stack

- **UI Framework**: PySide6 (Qt for Python)
- **Video Processing**: OpenCV
- **AI/ML**: YOLOv8, ONNX Runtime
- **Object Tracking**: ByteTrack
- **Database**: SQLite
- **Compilation**: Nuitka
- **Packaging**: MSIX

## Configuration

### Default Settings

- **Storage Location**: `C:/ProgramData/EdgeAI`
- **Database**: SQLite at `C:/ProgramData/EdgeAI/database.db`
- **Models**: Stored in `C:/ProgramData/EdgeAI/models`
- **Snapshots**: Saved in `C:/ProgramData/EdgeAI/snapshots`
- **Logs**: Written to `C:/ProgramData/EdgeAI/logs`

### Performance Tuning

Edit `config/config.py`:

```python
# Frame processing
FRAME_SKIP = 2  # Process every 2nd frame
TARGET_FPS = 15  # Target frames per second

# Detection
CONFIDENCE_THRESHOLD = 0.5  # YOLO confidence threshold
IOU_THRESHOLD = 0.45  # Non-maximum suppression threshold

# Alerts
ALERT_COOLDOWN = 30  # Seconds between alerts of same type
```

## Building for Release

### Compile to Executable

```bash
python build_windows.py
```

This creates a standalone executable using Nuitka.

### Create MSIX Package

```bash
python build_windows.py --msix
```

Requires Windows App Packaging Project or MakeAppx.exe.

## Licensing

### Trial License

- **Duration**: 7 days
- **Cameras**: 2 maximum
- **Automatic**: Activated on first login

### Commercial Licenses

Available through Microsoft Store:
- Cameras × Duration (months) packages
- Automatic renewal options
- Volume licensing available

## Security & Privacy

- **Local Processing**: No video data leaves your premises
- **DRM Protection**: Microsoft Store DRM prevents unauthorized use
- **Signed Binaries**: Application is cryptographically signed
- **Integrity Checks**: Validates application integrity on startup
- **Encrypted Storage**: Sensitive data encrypted in local database

## Troubleshooting

### Camera Connection Issues

1. Verify RTSP URL is correct
2. Check network connectivity
3. Ensure camera is accessible from the network
4. Review logs in `C:/ProgramData/EdgeAI/logs`

### Performance Issues

1. Reduce frame rate in settings
2. Disable unnecessary detection types
3. Upgrade system RAM
4. Use GPU acceleration if available

### Email Alert Issues

1. Verify SMTP server settings
2. Check sender email credentials
3. Ensure recipient emails are valid
4. Review logs for SMTP errors

## Support

For issues, feature requests, or feedback:
- Visit: https://help.manus.im
- Email: support@edgesecurity.ai

## Development

### Project Structure

```
edge_property_security_ai/
├── config/              # Configuration files
├── src/
│   ├── ui/             # User interface (PySide6)
│   ├── core/           # Core functionality
│   ├── ai/             # AI and video processing
│   └── utils/          # Utility functions
├── data/               # Data files and models
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
└── build_windows.py    # Build script
```

### Running Tests

```bash
pytest tests/
```

### Code Style

Follow PEP 8 guidelines. Format code with:

```bash
black src/
```

## Roadmap

### Phase 1: Property Security MVP (Current)
- ✓ Multi-camera support
- ✓ Basic object detection
- ✓ Email alerts
- ✓ Zone management

### Phase 2: Advanced Tracking
- Advanced object tracking
- Behavior pattern analysis
- Custom detection models
- API integration

### Phase 3: Behavior Detection
- Crowd behavior analysis
- Anomaly detection
- Predictive alerts
- Machine learning optimization

## License

Copyright © 2024 Edge Security. All rights reserved.

This software is licensed through Microsoft Store. See license terms in-app.

## Changelog

### Version 1.0.0 (Initial Release)

- Multi-camera support
- YOLOv8 object detection
- Email alerts with snapshots
- Zone-based rules
- Trial licensing
- Windows 10+ support

---

**Edge Property Security AI** - Protecting Your Property with AI
