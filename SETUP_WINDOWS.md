# Setup para Windows - Edge Property Security AI

Este guia fornece instruções passo a passo para configurar o ambiente de desenvolvimento e compilar a aplicação para Windows.

## Pré-requisitos

- **Windows 10/11** (64-bit)
- **Python 3.11+** (https://www.python.org/downloads/)
- **Git** (https://git-scm.com/download/win)
- **Visual Studio Build Tools** (para compilação)

## Instalação do Ambiente

### 1. Clonar o Repositório

```bash
git clone <repository-url>
cd edge_property_security_ai
```

### 2. Criar Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements-windows.txt
```

**Nota**: A instalação do PyTorch pode levar alguns minutos. Se encontrar problemas, tente:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. Verificar Instalação

```bash
python -c "import PySide6; import cv2; import torch; print('✓ Dependências instaladas com sucesso')"
```

## Desenvolvimento

### Executar a Aplicação

```bash
python main.py
```

### Estrutura de Diretórios

```
edge_property_security_ai/
├── config/              # Configurações
├── src/
│   ├── ui/             # Interface gráfica
│   ├── core/           # Lógica principal
│   ├── ai/             # Processamento de vídeo
│   └── utils/          # Utilitários
├── data/               # Dados e modelos
├── main.py             # Ponto de entrada
└── build_windows.py    # Script de build
```

## Build para Release

### 1. Compilar com Nuitka

```bash
python build_windows.py
```

Isto criará um executável em `build/main.exe`.

**Tempo estimado**: 10-30 minutos (primeira vez)

### 2. Testar o Executável

```bash
build\main.exe
```

### 3. Criar Pacote MSIX (Opcional)

Para publicar na Microsoft Store, você precisa criar um pacote MSIX:

```bash
# Instalar ferramentas de packaging
# https://docs.microsoft.com/en-us/windows/msix/packaging-tool/tool-overview

# Usar o manifesto fornecido
# AppxManifest.xml
```

## Assinatura Digital

Para publicar na Microsoft Store, o executável deve ser assinado:

### 1. Gerar Certificado (Desenvolvimento)

```bash
# Windows PowerShell (como Administrador)
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=EdgeSecurity" -CertStoreLocation Cert:\CurrentUser\My
Export-PfxCertificate -Cert $cert -FilePath EdgeSecurity.pfx -Password (ConvertTo-SecureString -String "password" -AsPlainText -Force)
```

### 2. Assinar o Executável

```bash
# Usando SignTool (Visual Studio)
"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe" sign /f EdgeSecurity.pfx /p password /t http://timestamp.comodoca.com/authenticode build\main.exe
```

## Configuração para Microsoft Store

### 1. Preparar Pacote MSIX

```bash
# Criar diretório de distribuição
mkdir dist
copy build\main.exe dist\
copy AppxManifest.xml dist\

# Criar pacote MSIX
makeappx pack /d dist /p EdgePropertySecurityAI.msix
```

### 2. Assinar Pacote MSIX

```bash
signtool sign /f EdgeSecurity.pfx /p password /t http://timestamp.comodoca.com/authenticode EdgePropertySecurityAI.msix
```

### 3. Enviar para Microsoft Store

1. Acesse https://partner.microsoft.com/dashboard
2. Crie nova aplicação
3. Preencha informações de produto
4. Faça upload do pacote MSIX
5. Aguarde aprovação

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'PySide6'"

```bash
pip install --upgrade PySide6
```

### Erro: "CUDA not available" (ao usar GPU)

```bash
# Instalar CUDA Toolkit 11.8
# https://developer.nvidia.com/cuda-11-8-0-download-archive

# Ou usar CPU (mais lento)
```

### Erro ao compilar com Nuitka

```bash
# Limpar cache
rm -r build
rm -r .nuitka

# Tentar novamente
python build_windows.py
```

### Aplicação não inicia após build

1. Verificar logs em `C:\ProgramData\EdgeAI\logs`
2. Executar em modo debug:
   ```bash
   python main.py
   ```
3. Verificar se todas as dependências estão instaladas

## Performance

### Otimizações para Windows

1. **Usar GPU NVIDIA**:
   - Instalar CUDA Toolkit
   - Instalar cuDNN
   - Usar `torch.cuda.is_available()` para verificar

2. **Reduzir Consumo de Memória**:
   - Editar `config/config.py`
   - Reduzir `FRAME_SKIP`
   - Usar modelo YOLO menor (yolov8n.pt)

3. **Melhorar Velocidade**:
   - Usar GPU
   - Aumentar `FRAME_SKIP`
   - Reduzir resolução de entrada

## Distribuição

### Opções de Distribuição

1. **Microsoft Store** (Recomendado)
   - Alcance máximo
   - Atualizações automáticas
   - Gerenciamento de licenças integrado

2. **Website Próprio**
   - Controle total
   - Sem comissão
   - Requer infraestrutura própria

3. **GitHub Releases**
   - Para versões beta/teste
   - Controle de versão

## Suporte

Para problemas ou dúvidas:
- Documentação: https://github.com/edgesecurity/edge-property-security-ai
- Issues: https://github.com/edgesecurity/edge-property-security-ai/issues
- Email: support@edgesecurity.ai

## Próximos Passos

1. ✓ Configurar ambiente
2. ✓ Executar aplicação
3. → Testar funcionalidades
4. → Compilar para release
5. → Publicar na Microsoft Store

---

**Última atualização**: Janeiro 2024
