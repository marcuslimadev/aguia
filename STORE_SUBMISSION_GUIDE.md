# Microsoft Store Submission Guide

## 🚀 Guia Completo de Publicação na Microsoft Store

Este guia detalha todos os passos para publicar **Edge Property Security AI** na Microsoft Store.

---

## 📋 Checklist Pré-Submissão

### ✅ Código & Build
- [x] **ONNX Runtime**: requirements.txt tem onnxruntime, NÃO torch/ultralytics
- [x] **Torch em Dev apenas**: requirements-dev.txt tem torch/ultralytics (para export)
- [x] **Build size**: < 1GB (target: 500MB com ONNX)
- [x] **Capabilities mínimas**: AppxManifest.xml tem APENAS `internetClient`
- [x] **Todos os testes passam**: `pytest -v` sem erros
- [x] **Performance targets**: >20 FPS @ 1080p, <500MB RAM
- [x] **DPAPI Security**: Credenciais criptografadas com DPAPI
- [x] **Store Licensing**: StoreContext integration implementado

### ✅ Assets Necessários
- [ ] **Icon 44×44**: assets/icon_44x44.png (Square44x44Logo)
- [ ] **Tile 150×150**: assets/tile_150x150.png (Square150x150Logo)
- [ ] **Logo**: assets/logo.png (Package logo)
- [ ] **Splash Screen**: assets/splash.png (1024×768 ou maior)
- [ ] **Screenshots**: 1280×720 ou 1920×1080 (mínimo 1, máximo 9)
- [ ] **App Icon .ico**: assets/icon.ico (para Windows executable)

### ✅ Documentação
- [x] **README.md**: Overview, features, installation
- [x] **LICENSE**: Licença do software
- [x] **Privacy Policy**: URL pública (obrigatório para Store)
- [x] **Deployment Checklist**: DEPLOYMENT_CHECKLIST.md
- [x] **Store Guide**: MICROSOFT_STORE_GUIDE.md
- [ ] **Support URL**: Website ou página de suporte

---

## 🛠️ Passo 1: Preparar Build de Produção

### 1.1 Verificar Requirements
```powershell
# requirements.txt deve ter APENAS:
cat requirements.txt | Select-String "torch|ultralytics"
# Resultado esperado: NENHUM (vazio)

# requirements-dev.txt PODE ter torch/ultralytics (apenas para dev)
cat requirements-dev.txt | Select-String "torch|ultralytics"
# Resultado esperado: torch>=2.0.0, ultralytics>=8.0.0
```

### 1.2 Executar Build
```powershell
# Build completo: executável + MSIX
python build_windows.py --full
```

**Output esperado**:
```
✓ Compilação concluída com sucesso!
Tamanho: 500-800 MB

✓ MSIX criado com sucesso!
  EdgePropertySecurityAI.msix
  Tamanho: 500-800 MB
```

⚠️ Se build > 1GB, verifique se Torch foi excluído corretamente!

### 1.3 Testar Build Local
```powershell
# Testar executável standalone
cd build\EdgePropertySecurityAI.dist
.\EdgePropertySecurityAI.exe

# Verificar:
# - Abre UI sem erros
# - Login funciona
# - Pode adicionar câmera (mock RTSP)
# - ONNX model carrega (não Torch!)
```

---

## 📦 Passo 2: Criar Certificado de Assinatura (DEV)

Para testes locais, crie certificado auto-assinado:

```powershell
# Criar certificado (válido por 1 ano)
New-SelfSignedCertificate `
    -Type Custom `
    -Subject "CN=Edge Security, O=Edge Security, C=US" `
    -KeyUsage DigitalSignature `
    -FriendlyName "Edge Security Dev Certificate" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")

# Exportar certificado
$cert = Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object {$_.Subject -like "*Edge Security*"} | Select-Object -First 1
Export-Certificate -Cert $cert -FilePath EdgeSecurity.cer

# Converter para PFX (password: "dev123")
$password = ConvertTo-SecureString -String "dev123" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath EdgeSecurity.pfx -Password $password
```

---

## 🔐 Passo 3: Assinar MSIX (DEV)

```powershell
# Assinar MSIX com certificado dev
signtool sign /fd SHA256 /a /f EdgeSecurity.pfx /p dev123 EdgePropertySecurityAI.msix

# Verificar assinatura
signtool verify /pa EdgePropertySecurityAI.msix
```

**Output esperado**: `Successfully verified`

---

## 🧪 Passo 4: Testar MSIX Localmente

### 4.1 Instalar Certificado
```powershell
# Instalar certificado na Trusted Root
Import-Certificate -FilePath EdgeSecurity.cer -CertStoreLocation Cert:\LocalMachine\Root
```

### 4.2 Instalar MSIX
```powershell
# Via PowerShell
Add-AppxPackage -Path EdgePropertySecurityAI.msix

# OU: Duplo clique no arquivo MSIX
# Windows irá perguntar se deseja instalar
```

### 4.3 Verificar Instalação
```powershell
# Listar apps instalados
Get-AppxPackage | Where-Object {$_.Name -like "*EdgeProperty*"}

# Resultado esperado:
# Name              : EdgePropertySecurityAI
# Publisher         : CN=Edge Security
# Version           : 1.0.0.0
# InstallLocation   : C:\Program Files\WindowsApps\...
```

### 4.4 Executar App
- Abrir menu Iniciar
- Buscar "Edge Property Security AI"
- Executar e verificar funcionalidade completa

---

## 🏢 Passo 5: Registrar no Partner Center

### 5.1 Criar Conta de Desenvolvedor
1. Acessar: https://partner.microsoft.com/dashboard
2. Criar conta de desenvolvedor ($19 individual ou $99 empresa)
3. Verificar identidade (pode levar 24-48h)

### 5.2 Reservar Nome do App
1. Partner Center → Apps and games → New product
2. Tipo: MSIX or PWA app
3. Nome: **Edge Property Security AI**
4. Verificar disponibilidade
5. Reservar nome (válido por 1 ano)

---

## 📝 Passo 6: Preencher Store Listing

### 6.1 Product Description (Inglês)

**Título**: Edge Property Security AI

**Short Description** (máximo 500 caracteres):
```
AI-powered property security monitoring with real-time RTSP video analysis, YOLOv8 object detection, and intelligent event alerts. Monitor multiple IP cameras, detect intrusions, loitering, and theft patterns. Email notifications with snapshots. Microsoft Store exclusive.
```

**Full Description** (máximo 10.000 caracteres):
```
Transform your property security with AI-powered video monitoring.

FEATURES:
• Real-time RTSP Stream Processing
• YOLOv8 Object Detection (ONNX optimized)
• Multi-Camera Support (up to 50 cameras)
• Intelligent Event Detection:
  - Intrusion Detection
  - Loitering Alerts
  - Theft Pattern Recognition
  - Crowd Anomaly Detection
• Email Alerts with Snapshots
• False Positive Filtering (AI Validator)
• Secure Credential Storage (Windows DPAPI)
• System Diagnostics & Monitoring
• Multi-language Support (English, Portuguese, Spanish, German)

PERFORMANCE:
• 20-30 FPS @ 1080p
• <500MB memory per camera
• Local processing (no cloud uploads)
• ONNX Runtime for efficient inference

LICENSING:
• Free Tier: 2 cameras
• Tier 1: 5 cameras
• Tier 2: 10 cameras
• Tier 3: 50 cameras

PRIVACY:
All video processing is done locally on your PC. No data is sent to external servers except email alerts you configure. Credentials are encrypted using Windows DPAPI.

REQUIREMENTS:
• Windows 10 version 1809 or later
• Intel Core i5 or equivalent
• 8GB RAM minimum (16GB recommended)
• Internet connection for RTSP cameras and email alerts

SUPPORT:
Visit our documentation for setup guides, troubleshooting, and FAQs.
```

**Keywords** (máximo 7):
```
security, ai, camera, surveillance, yolo, rtsp, monitoring
```

---

### 6.2 Screenshots

Necessário pelo menos **1 screenshot**, recomendado **3-5**:

1. **Dashboard Screenshot**: Mostrando câmeras ativas, estatísticas
2. **Cameras Page**: Gerenciamento de câmeras
3. **Alerts History**: Histórico de alertas com snapshots
4. **Diagnostics Page**: Observabilidade e métricas
5. **Detection Example**: Frame com detecções marcadas

**Resolução**: 1280×720 ou 1920×1080  
**Formato**: PNG ou JPG  
**Máximo**: 2MB por imagem

---

### 6.3 Privacy Policy (Obrigatório!)

Criar página pública com privacy policy. Exemplo:

**URL**: https://edgesecurity.com/privacy (substitua pelo seu)

**Conteúdo mínimo**:
```markdown
# Privacy Policy - Edge Property Security AI

Last updated: [Date]

## Data Collection
This app does NOT collect or transmit any personal data to external servers.

## Video Processing
All video processing is performed locally on your device. Video streams are accessed via RTSP protocol from your IP cameras and are not uploaded to any cloud service.

## Email Alerts
If you configure email alerts, the app sends emails using the SMTP server you provide. Email credentials are encrypted using Windows DPAPI and stored locally.

## Credentials Storage
RTSP and SMTP credentials are encrypted using Windows Data Protection API (DPAPI) and stored in a local SQLite database on your device.

## Third-Party Services
The app does not use any third-party analytics, tracking, or advertising services.

## Contact
For questions about this privacy policy, contact: support@edgesecurity.com
```

---

### 6.4 Support Contact

Fornecer pelo menos **1 método de suporte**:
- Email: support@edgesecurity.com
- Website: https://edgesecurity.com/support
- GitHub Issues: https://github.com/yourusername/edge-ai/issues

---

## 🎯 Passo 7: Submission Package

### 7.1 Preparar MSIX Final

⚠️ **Para Store, use certificado EV do Partner Center**

```powershell
# Build final
python build_windows.py --full

# Assinar com certificado Store (fornecido pelo Partner Center)
# Ou: Upload MSIX sem assinatura e Store assina automaticamente
```

### 7.2 Validar MSIX

Use **Windows App Certification Kit (WACK)**:

```powershell
# Instalar Windows SDK se não tiver
# https://developer.microsoft.com/windows/downloads/windows-sdk/

# Executar WACK
"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\appcert.exe" EdgePropertySecurityAI.msix
```

**Deve passar todos os testes**:
- Package compliance
- App launch tests
- Capability usage
- Security tests
- Performance tests

---

## 📤 Passo 8: Upload para Store

### 8.1 Partner Center Upload

1. Partner Center → Your app → Start submission
2. Pricing and availability:
   - Base price: Free (com in-app purchases para tiers)
   - Markets: Select all ou specific countries
   - Visibility: Public

3. Properties:
   - Category: Security
   - Subcategory: Monitoring
   - Age rating: Everyone

4. Packages:
   - Upload: EdgePropertySecurityAI.msix
   - Wait for validation (5-10 min)

5. Store listings:
   - Language: English (US) - preencher todos campos
   - Language: Portuguese (Brazil) - optional
   - Upload screenshots (1-9)

6. Notes for certification (importante!):
```
This app processes RTSP video streams from IP cameras locally on the user's device.

TESTING INSTRUCTIONS:
1. Login with test account: testuser / testpass123
2. Use mock RTSP URL for testing: rtsp://test:test@example.com/stream
3. All features work without real cameras (mock mode available)

SPECIAL PERMISSIONS:
- internetClient: Required for RTSP camera access and SMTP email alerts
- Full-trust application: Required for local file access (ProgramData) and DPAPI encryption

VIDEO PROCESSING:
All video processing is local. No data is uploaded to external servers.
```

7. Review and submit

---

## ⏱️ Passo 9: Aguardar Certificação

### Timeline típico:
- **Validation**: 1-2 horas (automated)
- **Certification**: 1-3 dias úteis (manual review)
- **Publishing**: 1-24 horas após aprovação

### Status possíveis:
- ✅ **Published**: App está na Store!
- ⏳ **In certification**: Review em andamento
- ❌ **Failed**: Problemas encontrados (ver feedback)

### Se falhar:
1. Ler relatório de certificação no Partner Center
2. Corrigir problemas
3. Resubmit (sem custo adicional)

---

## 🎉 Passo 10: Pós-Publicação

### 10.1 Verificar Store Page
```
https://www.microsoft.com/store/apps/EdgePropertySecurityAI
```

### 10.2 Monitoring
- Partner Center → Analytics: Downloads, crashes, ratings
- Email de usuários: Responder reviews e feedback
- Updates: Versões novas a cada 2-4 semanas

### 10.3 Updates
Para publicar atualização:
1. Incrementar version em AppxManifest.xml (1.0.0.0 → 1.1.0.0)
2. Build + assinar novo MSIX
3. Partner Center → Update submission
4. Upload novo MSIX
5. Submit (passa por certificação novamente)

---

## 🚨 Problemas Comuns

### Build > 1GB
**Causa**: Torch/Ultralytics incluído no build  
**Solução**: Remover de requirements.txt, usar apenas ONNX

### Capabilities rejeitadas
**Causa**: webcam, documentsLibrary desnecessários  
**Solução**: Remover de AppxManifest.xml, deixar só internetClient

### App não inicia na Store
**Causa**: Falta dependencies (VC++ Redistributable)  
**Solução**: Incluir VC++ no MSIX ou usar Nuitka standalone

### Falha no WACK
**Causa**: High CPU/memory durante tests  
**Solução**: Otimizar performance, adicionar sleep em init

---

## ✅ Checklist Final

Antes de submeter, verificar:

- [x] Build < 1GB
- [x] WACK passes (Windows App Certification Kit)
- [x] AppxManifest.xml minimizado (só internetClient)
- [x] Screenshots (mínimo 1, recomendado 3-5)
- [x] Privacy Policy URL pública
- [x] Support contact (email ou website)
- [x] Description em inglês preenchida
- [x] Keywords relevantes (máximo 7)
- [x] Pricing definido (Free + in-app)
- [x] Testing instructions para certification team
- [x] Todos os testes passam (pytest -v)
- [x] Performance targets atingidos (>20 FPS, <500MB)

---

## 📞 Suporte

**Problemas com build?**
- Ver: DEPLOYMENT_CHECKLIST.md
- Ver: MICROSOFT_STORE_GUIDE.md

**Problemas com Store?**
- Partner Center support: https://partner.microsoft.com/support
- Store certification docs: https://docs.microsoft.com/windows/uwp/publish/

**Problemas técnicos?**
- GitHub Issues: https://github.com/yourusername/edge-ai/issues
- Email: support@edgesecurity.com

---

**Boa sorte com a submissão! 🚀**
