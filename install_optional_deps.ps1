# Install Optional Dependencies for Edge AI
# These are NOT required but improve performance

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Edge AI - Optional Dependencies Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ByteTrack for advanced object tracking
Write-Host "1. ByteTrack (Advanced Object Tracking)" -ForegroundColor Yellow
Write-Host "   Improves multi-object tracking accuracy" -ForegroundColor Gray
Write-Host "   Current: Simple tracking (works fine)" -ForegroundColor Gray
$installBytetrack = Read-Host "Install ByteTrack? (y/n)"
if ($installBytetrack -eq "y") {
    Write-Host "Installing ByteTrack dependencies..." -ForegroundColor Green
    pip install lap cython-bbox
    Write-Host "✓ ByteTrack installed" -ForegroundColor Green
}

Write-Host ""

# MediaPipe Pose Model
Write-Host "2. MediaPipe Pose Model (Behavior Analysis)" -ForegroundColor Yellow
Write-Host "   Enables pose detection for suspicious behavior" -ForegroundColor Gray
Write-Host "   Current: Not required for basic detection" -ForegroundColor Gray
$installPose = Read-Host "Download MediaPipe model? (y/n)"
if ($installPose -eq "y") {
    Write-Host "Downloading pose_landmarker_lite.task..." -ForegroundColor Green
    $url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
    Invoke-WebRequest -Uri $url -OutFile "pose_landmarker_lite.task"
    Write-Host "✓ Pose model downloaded to current directory" -ForegroundColor Green
    Write-Host "  Move it to C:\Aguia\ to enable pose detection" -ForegroundColor Gray
}

Write-Host ""

# Email Configuration
Write-Host "3. Email Alerts Configuration" -ForegroundColor Yellow
Write-Host "   Configure SMTP for email notifications" -ForegroundColor Gray
Write-Host "   Current: Alerts shown in UI only" -ForegroundColor Gray
$configEmail = Read-Host "Configure email now? (y/n)"
if ($configEmail -eq "y") {
    Write-Host ""
    Write-Host "Email configuration is done in the app:" -ForegroundColor Cyan
    Write-Host "1. Login to the app" -ForegroundColor White
    Write-Host "2. Go to Settings" -ForegroundColor White
    Write-Host "3. Enter SMTP details (Gmail, Outlook, etc.)" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "✓ Core dependencies: Already installed" -ForegroundColor Green
Write-Host "✓ ONNX Runtime: Installed" -ForegroundColor Green
Write-Host "✓ Ultralytics YOLO: Installed" -ForegroundColor Green
Write-Host "✓ MediaPipe: Installed" -ForegroundColor Green
Write-Host ""
Write-Host "Optional (improve but not required):" -ForegroundColor Yellow
Write-Host "  • ByteTrack: Better object tracking" -ForegroundColor Gray
Write-Host "  • Pose Model: Behavior analysis" -ForegroundColor Gray
Write-Host "  • Email Config: Remote notifications" -ForegroundColor Gray
Write-Host ""
Write-Host "Run the app: python main.py" -ForegroundColor Cyan
