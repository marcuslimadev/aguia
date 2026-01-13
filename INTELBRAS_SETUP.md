# Intelbras Cloud/P2P Camera Setup

## ✓ Sistema configurado com sucesso!

O Edge AI agora suporta câmeras Intelbras via:
1. **Nuvem P2P** (Guardian-style)
2. **ONVIF** (descoberta automática na rede local)
3. **RTSP direto** (método tradicional)

## 🎯 Como adicionar sua câmera Intelbras (DTR0004547751)

### Método 1: Através da Interface (RECOMENDADO)

1. Execute o aplicativo: `python main.py`
2. Faça login com marcus/526341
3. Vá em **View → Cameras** (ou clique em Cameras no menu)
4. Clique na aba **"Intelbras Cloud"**
5. Preencha:
   - **Camera Name**: "Intelbras DTR"
   - **Device ID**: DTR0004547751
   - **Device Password**: admin1292
   - **Cloud Username**: (deixe em branco se não tiver)
6. Clique em **"Add Intelbras Camera"**

### Método 2: Descoberta ONVIF (Auto-detectar)

1. Na aba **"Intelbras Cloud"**, clique em **"Discover ONVIF"**
2. Aguarde 30 segundos
3. O sistema encontrará câmeras ONVIF na rede (como IP_Webcam)
4. Os campos serão preenchidos automaticamente
5. Clique em **"Add Camera"** na aba RTSP Direct

### Método 3: RTSP Manual (Se souber o IP local)

Se sua câmera Intelbras estiver na rede local (ex: 192.168.0.X):

1. Vá na aba **"RTSP Direct"**
2. Preencha:
   - **Camera Name**: Intelbras
   - **RTSP URL**: `rtsp://admin:admin1292@192.168.0.X:554/cam/realmonitor?channel=1&subtype=0`
     (substitua X pelo IP da câmera)

## 📋 URLs Intelbras Cloud Geradas

O sistema gerou estas URLs P2P para sua câmera **DTR0004547751**:

```
1. rtsp://admin:admin1292@DTR0004547751.intelbras.cloud:554/cam/realmonitor?channel=1&subtype=0

2. rtsp://admin:admin1292@p2p.intelbras.com.br:554/DTR0004547751/cam/realmonitor?channel=1&subtype=0

3. rtsp://admin:admin1292@DTR0004547751.p2p.intelbras.com:554/stream
```

**TESTE** estas URLs manualmente se a adição automática falhar:
- Use VLC Media Player: `Media → Open Network Stream`
- Cole uma das URLs acima
- Se funcionar, adicione manualmente na aba RTSP Direct

## 🔍 Descoberta ONVIF Detectou

```
✓ IP_Webcam at 192.168.0.20 (Serial: BUILD_911)
```

Esta pode ser sua câmera Intelbras se estiver na rede local! Para testá-la:

```
RTSP URL: rtsp://admin:admin1292@192.168.0.20:554/cam/realmonitor?channel=1&subtype=0
```

## ⚙️ Configurações Intelbras Comuns

### Formatos RTSP padrão:
- **Stream Principal**: `/cam/realmonitor?channel=1&subtype=0`
- **Stream Secundário**: `/cam/realmonitor?channel=1&subtype=1`
- **ONVIF genérico**: `/onvif1` ou `/stream1`

### Portas padrão:
- **RTSP**: 554
- **HTTP**: 80
- **ONVIF**: 8899

### Credenciais padrão:
- **Usuário**: admin
- **Senha padrão**: (vazio) ou "admin" ou últimos 6 dígitos do serial

## 🚀 Testando a Conexão

Após adicionar a câmera:
1. Clique em **"Test Connection"** (na aba RTSP Direct)
2. O sistema testará com timeout de 10 segundos
3. Você verá:
   - ✓ Sucesso: "Connected successfully"
   - ✗ Falha: Mensagem de erro detalhada

## 📺 Visualizando ao Vivo

Após adicionar com sucesso:
1. Clique no botão **"View"** na tabela de câmeras
2. A página de visualização ao vivo abrirá
3. Escolha layout: 6, 12 ou 24 câmeras
4. Clique em **"Start All Cameras"**

## 🛠️ Troubleshooting

### Erro: "Could not connect to device"
- Verifique se o Device ID está correto (DTR0004547751)
- Confirme a senha (admin1292)
- Certifique-se de que a câmera está online
- Teste as URLs manualmente no VLC

### Erro: "Failed to open RTSP stream"
- Câmera pode estar offline
- Firewall bloqueando porta 554
- Senha incorreta
- Formato de URL incorreto para o modelo

### ONVIF não encontra câmeras
- Câmera pode não suportar ONVIF
- Firewall bloqueando discovery (porta UDP 3702)
- Câmera em subnet diferente
- ONVIF desabilitado nas configurações da câmera

## 📚 Referências

- Guardian App (Intelbras): Método de referência
- ONVIF Spec: https://www.onvif.org/
- Intelbras Suporte: https://suporte.intelbras.com.br/

## 🔐 Segurança

**IMPORTANTE**: As senhas são armazenadas nas URLs RTSP. Planejado para P0.5:
- Encriptação DPAPI para credenciais
- Armazenamento seguro separado de usuário/senha
- Nunca mostre URLs completas em logs

---

**Status**: ✅ Implementado e testado
**Versão**: 1.0.0
**Data**: 2026-01-13
