#!/usr/bin/env python3
"""
Script simples para testar o Design System Bauhaus
Sem dependências externas (sem pytest)
"""

import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

def test_tokens():
    """Testa os tokens Bauhaus"""
    print("\n" + "="*60)
    print("TESTANDO TOKENS BAUHAUS")
    print("="*60)
    
    try:
        from config.bauhaus_tokens import (
            BAUHAUS_PALETTE, BORDER_RADIUS, SPACING, TYPOGRAPHY,
            BUTTONS, BADGES, INPUTS, CARDS
        )
        
        print("✓ Tokens importados com sucesso")
        
        # Verificar paleta
        assert "black" in BAUHAUS_PALETTE, "Cor 'black' não encontrada"
        assert BAUHAUS_PALETTE["black"] == "#0E0E0E", "Cor 'black' incorreta"
        print("✓ Paleta de cores validada")
        
        # Verificar border radius
        assert "buttons" in BORDER_RADIUS, "Border radius 'buttons' não encontrado"
        assert BORDER_RADIUS["buttons"] == "8px", "Border radius 'buttons' incorreto"
        print("✓ Border radius validado")
        
        # Verificar espaçamento
        assert SPACING["xs"] == "4px", "Espaçamento 'xs' incorreto"
        assert SPACING["md"] == "16px", "Espaçamento 'md' incorreto"
        print("✓ Sistema de espaçamento validado")
        
        # Verificar botões
        assert "primary" in BUTTONS, "Estilo 'primary' não encontrado"
        assert BUTTONS["primary"]["background"] == "#005BFF", "Cor primária incorreta"
        print("✓ Estilos de botão validados")
        
        # Verificar badges
        assert "success" in BADGES, "Badge 'success' não encontrado"
        assert BADGES["success"]["background"] == "#00A859", "Cor de sucesso incorreta"
        print("✓ Estilos de badge validados")
        
        print("\n✅ TODOS OS TESTES DE TOKENS PASSARAM!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES DE TOKENS: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_theme():
    """Testa o tema Bauhaus"""
    print("\n" + "="*60)
    print("TESTANDO TEMA BAUHAUS")
    print("="*60)
    
    try:
        from config.bauhaus_theme import get_bauhaus_stylesheet
        
        stylesheet = get_bauhaus_stylesheet()
        print("✓ Tema gerado com sucesso")
        
        assert isinstance(stylesheet, str), "Stylesheet não é string"
        assert len(stylesheet) > 1000, "Stylesheet muito pequeno"
        print(f"✓ Stylesheet tem {len(stylesheet)} caracteres")
        
        # Verificar cores no stylesheet
        assert "#0E0E0E" in stylesheet, "Cor black não encontrada no stylesheet"
        assert "#005BFF" in stylesheet, "Cor blue não encontrada no stylesheet"
        assert "#E10600" in stylesheet, "Cor red não encontrada no stylesheet"
        print("✓ Cores Bauhaus encontradas no stylesheet")
        
        # Verificar componentes
        assert "QPushButton" in stylesheet, "QPushButton não encontrado"
        assert "QLineEdit" in stylesheet, "QLineEdit não encontrado"
        assert "QFrame" in stylesheet, "QFrame não encontrado"
        print("✓ Componentes encontrados no stylesheet")
        
        # Verificar estados
        assert ":hover" in stylesheet, "Estado :hover não encontrado"
        assert ":focus" in stylesheet, "Estado :focus não encontrado"
        print("✓ Estados de componentes encontrados no stylesheet")
        
        print("\n✅ TODOS OS TESTES DE TEMA PASSARAM!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES DE TEMA: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_components():
    """Testa os componentes Bauhaus"""
    print("\n" + "="*60)
    print("TESTANDO COMPONENTES BAUHAUS")
    print("="*60)
    
    try:
        from src.ui.bauhaus_components import (
            BauhausButton,
            BauhausSecondaryButton,
            BauhausDangerButton,
            BauhausHighlightButton,
            BauhausGhostButton,
            BauhausLineEdit,
            BauhausTextEdit,
            BauhausComboBox,
            BauhausSpinBox,
            BauhausDoubleSpinBox,
            BauhausCard,
            BauhausStatCard,
            BauhausPageTitle,
            BauhausSectionTitle,
            BauhausBadge,
            BauhausContainer,
            BauhausHorizontalContainer,
            BauhausFormField,
            BauhausDivider
        )
        
        print("✓ Todos os componentes importados com sucesso")
        
        # Verificar que são classes
        assert callable(BauhausButton), "BauhausButton não é callable"
        assert callable(BauhausCard), "BauhausCard não é callable"
        assert callable(BauhausLineEdit), "BauhausLineEdit não é callable"
        print("✓ Componentes são classes válidas")
        
        print("\n✅ TODOS OS TESTES DE COMPONENTES PASSARAM!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES DE COMPONENTES: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_documentation():
    """Testa a documentação"""
    print("\n" + "="*60)
    print("TESTANDO DOCUMENTAÇÃO")
    print("="*60)
    
    try:
        doc_path = Path(__file__).parent / "BAUHAUS_DESIGN_SYSTEM.md"
        
        assert doc_path.exists(), "Arquivo de documentação não encontrado"
        print(f"✓ Documentação encontrada em {doc_path}")
        
        content = doc_path.read_text()
        assert len(content) > 100, "Documentação muito pequena"
        print(f"✓ Documentação tem {len(content)} caracteres")
        
        assert "Bauhaus Moderno" in content, "Título não encontrado"
        assert "Design System" in content, "Subtítulo não encontrado"
        assert "Paleta de Cores" in content or "Paleta" in content, "Seção de cores não encontrada"
        print("✓ Documentação contém seções esperadas")
        
        print("\n✅ TODOS OS TESTES DE DOCUMENTAÇÃO PASSARAM!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES DE DOCUMENTAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  TESTE DO DESIGN SYSTEM BAUHAUS MODERNO".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        "Tokens": test_tokens(),
        "Tema": test_theme(),
        "Componentes": test_components(),
        "Documentação": test_documentation(),
    }
    
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*60)
        print("\nO Design System Bauhaus Moderno está pronto para uso!")
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
