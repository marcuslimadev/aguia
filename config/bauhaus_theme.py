"""
Bauhaus Moderno Theme - Stylesheet Generator
Gera stylesheet QSS completo com design system Bauhaus
"""

from config.bauhaus_tokens import (
    BAUHAUS_PALETTE, BORDER_RADIUS, SPACING, TYPOGRAPHY,
    BUTTONS, INPUTS, CARDS, BADGES, TABS, MODALS, NAVBAR, TABLES
)


def generate_bauhaus_stylesheet() -> str:
    """Gera o stylesheet QSS completo com design system Bauhaus"""
    
    return f"""
    /* ========================================================================
       BAUHAUS MODERNO - DESIGN SYSTEM
       Geométrico, funcional e moderno para SaaS
       ======================================================================== */
    
    /* ========================================================================
       RESET E DEFAULTS
       ======================================================================== */
    
    * {{
        font-family: {TYPOGRAPHY['font_family']};
        font-size: {TYPOGRAPHY['size_base']};
        color: {BAUHAUS_PALETTE['black']};
        margin: 0;
        padding: 0;
    }}
    
    /* ========================================================================
       JANELA PRINCIPAL
       ======================================================================== */
    
    QMainWindow {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
    }}
    
    QWidget#AppRoot {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
    }}
    
    /* ========================================================================
       SIDEBAR / NAVBAR
       ======================================================================== */
    
    QFrame#Sidebar {{
        background-color: {NAVBAR['background']};
        border-right: 1px solid {BAUHAUS_PALETTE['dark_gray']};
        min-width: 240px;
        max-width: 240px;
    }}
    
    QLabel#BrandLabel {{
        color: {NAVBAR['text']};
        font-size: {TYPOGRAPHY['size_3xl']};
        font-weight: {TYPOGRAPHY['weight_bold']};
        letter-spacing: 0.5px;
        padding: {SPACING['md']};
    }}
    
    /* ========================================================================
       BOTÕES DE NAVEGAÇÃO
       ======================================================================== */
    
    QPushButton#NavButton {{
        text-align: left;
        background-color: transparent;
        color: {NAVBAR['text']};
        padding: {SPACING['sm']} {SPACING['md']};
        border: 1px solid transparent;
        border-radius: {BORDER_RADIUS['buttons']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
        margin: 2px 0;
    }}
    
    QPushButton#NavButton:hover {{
        background-color: {NAVBAR['hover']};
        border: 1px solid {NAVBAR['hover']};
    }}
    
    QPushButton#NavButton:checked {{
        background-color: {NAVBAR['active_item']};
        color: {BAUHAUS_PALETTE['white']};
        border: 1px solid {NAVBAR['active_item']};
    }}
    
    QPushButton#NavButtonDanger {{
        text-align: left;
        background-color: transparent;
        color: #F1B7B7;
        padding: {SPACING['sm']} {SPACING['md']};
        border: 1px solid transparent;
        border-radius: {BORDER_RADIUS['buttons']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
        margin: 2px 0;
    }}
    
    QPushButton#NavButtonDanger:hover {{
        background-color: {BAUHAUS_PALETTE['red']};
        color: {BAUHAUS_PALETTE['white']};
        border: 1px solid {BAUHAUS_PALETTE['red']};
    }}
    
    /* ========================================================================
       BOTÕES GERAIS
       ======================================================================== */
    
    QPushButton {{
        background-color: {BUTTONS['primary']['background']};
        color: {BUTTONS['primary']['text']};
        border: 1px solid {BUTTONS['primary']['background']};
        padding: {BUTTONS['primary']['padding']};
        border-radius: {BUTTONS['primary']['radius']};
        font-weight: {BUTTONS['primary']['font_weight']};
        min-height: {BUTTONS['primary']['height']};
    }}
    
    QPushButton:hover {{
        background-color: {BUTTONS['primary']['hover']};
        border: 1px solid {BUTTONS['primary']['hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {BUTTONS['primary']['active']};
        border: 1px solid {BUTTONS['primary']['active']};
    }}
    
    QPushButton:disabled {{
        background-color: {BAUHAUS_PALETTE['medium_gray']};
        color: {BAUHAUS_PALETTE['dark_gray']};
    }}
    
    /* Botão Secundário */
    QPushButton#SecondaryButton {{
        background-color: {BUTTONS['secondary']['background']};
        color: {BUTTONS['secondary']['text']};
        border: {BUTTONS['secondary']['border']};
        padding: {BUTTONS['secondary']['padding']};
        border-radius: {BUTTONS['secondary']['radius']};
        font-weight: {BUTTONS['secondary']['font_weight']};
        min-height: {BUTTONS['secondary']['height']};
    }}
    
    QPushButton#SecondaryButton:hover {{
        background-color: {BUTTONS['secondary']['hover_background']};
    }}
    
    /* Botão Destrutivo */
    QPushButton#DangerButton {{
        background-color: {BUTTONS['destructive']['background']};
        color: {BUTTONS['destructive']['text']};
        border: 1px solid {BUTTONS['destructive']['background']};
        padding: {BUTTONS['destructive']['padding']};
        border-radius: {BUTTONS['destructive']['radius']};
        font-weight: {BUTTONS['destructive']['font_weight']};
        min-height: {BUTTONS['destructive']['height']};
    }}
    
    QPushButton#DangerButton:hover {{
        background-color: {BUTTONS['destructive']['hover']};
        border: 1px solid {BUTTONS['destructive']['hover']};
    }}
    
    /* Botão de Destaque */
    QPushButton#HighlightButton {{
        background-color: {BUTTONS['highlight']['background']};
        color: {BUTTONS['highlight']['text']};
        border: 1px solid {BUTTONS['highlight']['background']};
        padding: {BUTTONS['highlight']['padding']};
        border-radius: {BUTTONS['highlight']['radius']};
        font-weight: {BUTTONS['highlight']['font_weight']};
        min-height: {BUTTONS['highlight']['height']};
    }}
    
    QPushButton#HighlightButton:hover {{
        background-color: {BUTTONS['highlight']['hover']};
        border: 1px solid {BUTTONS['highlight']['hover']};
    }}
    
    /* Botão Ghost */
    QPushButton#GhostButton {{
        background-color: transparent;
        color: {BAUHAUS_PALETTE['black']};
        border: 1px solid {BAUHAUS_PALETTE['medium_gray']};
        padding: {BUTTONS['primary']['padding']};
        border-radius: {BORDER_RADIUS['buttons']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
    }}
    
    QPushButton#GhostButton:hover {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
        border: 1px solid {BAUHAUS_PALETTE['dark_gray']};
    }}
    
    /* ========================================================================
       INPUTS E CAMPOS DE TEXTO
       ======================================================================== */
    
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {INPUTS['background']};
        color: {INPUTS['text']};
        border: {INPUTS['border']};
        border-radius: {INPUTS['radius']};
        padding: {INPUTS['padding']};
        min-height: {INPUTS['height']};
        font-size: {TYPOGRAPHY['size_base']};
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: {INPUTS['focus_border']};
        box-shadow: {INPUTS['focus_shadow']};
    }}
    
    /* ========================================================================
       COMBOBOX E SPINBOX
       ======================================================================== */
    
    QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {INPUTS['background']};
        color: {INPUTS['text']};
        border: {INPUTS['border']};
        border-radius: {INPUTS['radius']};
        padding: {INPUTS['padding']};
        min-height: {INPUTS['height']};
    }}
    
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: {INPUTS['focus_border']};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border: none;
    }}
    
    /* ========================================================================
       CARDS E FRAMES
       ======================================================================== */
    
    QFrame#Card {{
        background-color: {CARDS['background']};
        border: {CARDS['border']};
        border-radius: {CARDS['radius']};
        padding: {CARDS['padding']};
    }}
    
    QFrame#StatCard {{
        background-color: {CARDS['background']};
        border: {CARDS['border']};
        border-radius: {CARDS['radius']};
        padding: {CARDS['padding']};
    }}
    
    QFrame#StatCard[alert="true"] {{
        background-color: rgba(225, 6, 0, 0.05);
        border: 2px solid {BAUHAUS_PALETTE['red']};
    }}
    
    QFrame#LoginCard {{
        background-color: {CARDS['background']};
        border: {CARDS['border']};
        border-radius: {CARDS['radius']};
        padding: {CARDS['padding']};
    }}
    
    /* ========================================================================
       LABELS E TEXTO
       ======================================================================== */
    
    QLabel {{
        color: {BAUHAUS_PALETTE['black']};
    }}
    
    QLabel#PageTitle {{
        font-size: {TYPOGRAPHY['size_3xl']};
        font-weight: {TYPOGRAPHY['weight_bold']};
        color: {BAUHAUS_PALETTE['black']};
    }}
    
    QLabel#SectionTitle {{
        font-size: {TYPOGRAPHY['size_2xl']};
        font-weight: {TYPOGRAPHY['weight_bold']};
        color: {BAUHAUS_PALETTE['black']};
    }}
    
    QLabel#StatTitle {{
        color: {BAUHAUS_PALETTE['dark_gray']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
        font-size: {TYPOGRAPHY['size_sm']};
    }}
    
    QLabel#StatValue {{
        color: {BAUHAUS_PALETTE['blue']};
        font-size: {TYPOGRAPHY['size_3xl']};
        font-weight: {TYPOGRAPHY['weight_bold']};
    }}
    
    QLabel#StatCard[alert="true"] QLabel#StatValue {{
        color: {BAUHAUS_PALETTE['red']};
    }}
    
    /* ========================================================================
       TABS
       ======================================================================== */
    
    QTabWidget::pane {{
        border: {CARDS['border']};
        border-radius: {BORDER_RADIUS['cards']};
    }}
    
    QTabBar::tab {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
        color: {TABS['inactive_text']};
        padding: {SPACING['sm']} {SPACING['md']};
        border: 1px solid {BAUHAUS_PALETTE['medium_gray']};
        border-radius: {BORDER_RADIUS['buttons']} {BORDER_RADIUS['buttons']} 0 0;
        margin-right: 2px;
        font-weight: {TYPOGRAPHY['weight_semibold']};
    }}
    
    QTabBar::tab:selected {{
        background-color: {BAUHAUS_PALETTE['white']};
        color: {TABS['active_text']};
        border-bottom: {TABS['active_border']};
    }}
    
    QTabBar::tab:hover {{
        background-color: {BAUHAUS_PALETTE['white']};
    }}
    
    /* ========================================================================
       TABELAS
       ======================================================================== */
    
    QTableWidget {{
        background-color: {BAUHAUS_PALETTE['white']};
        border: {CARDS['border']};
        border-radius: {CARDS['radius']};
        gridline-color: {TABLES['row_border']};
    }}
    
    QHeaderView::section {{
        background-color: {TABLES['header_background']};
        color: {TABLES['header_text']};
        padding: {SPACING['sm']} {SPACING['md']};
        border: {TABLES['row_border']};
        font-weight: {TYPOGRAPHY['weight_bold']};
        border-radius: 0;
    }}
    
    QTableWidget::item {{
        padding: {SPACING['sm']} {SPACING['md']};
        border: {TABLES['row_border']};
    }}
    
    QTableWidget::item:selected {{
        background-color: {TABLES['active_row_background']};
        color: {BAUHAUS_PALETTE['black']};
    }}
    
    /* ========================================================================
       SCROLLBARS
       ======================================================================== */
    
    QScrollBar:vertical {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {BAUHAUS_PALETTE['medium_gray']};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {BAUHAUS_PALETTE['dark_gray']};
    }}
    
    QScrollBar:horizontal {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
        height: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {BAUHAUS_PALETTE['medium_gray']};
        border-radius: 6px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {BAUHAUS_PALETTE['dark_gray']};
    }}
    
    /* ========================================================================
       PROGRESS BAR
       ======================================================================== */
    
    QProgressBar {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
        border: {CARDS['border']};
        border-radius: {BORDER_RADIUS['buttons']};
        padding: 2px;
        text-align: center;
        color: {BAUHAUS_PALETTE['black']};
    }}
    
    QProgressBar::chunk {{
        background-color: {BAUHAUS_PALETTE['blue']};
        border-radius: {BORDER_RADIUS['buttons']};
    }}
    
    /* ========================================================================
       GROUPBOX
       ======================================================================== */
    
    QGroupBox {{
        border: {CARDS['border']};
        border-radius: {CARDS['radius']};
        margin-top: {SPACING['md']};
        padding-top: {SPACING['md']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
        color: {BAUHAUS_PALETTE['black']};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: {SPACING['md']};
        padding: 0 {SPACING['sm']};
        color: {BAUHAUS_PALETTE['black']};
        font-weight: {TYPOGRAPHY['weight_bold']};
    }}
    
    /* ========================================================================
       STATUSBAR
       ======================================================================== */
    
    QStatusBar {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
        border-top: 1px solid {BAUHAUS_PALETTE['medium_gray']};
        color: {BAUHAUS_PALETTE['black']};
        padding: {SPACING['sm']};
    }}
    
    /* ========================================================================
       BADGES
       ======================================================================== */
    
    QLabel#BadgeSuccess {{
        background-color: {BADGES['success']['background']};
        color: {BADGES['success']['text']};
        padding: 4px 12px;
        border-radius: {BADGES['success']['radius']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
    }}
    
    QLabel#BadgeError {{
        background-color: {BADGES['error']['background']};
        color: {BADGES['error']['text']};
        padding: 4px 12px;
        border-radius: {BADGES['error']['radius']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
    }}
    
    QLabel#BadgeWarning {{
        background-color: {BADGES['warning']['background']};
        color: {BADGES['warning']['text']};
        padding: 4px 12px;
        border-radius: {BADGES['warning']['radius']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
    }}
    
    QLabel#BadgeInfo {{
        background-color: {BADGES['info']['background']};
        color: {BADGES['info']['text']};
        padding: 4px 12px;
        border-radius: {BADGES['info']['radius']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
    }}
    
    /* ========================================================================
       DIALOGS
       ======================================================================== */
    
    QDialog {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
    }}
    
    QMessageBox {{
        background-color: {BAUHAUS_PALETTE['light_gray']};
    }}
    
    QMessageBox QLabel {{
        color: {BAUHAUS_PALETTE['black']};
    }}
    
    /* ========================================================================
       MISC
       ======================================================================== */
    
    QFrame#TopBar {{
        background-color: {BAUHAUS_PALETTE['white']};
        border-bottom: 1px solid {BAUHAUS_PALETTE['medium_gray']};
    }}
    
    QFrame#ContentFrame {{
        background-color: transparent;
    }}
    
    QFrame#LiveViewHeader {{
        background-color: {BAUHAUS_PALETTE['white']};
        border-bottom: 1px solid {BAUHAUS_PALETTE['medium_gray']};
    }}
    
    QFrame#LiveViewHeader QLabel {{
        font-size: {TYPOGRAPHY['size_lg']};
        font-weight: {TYPOGRAPHY['weight_semibold']};
    }}
    
    QFrame#LiveViewHeader QPushButton {{
        min-width: 140px;
    }}
    """


def get_minimal_black_stylesheet() -> str:
    """Tema minimalista: fundo #cecaca, fontes maiores, cantos arredondados 3px"""
    return """
    /* MINIMAL THEME - Fundo principal #cecaca, bordas #333, fontes maiores */
    QWidget {
        background-color: #cecaca;
        color: #000000;
        font-family: "Consolas", "Monaco", "Courier New", monospace;
        font-size: 16px;
        border: 1px solid #333333;
        border-radius: 3px;
    }
    
    QMainWindow {
        background-color: #cecaca;
        border: none;
        border-radius: 0px;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #666666;
        color: #ffffff;
        border: 1px solid #333333;
        border-radius: 3px;
        padding: 10px 18px;
        min-height: 36px;
        font-size: 16px;
    }
    
    QPushButton:hover {
        background-color: #808080;
        border: 1px solid #000000;
    }
    
    QPushButton:pressed {
        background-color: #4d4d4d;
    }
    
    QPushButton:disabled {
        background-color: #999999;
        color: #666666;
        border: 1px solid #333333;
    }
    
    /* Inputs */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 1px solid #333333;
        border-radius: 3px;
        padding: 8px;
        min-height: 32px;
        font-size: 16px;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #000000;
    }
    
    /* Tables */
    QTableWidget {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #333333;
        border-radius: 3px;
        gridline-color: #333333;
        font-size: 15px;
    }
    
    QTableWidget::item {
        color: #000000;
        border-bottom: 1px solid #333333;
        padding: 6px;
    }
    
    QTableWidget::item:selected {
        background-color: #999999;
    }
    
    QHeaderView::section {
        background-color: #666666;
        color: #ffffff;
        border: 1px solid #333333;
        border-radius: 3px;
        padding: 8px;
        font-size: 15px;
        font-weight: bold;
    }
    
    /* Tabs */
    QTabWidget::pane {
        background-color: #ffffff;
        border: 1px solid #333333;
        border-radius: 3px;
    }
    
    QTabBar::tab {
        background-color: #999999;
        color: #000000;
        border: 1px solid #333333;
        border-radius: 3px;
        padding: 10px 18px;
        font-size: 16px;
    }
    
    QTabBar::tab:selected {
        background-color: #666666;
        color: #ffffff;
        border: 2px solid #000000;
    }
    
    QTabBar::tab:hover {
        background-color: #808080;
        color: #ffffff;
    }
    
    /* Labels */
    QLabel {
        color: #000000;
        border: none;
        background: transparent;
        border-radius: 0px;
        font-size: 16px;
        font-weight: bold;
    }
    
    /* Progress Bar */
    QProgressBar {
        border: 1px solid #333333;
        border-radius: 3px;
        background-color: #ffffff;
        text-align: center;
        height: 4px;
    }
    
    QProgressBar::chunk {
        background-color: #666666;
        border-radius: 2px;
    }
    
    /* Frames/Cards */
    QFrame {
        border: 1px solid #333333;
        border-radius: 3px;
        background-color: #ffffff;
    }
    
    /* ScrollBars */
    QScrollBar:vertical {
        background: #ffffff;
        width: 14px;
        border: 1px solid #333333;
        border-radius: 3px;
    }
    
    QScrollBar::handle:vertical {
        background: #666666;
        border-radius: 3px;
        min-height: 24px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: #333333;
    }
    
    QScrollBar:horizontal {
        background: #ffffff;
        height: 14px;
        border: 1px solid #333333;
        border-radius: 3px;
    }
    
    QScrollBar::handle:horizontal {
        background: #666666;
        border-radius: 3px;
        min-width: 24px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background: #333333;
    }
    
    /* Status Labels for inline feedback */
    QLabel[feedbackType="success"] {
        color: #000000;
        background-color: #b3e6b3;
        border: 1px solid #333333;
        border-radius: 3px;
        padding: 10px;
        font-size: 15px;
    }
    
    QLabel[feedbackType="error"] {
        color: #000000;
        background-color: #ffb3b3;
        border: 1px solid #333333;
        border-radius: 3px;
        padding: 10px;
        font-size: 15px;
    }
    
    QLabel[feedbackType="info"] {
        color: #000000;
        background-color: #b3d9ff;
        border: 1px solid #333333;
        border-radius: 3px;
        padding: 10px;
        font-size: 15px;
    }
    """

def get_bauhaus_stylesheet() -> str:
    """Retorna o stylesheet Bauhaus completo"""
    return generate_bauhaus_stylesheet()
