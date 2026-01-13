"""
Testes para o Design System Bauhaus Moderno
Valida tokens, componentes e tema
"""

import sys
from pathlib import Path

# Adicionar raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


class TestBauhausTokens:
    """Testes para os tokens de design Bauhaus"""
    
    def test_palette_exists(self):
        """Verifica se a paleta Bauhaus existe"""
        from config.bauhaus_tokens import BAUHAUS_PALETTE
        assert BAUHAUS_PALETTE is not None
        assert len(BAUHAUS_PALETTE) > 0
    
    def test_primary_colors(self):
        """Verifica se as cores primárias existem"""
        from config.bauhaus_tokens import BAUHAUS_PALETTE
        assert "black" in BAUHAUS_PALETTE
        assert "white" in BAUHAUS_PALETTE
        assert "blue" in BAUHAUS_PALETTE
        assert "red" in BAUHAUS_PALETTE
        assert "yellow" in BAUHAUS_PALETTE
    
    def test_color_values(self):
        """Verifica se os valores das cores estão corretos"""
        from config.bauhaus_tokens import BAUHAUS_PALETTE
        assert BAUHAUS_PALETTE["black"] == "#0E0E0E"
        assert BAUHAUS_PALETTE["white"] == "#FFFFFF"
        assert BAUHAUS_PALETTE["blue"] == "#005BFF"
        assert BAUHAUS_PALETTE["red"] == "#E10600"
        assert BAUHAUS_PALETTE["yellow"] == "#FFD600"
    
    def test_border_radius_exists(self):
        """Verifica se os raios de borda existem"""
        from config.bauhaus_tokens import BORDER_RADIUS
        assert "buttons" in BORDER_RADIUS
        assert "inputs" in BORDER_RADIUS
        assert "cards" in BORDER_RADIUS
        assert "modals" in BORDER_RADIUS
    
    def test_spacing_values(self):
        """Verifica se os valores de espaçamento estão corretos"""
        from config.bauhaus_tokens import SPACING
        assert SPACING["xs"] == "4px"
        assert SPACING["sm"] == "8px"
        assert SPACING["md"] == "16px"
        assert SPACING["lg"] == "24px"
        assert SPACING["xl"] == "32px"
    
    def test_button_styles_exist(self):
        """Verifica se os estilos de botão existem"""
        from config.bauhaus_tokens import BUTTONS
        assert "primary" in BUTTONS
        assert "secondary" in BUTTONS
        assert "destructive" in BUTTONS
        assert "highlight" in BUTTONS
    
    def test_badge_styles_exist(self):
        """Verifica se os estilos de badge existem"""
        from config.bauhaus_tokens import BADGES
        assert "success" in BADGES
        assert "error" in BADGES
        assert "warning" in BADGES
        assert "info" in BADGES


class TestBauhausTheme:
    """Testes para o tema Bauhaus"""
    
    def test_theme_generation(self):
        """Verifica se o tema pode ser gerado"""
        from config.bauhaus_theme import get_bauhaus_stylesheet
        stylesheet = get_bauhaus_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0
    
    def test_theme_contains_colors(self):
        """Verifica se o tema contém as cores Bauhaus"""
        from config.bauhaus_theme import get_bauhaus_stylesheet
        stylesheet = get_bauhaus_stylesheet()
        assert "#0E0E0E" in stylesheet  # black
        assert "#005BFF" in stylesheet  # blue
        assert "#E10600" in stylesheet  # red
        assert "#FFD600" in stylesheet  # yellow
    
    def test_theme_contains_components(self):
        """Verifica se o tema contém estilos para componentes"""
        from config.bauhaus_theme import get_bauhaus_stylesheet
        stylesheet = get_bauhaus_stylesheet()
        assert "QPushButton" in stylesheet
        assert "QLineEdit" in stylesheet
        assert "QFrame" in stylesheet
        assert "QLabel" in stylesheet
    
    def test_theme_contains_states(self):
        """Verifica se o tema contém estados de componentes"""
        from config.bauhaus_theme import get_bauhaus_stylesheet
        stylesheet = get_bauhaus_stylesheet()
        assert ":hover" in stylesheet
        assert ":pressed" in stylesheet
        assert ":focus" in stylesheet
        assert ":checked" in stylesheet


class TestBauhausComponents:
    """Testes para os componentes Bauhaus"""
    
    def test_button_import(self):
        """Verifica se o BauhausButton pode ser importado"""
        from src.ui.bauhaus_components import BauhausButton
        assert BauhausButton is not None
    
    def test_secondary_button_import(self):
        """Verifica se o BauhausSecondaryButton pode ser importado"""
        from src.ui.bauhaus_components import BauhausSecondaryButton
        assert BauhausSecondaryButton is not None
    
    def test_danger_button_import(self):
        """Verifica se o BauhausDangerButton pode ser importado"""
        from src.ui.bauhaus_components import BauhausDangerButton
        assert BauhausDangerButton is not None
    
    def test_highlight_button_import(self):
        """Verifica se o BauhausHighlightButton pode ser importado"""
        from src.ui.bauhaus_components import BauhausHighlightButton
        assert BauhausHighlightButton is not None
    
    def test_ghost_button_import(self):
        """Verifica se o BauhausGhostButton pode ser importado"""
        from src.ui.bauhaus_components import BauhausGhostButton
        assert BauhausGhostButton is not None
    
    def test_line_edit_import(self):
        """Verifica se o BauhausLineEdit pode ser importado"""
        from src.ui.bauhaus_components import BauhausLineEdit
        assert BauhausLineEdit is not None
    
    def test_text_edit_import(self):
        """Verifica se o BauhausTextEdit pode ser importado"""
        from src.ui.bauhaus_components import BauhausTextEdit
        assert BauhausTextEdit is not None
    
    def test_combo_box_import(self):
        """Verifica se o BauhausComboBox pode ser importado"""
        from src.ui.bauhaus_components import BauhausComboBox
        assert BauhausComboBox is not None
    
    def test_card_import(self):
        """Verifica se o BauhausCard pode ser importado"""
        from src.ui.bauhaus_components import BauhausCard
        assert BauhausCard is not None
    
    def test_stat_card_import(self):
        """Verifica se o BauhausStatCard pode ser importado"""
        from src.ui.bauhaus_components import BauhausStatCard
        assert BauhausStatCard is not None
    
    def test_page_title_import(self):
        """Verifica se o BauhausPageTitle pode ser importado"""
        from src.ui.bauhaus_components import BauhausPageTitle
        assert BauhausPageTitle is not None
    
    def test_badge_import(self):
        """Verifica se o BauhausBadge pode ser importado"""
        from src.ui.bauhaus_components import BauhausBadge
        assert BauhausBadge is not None
    
    def test_container_import(self):
        """Verifica se o BauhausContainer pode ser importado"""
        from src.ui.bauhaus_components import BauhausContainer
        assert BauhausContainer is not None
    
    def test_form_field_import(self):
        """Verifica se o BauhausFormField pode ser importado"""
        from src.ui.bauhaus_components import BauhausFormField
        assert BauhausFormField is not None


class TestBauhausIntegration:
    """Testes de integração do design system"""
    
    def test_main_window_uses_bauhaus_theme(self):
        """Verifica se MainWindow usa o tema Bauhaus"""
        from src.ui.main_window import MainWindow
        import inspect
        source = inspect.getsource(MainWindow.apply_stylesheet)
        assert "get_bauhaus_stylesheet" in source
    
    def test_tokens_and_theme_consistency(self):
        """Verifica se tokens e tema são consistentes"""
        from config.bauhaus_tokens import BAUHAUS_PALETTE
        from config.bauhaus_theme import get_bauhaus_stylesheet
        
        stylesheet = get_bauhaus_stylesheet()
        
        # Verificar se as cores dos tokens aparecem no stylesheet
        for color_name, color_value in BAUHAUS_PALETTE.items():
            # Nem todas as cores precisam estar no stylesheet, mas as principais sim
            if color_name in ["black", "white", "blue", "red", "yellow"]:
                assert color_value in stylesheet, f"Cor {color_name} ({color_value}) não encontrada no stylesheet"


class TestBauhausDocumentation:
    """Testes para documentação"""
    
    def test_design_system_documentation_exists(self):
        """Verifica se a documentação do design system existe"""
        doc_path = Path(__file__).parent.parent / "BAUHAUS_DESIGN_SYSTEM.md"
        assert doc_path.exists(), "Documentação do design system não encontrada"
    
    def test_design_system_documentation_has_content(self):
        """Verifica se a documentação tem conteúdo"""
        doc_path = Path(__file__).parent.parent / "BAUHAUS_DESIGN_SYSTEM.md"
        content = doc_path.read_text()
        assert len(content) > 100
        assert "Bauhaus Moderno" in content
        assert "Design System" in content


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])
