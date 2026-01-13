"""
Test Intelbras Cloud/P2P integration
"""
import logging
from src.ai.onvif_discovery import discover_intelbras_p2p, discover_onvif_cameras

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_intelbras():
    """Test Intelbras connection"""
    device_id = "DTR0004547751"
    password = "admin1292"
    
    print("=" * 60)
    print("Testing Intelbras Cloud/P2P Integration")
    print("=" * 60)
    print(f"Device ID: {device_id}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    # Test P2P connection
    print("1. Attempting P2P connection...")
    rtsp_url = discover_intelbras_p2p(device_id, password)
    
    if rtsp_url:
        print(f"✓ SUCCESS! RTSP URL: {rtsp_url}")
    else:
        print("✗ P2P connection failed")
    
    print()
    print("2. Attempting ONVIF discovery...")
    cameras = discover_onvif_cameras(timeout=15)
    
    if cameras:
        print(f"✓ Found {len(cameras)} ONVIF cameras:")
        for cam in cameras:
            print(f"  • {cam['name']} at {cam['ip']}")
            if cam.get('serial'):
                print(f"    Serial: {cam['serial']}")
    else:
        print("✗ No ONVIF cameras found")
    
    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_intelbras()
