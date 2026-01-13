"""
Bauhaus Design System
Sistema de cores, tipografia e componentes baseado nos principios Bauhaus
Forma segue funcao, geometria pura, alto contraste
"""

# ============================================================================
# CORES PRIMARIAS BAUHAUS (apenas 5 cores-mae)
# ============================================================================

# Estruturais
BLACK_BAUHAUS = "#0B0B0B"
WHITE_BAUHAUS = "#F5F5F5"

# Primarias
RED_BAUHAUS = "#E10600"
BLUE_BAUHAUS = "#0057FF"
YELLOW_BAUHAUS = "#FFD600"

# ============================================================================
# ESCALA FUNCIONAL (Neutros) - 95% da interface
# ============================================================================

OFF_WHITE = "#FAFAFA"          # Fundo principal
LIGHT_GRAY = "#ECECEC"         # Fundo secundario
MID_GRAY = "#D1D1D1"           # Linhas e divisoes
DARK_GRAY = "#4F4F4F"          # Texto secundario
NEAR_BLACK = "#121212"         # Texto principal

# ============================================================================
# CORES SEMANTICAS (usar apenas quando necessario)
# ============================================================================

GREEN_BAUHAUS = "#00A859"      # Sucesso
# YELLOW_BAUHAUS ja definido    # Alerta
# RED_BAUHAUS ja definido       # Erro
# BLUE_BAUHAUS ja definido      # Info

# ============================================================================
# TIPOGRAFIA (Fontes geometricas)
# ============================================================================

FONT_FAMILY_UI = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
FONT_FAMILY_MONO = "JetBrains Mono, Consolas, monospace"
FONT_FAMILY_ALT = "Space Grotesk, Inter, sans-serif"

# Tamanhos em px (multiplos de 4)
FONT_SIZE_SMALL = 12
FONT_SIZE_BASE = 14
FONT_SIZE_MEDIUM = 16
FONT_SIZE_LARGE = 20
FONT_SIZE_XL = 24
FONT_SIZE_XXL = 32
FONT_SIZE_HUGE = 48

# ============================================================================
# ESPACAMENTO (Grid de 8px)
# ============================================================================

SPACE_1 = 4    # 0.5 unidade
SPACE_2 = 8    # 1 unidade
SPACE_3 = 12   # 1.5 unidades
SPACE_4 = 16   # 2 unidades
SPACE_5 = 20   # 2.5 unidades
SPACE_6 = 24   # 3 unidades
SPACE_8 = 32   # 4 unidades
SPACE_10 = 40  # 5 unidades
SPACE_12 = 48  # 6 unidades
SPACE_16 = 64  # 8 unidades

# ============================================================================
# GEOMETRIA (Formas puras)
# ============================================================================

BORDER_RADIUS = 0              # Cantos retos sempre
BORDER_WIDTH = 2               # Bordas visiveis
ICON_STROKE = 2                # Stroke de icones

# ============================================================================
# COMPONENTES (Padroes visuais)
# ============================================================================

def get_button_primary_style():
    """Botao primario - Azul Bauhaus"""
    return f"""
        QPushButton {{
            background-color: {BLUE_BAUHAUS};
            color: {WHITE_BAUHAUS};
            border: none;
            border-radius: {BORDER_RADIUS}px;
            padding: {SPACE_3}px {SPACE_6}px;
            font-family: {FONT_FAMILY_UI};
            font-size: {FONT_SIZE_BASE}px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        QPushButton:hover {{
            background-color: #003FCC;
        }}
        QPushButton:pressed {{
            background-color: #002999;
        }}
        QPushButton:disabled {{
            background-color: {MID_GRAY};
            color: {DARK_GRAY};
        }}
    """

def get_button_secondary_style():
    """Botao secundario - Outline preto"""
    return f"""
        QPushButton {{
            background-color: {WHITE_BAUHAUS};
            color: {BLACK_BAUHAUS};
            border: {BORDER_WIDTH}px solid {BLACK_BAUHAUS};
            border-radius: {BORDER_RADIUS}px;
            padding: {SPACE_3}px {SPACE_6}px;
            font-family: {FONT_FAMILY_UI};
            font-size: {FONT_SIZE_BASE}px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        QPushButton:hover {{
            background-color: {LIGHT_GRAY};
        }}
        QPushButton:pressed {{
            background-color: {MID_GRAY};
        }}
        QPushButton:disabled {{
            border-color: {MID_GRAY};
            color: {DARK_GRAY};
        }}
    """

def get_button_destructive_style():
    """Botao destrutivo - Vermelho Bauhaus"""
    return f"""
        QPushButton {{
            background-color: {RED_BAUHAUS};
            color: {WHITE_BAUHAUS};
            border: none;
            border-radius: {BORDER_RADIUS}px;
            padding: {SPACE_3}px {SPACE_6}px;
            font-family: {FONT_FAMILY_UI};
            font-size: {FONT_SIZE_BASE}px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        QPushButton:hover {{
            background-color: #B40500;
        }}
        QPushButton:pressed {{
            background-color: #8A0400;
        }}
    """

def get_input_style():
    """Campo de input - Geometrico puro"""
    return f"""
        QLineEdit {{
            background-color: {WHITE_BAUHAUS};
            color: {NEAR_BLACK};
            border: {BORDER_WIDTH}px solid {MID_GRAY};
            border-radius: {BORDER_RADIUS}px;
            padding: {SPACE_3}px {SPACE_4}px;
            font-family: {FONT_FAMILY_UI};
            font-size: {FONT_SIZE_BASE}px;
        }}
        QLineEdit:focus {{
            border-color: {BLUE_BAUHAUS};
        }}
        QLineEdit:disabled {{
            background-color: {LIGHT_GRAY};
            color: {DARK_GRAY};
        }}
    """

def get_card_style():
    """Card/Container - Sem sombra, apenas borda"""
    return f"""
        QFrame {{
            background-color: {WHITE_BAUHAUS};
            border: {BORDER_WIDTH}px solid {MID_GRAY};
            border-radius: {BORDER_RADIUS}px;
            padding: {SPACE_6}px;
        }}
    """

def get_label_title_style():
    """Label de titulo - Alto contraste"""
    return f"""
        QLabel {{
            color: {NEAR_BLACK};
            font-family: {FONT_FAMILY_UI};
            font-size: {FONT_SIZE_XXL}px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
    """

def get_label_subtitle_style():
    """Label de subtitulo"""
    return f"""
        QLabel {{
            color: {DARK_GRAY};
            font-family: {FONT_FAMILY_UI};
            font-size: {FONT_SIZE_BASE}px;
            font-weight: 400;
        }}
    """

def get_label_section_style():
    """Label de secao - Uppercase, espacado"""
    return f"""
        QLabel {{
            color: {NEAR_BLACK};
            font-family: {FONT_FAMILY_UI};
            font-size: {FONT_SIZE_SMALL}px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}
    """

def get_table_style():
    """Tabela - Grid rigido"""
    return f"""
        QTableWidget {{
            background-color: {WHITE_BAUHAUS};
            border: {BORDER_WIDTH}px solid {MID_GRAY};
            gridline-color: {MID_GRAY};
            font-family: {FONT_FAMILY_UI};
            font-size: {FONT_SIZE_BASE}px;
        }}
        QTableWidget::item {{
            padding: {SPACE_2}px;
            border-bottom: 1px solid {LIGHT_GRAY};
        }}
        QHeaderView::section {{
            background-color: {NEAR_BLACK};
            color: {WHITE_BAUHAUS};
            padding: {SPACE_3}px;
            border: none;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
    """

def get_tab_style():
    """Tab widget - Geometrico"""
    return f"""
        QTabWidget::pane {{
            border: {BORDER_WIDTH}px solid {MID_GRAY};
            border-radius: {BORDER_RADIUS}px;
        }}
        QTabBar::tab {{
            background-color: {LIGHT_GRAY};
            color: {DARK_GRAY};
            border: {BORDER_WIDTH}px solid {MID_GRAY};
            border-bottom: none;
            padding: {SPACE_3}px {SPACE_6}px;
            font-family: {FONT_FAMILY_UI};
            font-size: {FONT_SIZE_BASE}px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        QTabBar::tab:selected {{
            background-color: {WHITE_BAUHAUS};
            color: {NEAR_BLACK};
            border-bottom: {BORDER_WIDTH}px solid {BLUE_BAUHAUS};
        }}
        QTabBar::tab:hover {{
            background-color: {MID_GRAY};
        }}
    """

def get_status_indicator_style(status="active"):
    """Indicador de status - Circulo geometrico"""
    colors = {
        "active": GREEN_BAUHAUS,
        "warning": YELLOW_BAUHAUS,
        "error": RED_BAUHAUS,
        "info": BLUE_BAUHAUS,
        "inactive": MID_GRAY
    }
    color = colors.get(status, MID_GRAY)
    return f"""
        QLabel {{
            background-color: {color};
            border-radius: 6px;
            min-width: 12px;
            min-height: 12px;
            max-width: 12px;
            max-height: 12px;
        }}
    """

# ============================================================================
# REGRA DE OURO
# ============================================================================
# 95% da interface usa neutros (OFF_WHITE, LIGHT_GRAY, MID_GRAY, DARK_GRAY, NEAR_BLACK)
# 5% usa cores primarias (BLUE_BAUHAUS em botoes de acao, RED_BAUHAUS em alertas)
# Cor so aparece em: botoes de acao, estados ativos, indicadores, graficos
# NUNCA como fundo geral
# ============================================================================
