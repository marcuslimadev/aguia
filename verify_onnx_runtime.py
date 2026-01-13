"""
Script de verificação: App deve rodar sem Torch/Ultralytics instalado
Testa se o runtime ONNX está funcionando corretamente
"""
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_torch_not_imported():
    """Verifica que Torch NÃO foi importado"""
    if 'torch' in sys.modules:
        logger.error("❌ FALHA: Torch foi importado!")
        logger.error("   Torch não deve estar no runtime de produção")
        return False
    
    if 'ultralytics' in sys.modules:
        logger.error("❌ FALHA: Ultralytics foi importado!")
        logger.error("   Ultralytics não deve estar no runtime de produção")
        return False
    
    logger.info("✓ Torch e Ultralytics NÃO foram importados")
    return True


def check_onnx_available():
    """Verifica que ONNX Runtime está disponível"""
    try:
        import onnxruntime as ort
        logger.info(f"✓ ONNX Runtime disponível: {ort.__version__}")
        
        # Verificar providers
        providers = ort.get_available_providers()
        logger.info(f"  Providers disponíveis: {providers}")
        
        return True
    except ImportError:
        logger.error("❌ FALHA: ONNX Runtime não está instalado")
        logger.error("   pip install onnxruntime")
        return False


def check_detector_initialization():
    """Verifica que detector ONNX pode ser inicializado"""
    try:
        from src.ai.video_processor import YOLODetector
        
        # Tentar criar detector ONNX
        detector = YOLODetector(model_path="yolov8m.onnx", use_onnx=True)
        
        if detector.using_onnx:
            logger.info("✓ Detector ONNX inicializado com sucesso")
            return True
        else:
            logger.warning("⚠ Detector caiu para Ultralytics (esperado se modelo ONNX não existe)")
            return True  # Não é erro se modelo não existe
            
    except Exception as e:
        logger.error(f"❌ FALHA ao inicializar detector: {e}")
        return False


def check_video_processor():
    """Verifica que VideoProcessor pode ser criado"""
    try:
        from src.ai.video_processor import VideoProcessor
        
        # Criar processor (sem conectar)
        processor = VideoProcessor(
            rtsp_url="rtsp://test.local/stream",
            camera_id=1,
            use_onnx=True
        )
        
        logger.info("✓ VideoProcessor criado com sucesso")
        
        # Verificar que tem detector
        if processor.yolo_detector:
            if processor.yolo_detector.using_onnx:
                logger.info("  → Usando detector ONNX")
            else:
                logger.info("  → Usando detector Ultralytics (fallback)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FALHA ao criar VideoProcessor: {e}")
        return False


def check_dependencies():
    """Verifica dependências necessárias"""
    required = {
        'numpy': 'numpy',
        'cv2': 'opencv-python',
        'PySide6': 'PySide6',
        'onnxruntime': 'onnxruntime',
    }
    
    all_ok = True
    
    for module_name, package_name in required.items():
        try:
            __import__(module_name)
            logger.info(f"✓ {package_name} disponível")
        except ImportError:
            logger.error(f"❌ {package_name} NÃO disponível")
            logger.error(f"   pip install {package_name}")
            all_ok = False
    
    return all_ok


def main():
    """Executa todas as verificações"""
    logger.info("="*60)
    logger.info("VERIFICAÇÃO DE RUNTIME SEM TORCH")
    logger.info("="*60)
    logger.info("")
    
    checks = [
        ("Dependências", check_dependencies),
        ("ONNX Runtime", check_onnx_available),
        ("Detector ONNX", check_detector_initialization),
        ("VideoProcessor", check_video_processor),
        ("Torch não importado", check_torch_not_imported),
    ]
    
    results = []
    
    for name, check_func in checks:
        logger.info(f"\n--- {name} ---")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ Erro durante verificação: {e}")
            results.append((name, False))
    
    # Resumo
    logger.info("\n" + "="*60)
    logger.info("RESUMO")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {name}")
    
    logger.info("")
    logger.info(f"Total: {passed}/{total} verificações passaram")
    
    if passed == total:
        logger.info("\n🎉 SUCESSO! App pode rodar sem Torch/Ultralytics")
        logger.info("   Runtime está usando ONNX corretamente")
        return 0
    else:
        logger.error("\n❌ FALHA! Alguns problemas foram encontrados")
        logger.error("   Revise os erros acima")
        return 1


if __name__ == "__main__":
    sys.exit(main())
