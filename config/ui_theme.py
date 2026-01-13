"""
Central UI theme tokens and helpers.
"""

PALETTE = {
    "background": "#F4EFE9",
    "background_alt": "#EEE5D9",
    "surface": "#FFFFFF",
    "surface_alt": "#F7F2EA",
    "sidebar": "#0E1116",
    "sidebar_edge": "#141823",
    "border": "#D6C9BC",
    "text": "#1B1A17",
    "text_muted": "#5B544C",
    "accent": "#0E7C7B",
    "accent_hover": "#0A5C5B",
    "accent_pressed": "#084645",
    "accent_text": "#F7F1EA",
    "danger": "#E03A3E",
    "danger_hover": "#C63236",
    "warning": "#F1A208",
    "success": "#2E8B57",
    "info": "#2F6FD0",
    "alert_surface": "#FFF1EF",
}

SEVERITY_COLORS = {
    "low": "#2F6FD0",
    "medium": "#F1A208",
    "high": "#E03A3E",
    "critical": "#9B1B30",
}

STATUS_COLORS = {
    "unreviewed": "#F1A208",
    "pending": "#F1A208",
    "real": "#2E8B57",
    "false_positive": "#E03A3E",
    "active": "#E03A3E",
    "acknowledged": "#2E8B57",
}


def color_for_severity(severity: str) -> str:
    if not severity:
        return SEVERITY_COLORS["low"]
    return SEVERITY_COLORS.get(severity.lower(), SEVERITY_COLORS["low"])


def color_for_status(status: str) -> str:
    if not status:
        return STATUS_COLORS["unreviewed"]
    key = status.strip().lower().replace(" ", "_")
    return STATUS_COLORS.get(key, STATUS_COLORS["unreviewed"])


def contrast_text(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return PALETTE["text"]
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return PALETTE["accent_text"] if luminance < 0.62 else PALETTE["text"]


def get_app_stylesheet() -> str:
    return f"""
    * {{
        font-family: "Space Grotesk", "Bahnschrift", "Segoe UI", Arial;
        font-size: 11.5pt;
        color: {PALETTE['text']};
    }}
    QMainWindow {{
        background: {PALETTE['background']};
    }}
    QWidget#AppRoot {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {PALETTE['background']}, stop:1 {PALETTE['background_alt']});
    }}
    QFrame#Sidebar {{
        background-color: {PALETTE['sidebar']};
        min-width: 210px;
        max-width: 240px;
        border-right: 1px solid {PALETTE['sidebar_edge']};
    }}
    QLabel#BrandLabel {{
        color: {PALETTE['accent_text']};
        font-size: 18pt;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}
    QFrame#TopBar {{
        background-color: {PALETTE['surface_alt']};
        border: 1px solid {PALETTE['border']};
    }}
    QLabel#PageTitle {{
        font-size: 17pt;
        font-weight: 700;
        color: {PALETTE['text']};
    }}
    QLabel#UserLabel {{
        color: {PALETTE['text_muted']};
    }}
    QFrame#ContentFrame {{
        background: transparent;
    }}
    QPushButton#NavButton {{
        text-align: left;
        background: transparent;
        color: {PALETTE['accent_text']};
        padding: 10px 12px;
        border: 1px solid transparent;
        font-weight: 600;
    }}
    QPushButton#NavButton:hover {{
        background-color: {PALETTE['sidebar_edge']};
        border: 1px solid {PALETTE['sidebar_edge']};
    }}
    QPushButton#NavButton:checked {{
        background-color: {PALETTE['accent']};
        color: {PALETTE['accent_text']};
    }}
    QPushButton#NavButton[alert="true"] {{
        background-color: {PALETTE['danger']};
        color: {PALETTE['accent_text']};
        border: 1px solid {PALETTE['danger_hover']};
    }}
    QPushButton#NavButton[alert="true"]:hover {{
        background-color: {PALETTE['danger_hover']};
    }}
    QPushButton#NavButtonDanger {{
        text-align: left;
        background: transparent;
        color: #F1B7B7;
        padding: 10px 12px;
        border: 1px solid transparent;
        font-weight: 600;
    }}
    QPushButton#NavButtonDanger:hover {{
        background-color: {PALETTE['danger']};
        color: {PALETTE['accent_text']};
    }}
    QPushButton {{
        background-color: {PALETTE['accent']};
        color: {PALETTE['accent_text']};
        border: 1px solid {PALETTE['sidebar']};
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {PALETTE['accent_hover']};
    }}
    QPushButton:pressed {{
        background-color: {PALETTE['accent_pressed']};
    }}
    QPushButton#DangerButton {{
        background-color: {PALETTE['danger']};
        color: {PALETTE['accent_text']};
        border: 1px solid {PALETTE['danger_hover']};
    }}
    QPushButton#DangerButton:hover {{
        background-color: {PALETTE['danger_hover']};
    }}
    QPushButton#SuccessButton {{
        background-color: {PALETTE['success']};
        color: {PALETTE['accent_text']};
        border: 1px solid #1F6B43;
    }}
    QPushButton#SuccessButton:hover {{
        background-color: #256E48;
    }}
    QPushButton#GhostButton {{
        background-color: transparent;
        color: {PALETTE['text']};
        border: 1px solid {PALETTE['border']};
    }}
    QPushButton#GhostButton:hover {{
        background-color: {PALETTE['surface_alt']};
    }}
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QTabWidget::pane, QTableWidget {{
        border: 1px solid {PALETTE['border']};
        padding: 6px 8px;
        background-color: {PALETTE['surface']};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 2px solid {PALETTE['accent']};
        background-color: {PALETTE['surface']};
    }}
    QTabBar::tab {{
        background: {PALETTE['surface_alt']};
        color: {PALETTE['text']};
        padding: 8px 14px;
        border: 1px solid {PALETTE['border']};
        margin-right: 4px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: {PALETTE['surface']};
        border-bottom: 1px solid {PALETTE['surface']};
    }}
    QGroupBox {{
        border: 1px solid {PALETTE['border']};
        margin-top: 12px;
        background: {PALETTE['surface']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
        color: {PALETTE['text']};
        font-weight: 600;
    }}
    QHeaderView::section {{
        background-color: {PALETTE['sidebar_edge']};
        border: 1px solid {PALETTE['sidebar_edge']};
        padding: 6px 8px;
        font-weight: 700;
        color: {PALETTE['accent_text']};
    }}
    QTableWidget {{
        gridline-color: {PALETTE['border']};
    }}
    QTableWidget::item:selected {{
        background-color: #E7DCCB;
        color: {PALETTE['text']};
    }}
    QProgressBar {{
        border: 1px solid {PALETTE['border']};
        text-align: center;
        background: {PALETTE['surface']};
    }}
    QProgressBar::chunk {{
        background-color: {PALETTE['accent']};
    }}
    QFrame#StatCard {{
        background-color: {PALETTE['surface']};
        border: 1px solid {PALETTE['border']};
        padding: 14px;
    }}
    QFrame#StatCard[alert="true"] {{
        background-color: {PALETTE['alert_surface']};
        border: 2px solid {PALETTE['danger']};
    }}
    QFrame#StatCard QLabel#StatTitle {{
        color: {PALETTE['text_muted']};
        font-weight: 600;
    }}
    QFrame#StatCard QLabel#StatValue {{
        color: {PALETTE['accent']};
        font-size: 22pt;
        font-weight: 700;
    }}
    QFrame#StatCard[alert="true"] QLabel#StatValue {{
        color: {PALETTE['danger']};
    }}
    QFrame#LoginCard {{
        background-color: {PALETTE['surface']};
        border: 1px solid {PALETTE['border']};
    }}
    QLabel#LoginTitle {{
        font-size: 20pt;
        font-weight: 700;
        color: {PALETTE['text']};
    }}
    QLabel#LoginSubtitle {{
        color: {PALETTE['text_muted']};
    }}
    QTabWidget#LoginTabs::pane {{
        border: 1px solid {PALETTE['border']};
    }}
    QFrame#LoginCard QLabel {{
        font-size: 11.5pt;
    }}
    QFrame#LiveViewHeader {{
        background-color: {PALETTE['surface_alt']};
        border: 1px solid {PALETTE['border']};
    }}
    QFrame#LiveViewHeader QLabel {{
        font-size: 12pt;
        font-weight: 600;
    }}
    QFrame#LiveViewHeader QPushButton {{
        min-width: 140px;
    }}
    QStatusBar {{
        background: {PALETTE['background']};
        border-top: 1px solid {PALETTE['border']};
        color: {PALETTE['text']};
    }}
    """
