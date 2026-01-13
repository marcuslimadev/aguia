# Exportação de Modelo YOLO para ONNX

Este guia explica como exportar o modelo YOLOv8 para formato ONNX para uso em produção.

## Por que ONNX?

- **Tamanho reduzido**: MSIX sem Torch é ~80% menor
- **Performance**: ONNX Runtime é otimizado para inferência
- **Compatibilidade**: Funciona sem dependências pesadas (Torch/CUDA)
- **Microsoft Store**: Requisito para publicação

## Pré-requisitos (Dev Only)

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt
```

Isso instala:
- `torch` - Necessário para carregar modelo .pt
- `ultralytics` - YOLO framework
- `onnx` - Para verificação
- `onnx-simplifier` - Otimização do modelo

## Exportação Rápida

### Método 1: Script Automatizado (Recomendado)

```bash
# Exportar YOLOv8m (medium) - padrão
python export_model_to_onnx.py

# Exportar e testar
python export_model_to_onnx.py --test

# Exportar outro modelo
python export_model_to_onnx.py --model yolov8n.pt  # nano (mais rápido)
python export_model_to_onnx.py --model yolov8s.pt  # small
python export_model_to_onnx.py --model yolov8l.pt  # large
python export_model_to_onnx.py --model yolov8x.pt  # xlarge (mais preciso)

# Com opções
python export_model_to_onnx.py \
    --model yolov8m.pt \
    --output C:/ProgramData/EdgeAI/models \
    --imgsz 640 \
    --test
```

### Método 2: Manual (Python)

```python
from ultralytics import YOLO

# Carregar modelo
model = YOLO("yolov8m.pt")

# Exportar para ONNX
model.export(
    format="onnx",
    imgsz=640,
    half=False,        # FP32 para compatibilidade
    simplify=True,     # Otimizar modelo
    dynamic=False,     # Tamanho fixo
    opset=12           # Versão ONNX
)
```

## Verificação

Após exportação, verificar:

```bash
# 1. Verificar que modelo foi criado
ls C:/ProgramData/EdgeAI/models/yolov8m.onnx

# 2. Testar runtime ONNX (sem Torch)
python verify_onnx_runtime.py

# 3. Executar testes
pytest tests/test_yolo_onnx.py -v
```

## Comparação de Modelos

| Modelo | Tamanho ONNX | Velocidade | mAP | Recomendação |
|--------|--------------|------------|-----|--------------|
| yolov8n | ~6 MB | ⚡⚡⚡ | 37.3 | Testes rápidos |
| yolov8s | ~22 MB | ⚡⚡ | 44.9 | Embedded devices |
| **yolov8m** | **~52 MB** | **⚡** | **50.2** | **Produção (padrão)** |
| yolov8l | ~88 MB | ⚠️ | 52.9 | Alta precisão |
| yolov8x | ~136 MB | ⚠️⚠️ | 53.9 | Máxima precisão |

**Recomendação**: `yolov8m` oferece melhor balanço precisão/velocidade/tamanho.

## Troubleshooting

### Erro: "No module named 'ultralytics'"

```bash
pip install ultralytics torch
```

### Erro: "ONNX model validation failed"

```bash
# Reinstalar onnx
pip uninstall onnx
pip install onnx==1.14.1
```

### Modelo .onnx não aparece em MODELS_DIR

```bash
# Verificar caminho
python -c "from config.config import MODELS_DIR; print(MODELS_DIR)"

# Criar diretório manualmente
mkdir C:/ProgramData/EdgeAI/models

# Mover modelo manualmente
move yolov8m.onnx C:/ProgramData/EdgeAI/models/
```

### Runtime não usa ONNX (cai para Ultralytics)

1. Verificar que modelo existe:
   ```bash
   ls C:/ProgramData/EdgeAI/models/yolov8m.onnx
   ```

2. Verificar logs da aplicação:
   ```
   ✓ Usando detector ONNX: C:/ProgramData/EdgeAI/models/yolov8m.onnx
   ```

3. Se ainda usar Ultralytics, verificar:
   ```bash
   python verify_onnx_runtime.py
   ```

## Deployment

Para produção, após exportar modelo:

1. **Remover Torch do ambiente**:
   ```bash
   pip uninstall torch ultralytics
   pip install -r requirements.txt  # Apenas runtime deps
   ```

2. **Verificar que funciona**:
   ```bash
   python verify_onnx_runtime.py
   python main.py
   ```

3. **Build para distribuição**:
   ```bash
   python build_windows.py
   ```

O build automaticamente:
- Inclui `onnxruntime`
- Exclui `torch`
- Copia modelo `.onnx`
- Gera MSIX otimizado

## Performance Esperada

Com ONNX Runtime (CPU):
- **1 câmera 1280×720**: ~5 FPS, 20-30% CPU
- **3 câmeras 1280×720**: ~15 FPS total, 50-60% CPU
- **RAM**: ~500 MB por câmera

Com ONNX Runtime (GPU - opcional):
```bash
pip install onnxruntime-gpu
```
- **1 câmera 1920×1080**: ~15-20 FPS
- **5+ câmeras**: Processamento paralelo eficiente

## Próximos Passos

Após exportar modelo ONNX:

1. ✅ Testar detecção: `pytest tests/test_yolo_onnx.py`
2. ✅ Verificar runtime: `python verify_onnx_runtime.py`
3. ✅ Executar app: `python main.py`
4. ➡️ **Passo 3**: Integrar Event Engine (eventos temporais)

---

**Nota**: Modelos .pt (Torch) devem ser mantidos apenas no ambiente de desenvolvimento para possíveis re-exportações ou fine-tuning.
