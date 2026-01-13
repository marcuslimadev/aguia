"""
Script para exportar modelo YOLOv8 para formato ONNX
Executar apenas em ambiente de desenvolvimento (requer ultralytics/torch)
"""
import logging
from pathlib import Path
from config.config import MODELS_DIR, YOLO_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def export_yolo_to_onnx(
    model_name: str = "yolov8m.pt",
    output_dir: Path = MODELS_DIR,
    imgsz: int = 640,
    simplify: bool = True
):
    """
    Exporta modelo YOLOv8 para ONNX
    
    Args:
        model_name: Nome do modelo YOLOv8 (.pt)
        output_dir: Diretório de saída
        imgsz: Tamanho de entrada (640 recomendado)
        simplify: Simplificar modelo ONNX
    """
    try:
        from ultralytics import YOLO
        import onnx
        from onnxsim import simplify as onnx_simplify
        
        logger.info("="*60)
        logger.info("EXPORTAÇÃO DE MODELO YOLO PARA ONNX")
        logger.info("="*60)
        
        # Criar diretório se não existe
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Carregar modelo
        logger.info(f"Carregando modelo: {model_name}")
        model = YOLO(model_name)
        
        # Exportar para ONNX
        logger.info(f"Exportando para ONNX (tamanho de entrada: {imgsz}×{imgsz})...")
        
        onnx_path = model.export(
            format="onnx",
            imgsz=imgsz,
            half=False,  # FP32 para compatibilidade
            simplify=simplify,
            dynamic=False,  # Tamanho fixo para melhor performance
            opset=12  # Opset compatível com a maioria dos runtimes
        )
        
        logger.info(f"✓ Modelo ONNX exportado: {onnx_path}")
        
        # Mover para diretório de modelos se necessário
        onnx_path = Path(onnx_path)
        target_path = output_dir / onnx_path.name
        
        if onnx_path != target_path:
            onnx_path.rename(target_path)
            logger.info(f"✓ Modelo movido para: {target_path}")
        
        # Verificar modelo
        logger.info("Verificando modelo ONNX...")
        onnx_model = onnx.load(str(target_path))
        onnx.checker.check_model(onnx_model)
        logger.info("✓ Modelo ONNX válido")
        
        # Informações do modelo
        logger.info("\nInformações do modelo:")
        logger.info(f"  Arquivo: {target_path}")
        logger.info(f"  Tamanho: {target_path.stat().st_size / (1024*1024):.2f} MB")
        
        # Inputs/Outputs
        logger.info(f"\n  Inputs:")
        for inp in onnx_model.graph.input:
            logger.info(f"    {inp.name}: {[d.dim_value for d in inp.type.tensor_type.shape.dim]}")
        
        logger.info(f"\n  Outputs:")
        for out in onnx_model.graph.output:
            logger.info(f"    {out.name}: {[d.dim_value for d in out.type.tensor_type.shape.dim]}")
        
        logger.info("\n" + "="*60)
        logger.info("EXPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("="*60)
        
        return target_path
        
    except ImportError as e:
        logger.error(f"Erro: {e}")
        logger.error("\nDependências necessárias:")
        logger.error("  pip install ultralytics torch onnx onnx-simplifier")
        raise
    
    except Exception as e:
        logger.error(f"Erro durante exportação: {e}", exc_info=True)
        raise


def test_onnx_model(onnx_path: Path):
    """
    Testa modelo ONNX exportado
    
    Args:
        onnx_path: Caminho para modelo ONNX
    """
    try:
        import onnxruntime as ort
        import numpy as np
        
        logger.info("\nTestando modelo ONNX...")
        
        # Criar sessão
        session = ort.InferenceSession(
            str(onnx_path),
            providers=['CPUExecutionProvider']
        )
        
        # Obter input shape
        input_name = session.get_inputs()[0].name
        input_shape = session.get_inputs()[0].shape
        
        logger.info(f"Input: {input_name} {input_shape}")
        
        # Criar input dummy
        batch_size = input_shape[0] if input_shape[0] else 1
        channels = input_shape[1]
        height = input_shape[2]
        width = input_shape[3]
        
        dummy_input = np.random.randn(batch_size, channels, height, width).astype(np.float32)
        
        # Inferência
        logger.info("Executando inferência de teste...")
        outputs = session.run(None, {input_name: dummy_input})
        
        logger.info(f"✓ Inferência bem-sucedida!")
        logger.info(f"  Output shape: {outputs[0].shape}")
        
        return True
        
    except ImportError:
        logger.warning("onnxruntime não instalado. Pulando teste.")
        logger.warning("  pip install onnxruntime")
        return False
    
    except Exception as e:
        logger.error(f"Erro ao testar modelo: {e}", exc_info=True)
        return False


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Exportar YOLOv8 para ONNX")
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8m.pt",
        help="Nome do modelo YOLOv8 (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(MODELS_DIR),
        help="Diretório de saída"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Tamanho de entrada"
    )
    parser.add_argument(
        "--no-simplify",
        action="store_true",
        help="Não simplificar modelo ONNX"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Testar modelo após exportação"
    )
    
    args = parser.parse_args()
    
    # Exportar
    onnx_path = export_yolo_to_onnx(
        model_name=args.model,
        output_dir=Path(args.output),
        imgsz=args.imgsz,
        simplify=not args.no_simplify
    )
    
    # Testar se solicitado
    if args.test:
        test_onnx_model(onnx_path)


if __name__ == "__main__":
    main()
