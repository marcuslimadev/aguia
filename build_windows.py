"""
Script de build para compilar a aplicação com Nuitka (PRODUCTION)
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

def build_executable():
    """Compila a aplicação para executável Windows"""
    
    project_root = Path(__file__).parent
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    # Criar diretórios
    build_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("EDGE PROPERTY SECURITY AI - Windows Build (Production)")
    print("=" * 80)
    print()
    
    # Verificar se está usando requirements.txt correto (ONNX, não Torch)
    print("✓ Verificando dependencies...")
    with open(project_root / "requirements.txt") as f:
        reqs = f.read()
        if "torch" in reqs.lower() or "ultralytics" in reqs.lower():
            print("⚠ WARNING: requirements.txt contém torch/ultralytics!")
            print("  Para build de produção, use apenas onnxruntime.")
            print("  Torch deve estar em requirements-dev.txt apenas.")
            response = input("Continuar mesmo assim? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    
    # Comando Nuitka (PRODUCTION)
    nuitka_cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",  # Standalone ao invés de onefile (mais compatível)
        "--windows-disable-console",  # Sem console
        "--enable-plugin=pyside6",  # Plugin PySide6
        "--include-package=cv2",
        "--include-package=numpy",
        "--include-package=onnxruntime",  # ONNX apenas
        "--include-package-data=config",  # Incluir config
        "--include-data-dir=data=data",  # Incluir models
        "--include-data-dir=translations=translations",  # Incluir i18n
        "--nofollow-import-to=torch",  # IGNORE torch (production)
        "--nofollow-import-to=ultralytics",  # IGNORE ultralytics (production)
        "--output-dir=" + str(build_dir),
        "--output-filename=EdgePropertySecurityAI.exe",
        "--company-name=Edge Property Security",
        "--product-name=Edge Property Security AI",
        "--file-version=1.0.0.0",
        "--product-version=1.0",
        "--file-description=AI-powered property security monitoring",
        "--windows-icon-from-ico=assets/icon.ico" if (project_root / "assets" / "icon.ico").exists() else "",
        str(project_root / "main.py")
    ]
    
    # Remover opções vazias
    nuitka_cmd = [arg for arg in nuitka_cmd if arg]
    
    print("✓ Iniciando compilação com Nuitka...")
    print()
    print("Command:")
    print(" ".join(nuitka_cmd))
    print()
    
    result = subprocess.run(nuitka_cmd)
    
    if result.returncode == 0:
        print()
        print("=" * 80)
        print("✓ Compilação concluída com sucesso!")
        print("=" * 80)
        print(f"Executável gerado em: {build_dir}")
        
        # Verificar tamanho
        exe_path = build_dir / "EdgePropertySecurityAI.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Tamanho: {size_mb:.1f} MB")
            
            if size_mb > 1000:
                print("⚠ WARNING: Build > 1GB! Verifique se Torch foi excluído.")
        
        return True
    else:
        print()
        print("=" * 80)
        print("✗ Erro durante a compilação")
        print("=" * 80)
        sys.exit(1)


def create_msix_package():
    """Cria o pacote MSIX para Microsoft Store"""
    
    project_root = Path(__file__).parent
    build_dir = project_root / "build"
    msix_dir = project_root / "msix_package"
    
    print()
    print("=" * 80)
    print("Criando pacote MSIX para Microsoft Store")
    print("=" * 80)
    print()
    
    # Criar estrutura MSIX
    msix_dir.mkdir(exist_ok=True)
    
    # Copiar executável
    exe_source = build_dir / "EdgePropertySecurityAI.dist"
    if not exe_source.exists():
        print("✗ Erro: Build não encontrado! Execute build primeiro.")
        print(f"Esperado: {exe_source}")
        sys.exit(1)
    
    print(f"✓ Copiando build de: {exe_source}")
    shutil.copytree(exe_source, msix_dir / "app", dirs_exist_ok=True)
    
    # Copiar AppxManifest.xml
    manifest_source = project_root / "AppxManifest.xml"
    if manifest_source.exists():
        print("✓ Copiando AppxManifest.xml")
        shutil.copy(manifest_source, msix_dir / "AppxManifest.xml")
    else:
        print("⚠ AppxManifest.xml não encontrado!")
    
    # Copiar assets
    assets_source = project_root / "assets"
    if assets_source.exists():
        print("✓ Copiando assets (icons)")
        shutil.copytree(assets_source, msix_dir / "assets", dirs_exist_ok=True)
    
    print()
    print("✓ Estrutura MSIX criada em:", msix_dir)
    print()
    print("Próximo passo: Criar pacote MSIX")
    print()
    print("Execute:")
    print(f'  makeappx pack /d "{msix_dir}" /p EdgePropertySecurityAI.msix')
    print()
    print("Para assinar:")
    print(f'  signtool sign /fd SHA256 /a /f <certificado.pfx> EdgePropertySecurityAI.msix')
    print()
    
    # Opcionalmente executar makeappx automaticamente
    try:
        makeappx_cmd = [
            "makeappx.exe",
            "pack",
            "/d", str(msix_dir),
            "/p", str(project_root / "EdgePropertySecurityAI.msix"),
            "/o"  # Overwrite
        ]
        
        print("Executando makeappx...")
        result = subprocess.run(makeappx_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ MSIX criado com sucesso!")
            print(f"  {project_root / 'EdgePropertySecurityAI.msix'}")
            
            # Verificar tamanho
            msix_path = project_root / "EdgePropertySecurityAI.msix"
            if msix_path.exists():
                size_mb = msix_path.stat().st_size / (1024 * 1024)
                print(f"  Tamanho: {size_mb:.1f} MB")
        else:
            print("⚠ makeappx falhou ou não está instalado")
            print("Output:", result.stderr)
    
    except FileNotFoundError:
        print("⚠ makeappx.exe não encontrado no PATH")
        print("Instale Windows SDK: https://developer.microsoft.com/windows/downloads/windows-sdk/")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--msix":
        # Apenas MSIX (assume que build já foi feito)
        create_msix_package()
    elif len(sys.argv) > 1 and sys.argv[1] == "--full":
        # Build + MSIX
        if build_executable():
            create_msix_package()
    else:
        # Apenas build
        build_executable()

