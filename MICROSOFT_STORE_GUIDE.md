# Guia de Publicação na Microsoft Store

Este guia fornece instruções passo a passo para publicar o Edge Property Security AI na Microsoft Store.

## Pré-requisitos

1. **Conta Microsoft Partner Center**
   - Acesse: https://partner.microsoft.com/dashboard
   - Crie uma conta ou faça login
   - Pague a taxa de registro ($19 USD)

2. **Certificado de Assinatura**
   - Certificado de desenvolvedor ou comercial
   - Para desenvolvimento: auto-assinado
   - Para produção: certificado válido de CA

3. **Aplicação Compilada**
   - Executável Windows compilado com Nuitka
   - Todos os assets (ícones, screenshots)
   - Descrição e informações de produto

## Passo 1: Preparar Aplicação

### 1.1 Compilar com Nuitka

```bash
cd edge_property_security_ai
python build_windows.py
```

Isto cria `build/main.exe`

### 1.2 Preparar Assets

Criar os seguintes arquivos de imagem:

- **Logo da Aplicação**: 150x150px (PNG)
- **Screenshot 1**: 1920x1080px (PNG)
- **Screenshot 2**: 1920x1080px (PNG)
- **Screenshot 3**: 1920x1080px (PNG)
- **Tile Grande**: 310x310px (PNG)
- **Tile Pequeno**: 150x150px (PNG)

Salvar em: `assets/store/`

### 1.3 Preparar Descrição

**Título**: Edge Property Security AI

**Descrição Curta** (até 120 caracteres):
```
Professional property security with AI-powered video analysis
```

**Descrição Longa**:
```
Edge Property Security AI is a professional property security software 
that performs real-time local video analysis using artificial intelligence 
to protect physical assets.

Features:
- Real-time video analysis with YOLOv8 AI
- Local processing - no cloud uploads
- Multi-camera support
- Email alerts with snapshots
- Zone-based security rules
- Trial license included (7 days, 2 cameras)

Security Events:
- Intrusion detection
- Theft pattern recognition
- Loitering detection
- Restricted area access
- Crowd anomalies
- Fire and smoke detection
- Vandalism detection

System Requirements:
- Windows 10 or later (64-bit)
- 8GB RAM minimum
- 2GB free storage
- Internet connection for email alerts
```

## Passo 2: Criar Pacote MSIX

### 2.1 Gerar Certificado (Desenvolvimento)

```powershell
# Windows PowerShell (como Administrador)
$cert = New-SelfSignedCertificate -Type CodeSigningCert `
  -Subject "CN=EdgeSecurity" `
  -CertStoreLocation Cert:\CurrentUser\My

Export-PfxCertificate -Cert $cert -FilePath EdgeSecurity.pfx `
  -Password (ConvertTo-SecureString -String "YourPassword" -AsPlainText -Force)
```

### 2.2 Criar Estrutura de Distribuição

```bash
mkdir dist
copy build\main.exe dist\
copy assets\store\* dist\
copy AppxManifest.xml dist\
```

### 2.3 Criar Pacote MSIX

```powershell
# Instalar ferramentas (se necessário)
# https://docs.microsoft.com/en-us/windows/msix/packaging-tool/tool-overview

# Criar pacote
makeappx pack /d dist /p EdgePropertySecurityAI.msix
```

### 2.4 Assinar Pacote

```powershell
$pfxPath = "EdgeSecurity.pfx"
$password = "YourPassword"
$timestamp = "http://timestamp.comodoca.com/authenticode"

signtool sign /f $pfxPath /p $password /t $timestamp `
  EdgePropertySecurityAI.msix
```

## Passo 3: Enviar para Microsoft Store

### 3.1 Acessar Partner Center

1. Acesse: https://partner.microsoft.com/dashboard
2. Clique em "Create a new app"
3. Selecione "Windows App"

### 3.2 Preencher Informações de Produto

**Informações Básicas:**
- Nome do Aplicativo: Edge Property Security AI
- Categoria: Utilities
- Subcategoria: System Utilities

**Informações de Contato:**
- Email de suporte
- Website
- Telefone de suporte (opcional)

**Classificação de Conteúdo:**
- Responder questionário de classificação IARC

### 3.3 Fazer Upload do Pacote

1. Ir para "Packages"
2. Clicar "Upload package"
3. Selecionar `EdgePropertySecurityAI.msix`
4. Aguardar validação

### 3.4 Configurar Preço e Disponibilidade

**Preço:**
- Selecionar modelo de preço
- Opções: Gratuito com compras no app, ou pago

**Disponibilidade:**
- Selecionar mercados onde disponibilizar
- Definir data de lançamento

### 3.5 Adicionar Screenshots e Descrição

1. Fazer upload de screenshots (mínimo 3)
2. Adicionar descrição
3. Adicionar palavras-chave (tags)
4. Adicionar informações de privacidade

### 3.6 Revisar e Enviar

1. Revisar todas as informações
2. Aceitar termos e condições
3. Clicar "Submit for review"

## Passo 4: Processo de Revisão

### Tempo de Revisão

- Geralmente: 24-48 horas
- Máximo: 7 dias

### Critérios de Aprovação

- ✓ Aplicação deve funcionar corretamente
- ✓ Sem malware ou comportamento suspeito
- ✓ Descrição precisa e completa
- ✓ Screenshots relevantes
- ✓ Política de privacidade clara
- ✓ Sem conteúdo ofensivo

### Possíveis Rejeições

Se rejeitado, você receberá motivo e poderá:
1. Corrigir problemas
2. Reenviar para revisão

## Passo 5: Publicação e Manutenção

### Após Aprovação

- Aplicação fica disponível na Microsoft Store
- Usuários podem fazer download e instalar
- Atualizações automáticas habilitadas

### Atualizações

Para atualizar:

1. Compilar nova versão
2. Incrementar versão em `AppxManifest.xml`
3. Criar novo pacote MSIX
4. Fazer upload via Partner Center

### Monitoramento

- Verificar reviews e ratings
- Responder a feedback de usuários
- Monitorar crashes e erros
- Atualizar regularmente

## Dicas Importantes

### Segurança

- ✓ Sempre assinar pacotes
- ✓ Usar certificados válidos
- ✓ Manter chaves privadas seguras
- ✓ Implementar DRM corretamente

### Performance

- ✓ Otimizar tamanho do executável
- ✓ Testar em diferentes configurações
- ✓ Monitorar uso de memória
- ✓ Implementar tratamento de erros

### Conformidade

- ✓ Cumprir políticas da Microsoft Store
- ✓ Respeitar privacidade do usuário
- ✓ Incluir política de privacidade
- ✓ Fornecer suporte ao cliente

## Troubleshooting

### Erro: "Invalid certificate"

```powershell
# Verificar certificado
Get-ChildItem Cert:\CurrentUser\My | Where-Object {$_.Subject -like "*EdgeSecurity*"}
```

### Erro: "Package validation failed"

1. Verificar `AppxManifest.xml`
2. Validar integridade do executável
3. Testar pacote localmente

### Erro: "Signature verification failed"

```powershell
# Verificar assinatura
signtool verify /pa EdgePropertySecurityAI.msix
```

## Recursos Adicionais

- [Microsoft Store Documentation](https://docs.microsoft.com/en-us/windows/msix/)
- [Partner Center Help](https://partner.microsoft.com/en-us/dashboard/support)
- [App Certification Requirements](https://docs.microsoft.com/en-us/windows/uwp/publish/store-policies)

## Contato de Suporte

- Email: support@edgesecurity.ai
- Website: https://edgesecurity.ai
- Help: https://help.manus.im

---

**Última atualização**: Janeiro 2024
