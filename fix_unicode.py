"""Fix Unicode characters for Windows console"""
from pathlib import Path

src_dir = Path("c:/Aguia/src")
fixed_count = 0

replacements = {
    '✓': '[OK]',
    '✗': '[ERRO]',
    '⚠': '[AVISO]',
}

for py_file in src_dir.rglob("*.py"):
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        if content != original:
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Fixed: {py_file.relative_to(src_dir)}")
            fixed_count += 1
    except Exception as e:
        print(f"[ERRO] Error in {py_file.name}: {e}")

print(f"\n{fixed_count} files fixed!")
