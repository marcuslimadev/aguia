"""
Test RTSP URLs for discovered cameras
Tests common RTSP path formats even if port scan didn't find 554
"""
import cv2
import time

# Discovered devices
devices = [
    "192.168.0.20",  # IP_Webcam (ONVIF detected)
    "192.168.0.3",   # Unknown device
]

# Common Intelbras/DVR RTSP paths
rtsp_formats = [
    "rtsp://admin:{password}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
    "rtsp://admin:{password}@{ip}:554/stream1",
    "rtsp://admin:{password}@{ip}:554/onvif1",
    "rtsp://admin:{password}@{ip}:8554/live",
    "rtsp://{ip}:554/h264.sdp",  # IP Webcam Android
    "rtsp://admin:{password}@{ip}:554/cam1/mpeg4",
    "rtsp://admin:{password}@{ip}:554/11",
    "http://{ip}:8080/video",  # IP Webcam Android HTTP
]

# Common passwords for Intelbras
passwords = [
    "admin1292",
    "admin",
    "",
    "12345",
    "547751",  # Last 6 digits of DTR0004547751
]

print("="*70)
print("RTSP URL Tester")
print("="*70)
print(f"Testing {len(devices)} devices with {len(rtsp_formats)} URL formats")
print(f"Passwords: {', '.join(repr(p) if p else '(empty)' for p in passwords)}")
print("="*70 + "\n")

successful = []

for ip in devices:
    print(f"\n📹 Testing {ip}...")
    
    for fmt in rtsp_formats:
        for password in passwords:
            url = fmt.format(ip=ip, password=password)
            
            # Hide password in display
            display_url = fmt.format(ip=ip, password="***")
            print(f"  Trying: {display_url}", end=" ... ")
            
            try:
                cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        print(f"✅ SUCCESS! ({w}x{h})")
                        successful.append({
                            'ip': ip,
                            'url': url,
                            'resolution': f"{w}x{h}"
                        })
                        cap.release()
                        break  # Found working URL for this format
                    else:
                        print("❌ Opened but no frame")
                else:
                    print("❌ Failed to open")
                
                cap.release()
            except Exception as e:
                print(f"❌ Error: {e}")
            
            time.sleep(0.1)  # Small delay between attempts
        
        # If found working URL, try next format
        if any(s['ip'] == ip and fmt.split('?')[0] in s['url'] for s in successful):
            continue

print("\n" + "="*70)
print("Test Results")
print("="*70 + "\n")

if successful:
    print(f"✅ Found {len(successful)} working RTSP URL(s):\n")
    for s in successful:
        print(f"📹 {s['ip']} ({s['resolution']})")
        print(f"   URL: {s['url']}")
        print(f"   Para adicionar no Edge AI:")
        print(f"   1. Vá em: View → Cameras → Tab RTSP Direct")
        print(f"   2. Cole a URL acima")
        print(f"   3. Clique 'Add Camera'")
        print()
else:
    print("❌ Nenhuma URL RTSP funcionou")
    print("\nPróximos passos:")
    print("  1. Acesse interface web dos dispositivos:")
    print("     • http://192.168.0.20:8080 (IP_Webcam)")
    print("     • http://192.168.0.3:8080")
    print("  2. Procure nas configurações:")
    print("     • RTSP settings / Enable RTSP")
    print("     • Stream URL / Path")
    print("     • Network / Port settings")
    print("  3. Se for DVR Intelbras, verifique no menu:")
    print("     • Menu → Network → TCP/IP")
    print("     • Menu → Network → Connection")

print("="*70)
