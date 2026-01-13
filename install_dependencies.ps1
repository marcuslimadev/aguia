# Install ALL dependencies for Edge AI - Complete Setup
# Run this script after closing the application

Write-Host "=== Edge AI Complete Installation ===" -ForegroundColor Cyan
Write-Host ""

# Core dependencies
Write-Host "Installing Core Dependencies..." -ForegroundColor Green
pip install PySide6 opencv-python numpy pillow psutil

# YOLO and AI
Write-Host "`nInstalling YOLO (Ultralytics)..." -ForegroundColor Green
pip install ultralytics torch torchvision

# ONNX Runtime for optimized inference
Write-Host "`nInstalling ONNX Runtime..." -ForegroundColor Green
pip install onnxruntime

# MediaPipe for pose detection (specific version with solutions API)
Write-Host "`nInstalling MediaPipe 0.10.9..." -ForegroundColor Green
pip uninstall mediapipe -y
pip install mediapipe==0.10.9

# ByteTrack for advanced object tracking
Write-Host "`nInstalling ByteTrack dependencies..." -ForegroundColor Green
pip install lap cython-bbox

# Email and networking
Write-Host "`nInstalling Email/Network dependencies..." -ForegroundColor Green
pip install requests

# Database
Write-Host "`nSQLite is built-in to Python" -ForegroundColor Gray

Write-Host "`n=== Installation Complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Export YOLO model to ONNX:" -ForegroundColor White
Write-Host "   python -c ""from ultralytics import YOLO; YOLO('yolov8m.pt').export(format='onnx')""" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Move the .onnx file to:" -ForegroundColor White
Write-Host "   C:\Users\$env:USERNAME\AppData\Local\EdgeAI\models\yolov8m.onnx" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Run the application:" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor Gray
Write-Host ""

