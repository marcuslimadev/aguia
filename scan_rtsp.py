"""
RTSP Camera/DVR Scanner
Scans local network for RTSP services on port 554
"""
import socket
import threading
import subprocess

# Auto-detect local subnet
def get_local_subnet():
    """Detecta a subnet local automaticamente"""
    try:
        # Get ipconfig output
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp850')
        lines = result.stdout.split('\n')
        
        # Find IPv4 address
        for i, line in enumerate(lines):
            if 'IPv4' in line or 'Endereço IPv4' in line:
                # Extract IP (format: "   Endereço IPv4. . . . . . . . . . : 192.168.0.10")
                ip = line.split(':')[-1].strip()
                if ip.startswith('192.168'):
                    # Extract subnet (e.g., 192.168.0.)
                    parts = ip.split('.')
                    subnet = f"{parts[0]}.{parts[1]}.{parts[2]}."
                    print(f"[INFO] Seu IP local: {ip}")
                    print(f"[INFO] Subnet detectada: {subnet}0/24")
                    return subnet
    except Exception as e:
        print(f"[WARN] Erro ao detectar subnet: {e}")
    
    # Default fallback
    print("[INFO] Usando subnet padrão: 192.168.0.0/24")
    return "192.168.0."

# Configuration
subnet = get_local_subnet()
port = 554  # RTSP standard port
timeout = 0.5  # Socket timeout in seconds
found = []
found_lock = threading.Lock()

def scan(ip):
    """Scan single IP for RTSP port"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        s.close()
        
        with found_lock:
            print(f"✓ [RTSP] {ip}:{port} ABERTO")
            found.append(ip)
    except:
        pass

# Start scanning
print("\n" + "="*60)
print("RTSP Camera/DVR Scanner")
print("="*60)
print(f"Scanning {subnet}1-254 on port {port}...")
print(f"Timeout: {timeout}s per host")
print("="*60 + "\n")

threads = []

# Scan range 1-254
for i in range(1, 255):
    ip = subnet + str(i)
    t = threading.Thread(target=scan, args=(ip,))
    threads.append(t)
    t.start()

# Wait for all threads
for t in threads:
    t.join()

# Results
print("\n" + "="*60)
print(f"Scan completo! {len(found)} dispositivo(s) RTSP encontrado(s)")
print("="*60)

if found:
    print("\nDispositivos RTSP encontrados:")
    for ip in found:
        print(f"  • {ip}:554")
        print(f"    URL: rtsp://admin:senha@{ip}:554/cam/realmonitor?channel=1&subtype=0")
        print(f"    (Para Intelbras, tente: admin1292 ou últimos 6 dígitos do serial)")
        print()
    
    print("\nPara testar no VLC:")
    print("1. Abra VLC Media Player")
    print("2. Media → Open Network Stream (Ctrl+N)")
    print("3. Cole a URL RTSP acima")
    print("4. Ajuste a senha conforme necessário")
else:
    print("\n⚠ Nenhum dispositivo RTSP encontrado na rede")
    print("\nPossíveis causas:")
    print("  • DVR/Câmera está offline")
    print("  • Firewall bloqueando porta 554")
    print("  • Dispositivo em subnet diferente")
    print("  • RTSP desabilitado no dispositivo")

print("\n" + "="*60)
