"""
Multi-Port Camera/DVR Scanner
Scans for common camera ports: RTSP, HTTP, ONVIF
"""
import socket
import threading
import subprocess

# Auto-detect local subnet
def get_local_subnet():
    """Detecta a subnet local automaticamente"""
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp850')
        lines = result.stdout.split('\n')
        
        for i, line in enumerate(lines):
            if 'IPv4' in line or 'Endereço IPv4' in line:
                ip = line.split(':')[-1].strip()
                if ip.startswith('192.168'):
                    parts = ip.split('.')
                    subnet = f"{parts[0]}.{parts[1]}.{parts[2]}."
                    print(f"[INFO] Seu IP local: {ip}")
                    print(f"[INFO] Subnet: {subnet}0/24")
                    return subnet, ip
    except Exception as e:
        print(f"[WARN] Erro ao detectar subnet: {e}")
    
    return "192.168.0.", "192.168.0.21"

# Common camera/DVR ports
PORTS = {
    554: "RTSP",
    8554: "RTSP Alt",
    80: "HTTP/Web",
    8080: "HTTP Alt",
    8000: "HTTP Intelbras",
    37777: "Dahua/Intelbras TCP",
    34567: "Hikvision",
    3702: "ONVIF Discovery",
    8899: "ONVIF",
}

subnet, my_ip = get_local_subnet()
timeout = 0.3
found = {}
found_lock = threading.Lock()

def scan(ip, port, service):
    """Scan single IP:port"""
    # Skip scanning our own IP
    if ip == my_ip:
        return
        
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        
        with found_lock:
            if ip not in found:
                found[ip] = []
            found[ip].append((port, service))
            print(f"✓ {ip}:{port} ({service})")
    except:
        pass

# Start scanning
print("\n" + "="*70)
print("Multi-Port Camera/DVR Scanner")
print("="*70)
print(f"Scanning {subnet}1-254")
print(f"Ports: {', '.join(str(p) for p in PORTS.keys())}")
print(f"Timeout: {timeout}s per host")
print("="*70 + "\n")

threads = []

# Scan all IPs and ports
for i in range(1, 255):
    ip = subnet + str(i)
    for port, service in PORTS.items():
        t = threading.Thread(target=scan, args=(ip, port, service))
        threads.append(t)
        t.start()
        
        # Limit concurrent threads
        if len(threads) >= 100:
            for t in threads[:50]:
                t.join()
            threads = threads[50:]

# Wait for remaining threads
for t in threads:
    t.join()

# Results
print("\n" + "="*70)
print(f"Scan completo! {len(found)} dispositivo(s) encontrado(s)")
print("="*70 + "\n")

if found:
    for ip in sorted(found.keys()):
        ports = found[ip]
        print(f"📹 Dispositivo: {ip}")
        print(f"   Portas abertas:")
        
        has_rtsp = False
        has_http = False
        
        for port, service in sorted(ports):
            print(f"     • {port} ({service})")
            if "RTSP" in service:
                has_rtsp = True
            if "HTTP" in service:
                has_http = True
        
        # Suggest URLs
        print(f"   URLs sugeridas:")
        
        if has_rtsp:
            print(f"     RTSP: rtsp://admin:admin1292@{ip}:554/cam/realmonitor?channel=1&subtype=0")
        
        if has_http:
            http_port = next((p for p, s in ports if "HTTP" in s and "Alt" not in s), 80)
            print(f"     Web:  http://{ip}:{http_port}")
        
        # Intelbras specific
        if 37777 in [p for p, _ in ports] or 8000 in [p for p, _ in ports]:
            print(f"     🎯 PROVÁVEL INTELBRAS!")
            print(f"        • Tente login web: http://{ip}:8000")
            print(f"        • Senha padrão: admin / (vazio) ou últimos 6 dígitos do serial")
        
        print()
else:
    print("⚠ Nenhum dispositivo encontrado")
    print("\nDicas:")
    print("  1. Certifique-se que DVR/Câmera está ligado")
    print("  2. Verifique se está na mesma rede (sem VLANs)")
    print("  3. Desabilite firewall temporariamente para teste")
    print("  4. Verifique IP diretamente no menu do DVR")

print("="*70)
