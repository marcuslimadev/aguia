"""
Bauhaus Moderno Design System - Design Tokens
Sistema de design geométrico, funcional e moderno para SaaS
"""

# ============================================================================
# 1. PALETA PRIMÁRIA - Bauhaus Moderno
# ============================================================================

BAUHAUS_PALETTE = {
    # Estrutural
    "black": "#0E0E0E",           # Preto estrutural
    "white": "#FFFFFF",            # Branco
    "light_gray": "#F2F2F2",        # Cinza claro
    "medium_gray": "#D6D6D6",       # Cinza médio
    "dark_gray": "#3A3A3A",         # Cinza escuro
    
    # Cores Bauhaus
    "blue": "#005BFF",              # Azul Bauhaus
    "red": "#E10600",               # Vermelho Bauhaus
    "yellow": "#FFD600",            # Amarelo Bauhaus
    
    # Variações de Azul
    "blue_hover": "#0047CC",
    "blue_active": "#003399",
    
    # Variações de Vermelho
    "red_hover": "#B80000",
    
    # Variações de Amarelo
    "yellow_hover": "#E6C000",
}

# ============================================================================
# 2. RAIO DE BORDA (Border Radius) - Bauhaus Moderno
# ============================================================================

BORDER_RADIUS = {
    "buttons": "8px",
    "inputs": "10px",
    "cards": "16px",
    "modals": "20px",
    "avatars": "50%",
}

# ============================================================================
# 3. GRID E ESPAÇAMENTO - Sistema Base 4px/8px
# ============================================================================

SPACING = {
    "xs": "4px",      # Extra small
    "sm": "8px",      # Small
    "md": "16px",     # Medium
    "lg": "24px",     # Large
    "xl": "32px",     # Extra large
}

# ============================================================================
# 4. TIPOGRAFIA
# ============================================================================

TYPOGRAPHY = {
    "font_family": '"Inter", "Segoe UI", "Helvetica Neue", sans-serif',
    "font_family_mono": '"Fira Code", "Courier New", monospace',
    
    # Tamanhos
    "size_xs": "11px",
    "size_sm": "12px",
    "size_base": "14px",
    "size_lg": "16px",
    "size_xl": "18px",
    "size_2xl": "20px",
    "size_3xl": "24px",
    "size_4xl": "32px",
    
    # Pesos
    "weight_normal": "400",
    "weight_medium": "500",
    "weight_semibold": "600",
    "weight_bold": "700",
}

# ============================================================================
# 5. COMPONENTES - BOTÕES
# ============================================================================

BUTTONS = {
    "primary": {
        "background": BAUHAUS_PALETTE["blue"],
        "text": BAUHAUS_PALETTE["white"],
        "hover": BAUHAUS_PALETTE["blue_hover"],
        "active": BAUHAUS_PALETTE["blue_active"],
        "radius": BORDER_RADIUS["buttons"],
        "height": "44px",
        "padding": "12px 24px",
        "font_weight": TYPOGRAPHY["weight_semibold"],
    },
    "secondary": {
        "background": BAUHAUS_PALETTE["white"],
        "text": BAUHAUS_PALETTE["black"],
        "border": f"2px solid {BAUHAUS_PALETTE['black']}",
        "hover_background": BAUHAUS_PALETTE["light_gray"],
        "radius": BORDER_RADIUS["buttons"],
        "height": "44px",
        "padding": "12px 24px",
        "font_weight": TYPOGRAPHY["weight_semibold"],
    },
    "destructive": {
        "background": BAUHAUS_PALETTE["red"],
        "text": BAUHAUS_PALETTE["white"],
        "hover": BAUHAUS_PALETTE["red_hover"],
        "radius": BORDER_RADIUS["buttons"],
        "height": "44px",
        "padding": "12px 24px",
        "font_weight": TYPOGRAPHY["weight_semibold"],
    },
    "highlight": {
        "background": BAUHAUS_PALETTE["yellow"],
        "text": BAUHAUS_PALETTE["black"],
        "hover": BAUHAUS_PALETTE["yellow_hover"],
        "radius": BORDER_RADIUS["buttons"],
        "height": "44px",
        "padding": "12px 24px",
        "font_weight": TYPOGRAPHY["weight_semibold"],
    },
}

# ============================================================================
# 6. COMPONENTES - INPUTS
# ============================================================================

INPUTS = {
    "background": BAUHAUS_PALETTE["white"],
    "text": BAUHAUS_PALETTE["black"],
    "border": f"2px solid {BAUHAUS_PALETTE['medium_gray']}",
    "radius": BORDER_RADIUS["inputs"],
    "height": "44px",
    "padding": "12px 14px",
    "focus_border": f"2px solid {BAUHAUS_PALETTE['blue']}",
    "focus_shadow": "0 0 0 3px rgba(0, 91, 255, 0.15)",
}

# ============================================================================
# 7. COMPONENTES - CARDS
# ============================================================================

CARDS = {
    "background": BAUHAUS_PALETTE["white"],
    "border": f"1px solid {BAUHAUS_PALETTE['medium_gray']}",
    "radius": BORDER_RADIUS["cards"],
    "padding": SPACING["lg"],
    "gap": SPACING["lg"],
    "shadow": "none",  # Bauhaus é plano e limpo
}

# ============================================================================
# 8. COMPONENTES - BADGES (Status)
# ============================================================================

BADGES = {
    "success": {
        "background": "#00A859",
        "text": BAUHAUS_PALETTE["white"],
        "radius": "999px",
    },
    "error": {
        "background": BAUHAUS_PALETTE["red"],
        "text": BAUHAUS_PALETTE["white"],
        "radius": "999px",
    },
    "warning": {
        "background": BAUHAUS_PALETTE["yellow"],
        "text": BAUHAUS_PALETTE["black"],
        "radius": "999px",
    },
    "info": {
        "background": BAUHAUS_PALETTE["blue"],
        "text": BAUHAUS_PALETTE["white"],
        "radius": "999px",
    },
}

# ============================================================================
# 9. COMPONENTES - TABS
# ============================================================================

TABS = {
    "inactive_text": BAUHAUS_PALETTE["dark_gray"],
    "active_text": BAUHAUS_PALETTE["black"],
    "active_border": f"3px solid {BAUHAUS_PALETTE['blue']}",
    "background": "transparent",
}

# ============================================================================
# 10. COMPONENTES - MODAIS
# ============================================================================

MODALS = {
    "background": BAUHAUS_PALETTE["white"],
    "radius": BORDER_RADIUS["modals"],
    "padding": "32px",
    "overlay": "rgba(0, 0, 0, 0.6)",
}

# ============================================================================
# 11. COMPONENTES - NAVBAR / SIDEBAR
# ============================================================================

NAVBAR = {
    "background": BAUHAUS_PALETTE["black"],
    "text": BAUHAUS_PALETTE["white"],
    "active_item": BAUHAUS_PALETTE["blue"],
    "hover": "#1A1A1A",
}

# ============================================================================
# 12. COMPONENTES - TABELAS
# ============================================================================

TABLES = {
    "header_background": BAUHAUS_PALETTE["light_gray"],
    "header_text": BAUHAUS_PALETTE["black"],
    "row_border": f"1px solid {BAUHAUS_PALETTE['medium_gray']}",
    "active_row_background": "rgba(0, 91, 255, 0.05)",
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_button_style(button_type: str = "primary") -> dict:
    """Retorna o estilo completo para um tipo de botão"""
    return BUTTONS.get(button_type, BUTTONS["primary"])


def get_badge_style(badge_type: str = "info") -> dict:
    """Retorna o estilo completo para um tipo de badge"""
    return BADGES.get(badge_type, BADGES["info"])


def get_spacing(size: str = "md") -> str:
    """Retorna o valor de espaçamento"""
    return SPACING.get(size, SPACING["md"])


def get_border_radius(element: str = "cards") -> str:
    """Retorna o raio de borda para um elemento"""
    return BORDER_RADIUS.get(element, BORDER_RADIUS["cards"])
