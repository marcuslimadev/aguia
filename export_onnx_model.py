# Export YOLO model to ONNX format for optimized inference
# This creates the .onnx file needed by the application

from ultralytics import YOLO
import os
import shutil
from pathlib import Path

print("=== YOLO ONNX Export ===\n")

# Download/load YOLOv8m model
print("Loading YOLOv8m model...")
model = YOLO('yolov8m.pt')

# Export to ONNX
print("\nExporting to ONNX format...")
model.export(format='onnx', imgsz=640)

# Move to application models directory
onnx_file = "yolov8m.onnx"
app_data_dir = Path(os.environ['LOCALAPPDATA']) / 'EdgeAI' / 'models'
app_data_dir.mkdir(parents=True, exist_ok=True)

destination = app_data_dir / onnx_file

if os.path.exists(onnx_file):
    print(f"\nMoving {onnx_file} to {destination}...")
    shutil.copy(onnx_file, destination)
    print(f"✓ Model exported successfully to: {destination}")
else:
    print(f"✗ Error: {onnx_file} not found after export")

print("\nDone! You can now run the application with ONNX inference.")
