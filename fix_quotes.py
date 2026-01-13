"""Fix ALL escaped strings in Python files"""
from pathlib import Path
import re

src_dir = Path("c:/Aguia/src")
fixed_count = 0

for py_file in src_dir.rglob("*.py"):
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            original = f.read()
        
        # Fix escaped triple quotes
        content = original.replace('\\"\\"\\"', '"""')
        # Fix escaped single quotes in strings  
        content = content.replace('\\"', '"')
        
        if content != original:
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed: {py_file.relative_to(src_dir)}")
            fixed_count += 1
    except Exception as e:
        print(f"✗ Error in {py_file.name}: {e}")

print(f"\n{fixed_count} files fixed!")
