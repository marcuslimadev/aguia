"""
Bauhaus Moderno - Componentes Reutilizáveis
Componentes de UI padrão seguindo design system Bauhaus
"""

from PySide6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QFrame, QVBoxLayout, QHBoxLayout,
    QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from config.bauhaus_tokens import (
    BAUHAUS_PALETTE, BORDER_RADIUS, SPACING, TYPOGRAPHY,
    BUTTONS, INPUTS, BADGES
)


# ============================================================================
# BOTÕES
# ============================================================================

class BauhausButton(QPushButton):
    """Botão primário Bauhaus"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("BauhausButton")
        self.setup_style()
    
    def setup_style(self):
        self.setMinimumHeight(44)
        self.setMinimumWidth(100)
        font = QFont()
        font.setPointSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)


class BauhausSecondaryButton(QPushButton):
    """Botão secundário Bauhaus"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("SecondaryButton")
        self.setup_style()
    
    def setup_style(self):
        self.setMinimumHeight(44)
        self.setMinimumWidth(100)
        font = QFont()
        font.setPointSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)


class BauhausDangerButton(QPushButton):
    """Botão destrutivo Bauhaus"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("DangerButton")
        self.setup_style()
    
    def setup_style(self):
        self.setMinimumHeight(44)
        self.setMinimumWidth(100)
        font = QFont()
        font.setPointSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)


class BauhausHighlightButton(QPushButton):
    """Botão de destaque Bauhaus"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("HighlightButton")
        self.setup_style()
    
    def setup_style(self):
        self.setMinimumHeight(44)
        self.setMinimumWidth(100)
        font = QFont()
        font.setPointSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)


class BauhausGhostButton(QPushButton):
    """Botão ghost Bauhaus (transparente com borda)"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("GhostButton")
        self.setup_style()
    
    def setup_style(self):
        self.setMinimumHeight(44)
        self.setMinimumWidth(100)
        font = QFont()
        font.setPointSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)


# ============================================================================
# INPUTS
# ============================================================================

class BauhausLineEdit(QLineEdit):
    """Input de texto Bauhaus"""
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)
        self.setup_style()
    
    def setup_style(self):
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)


class BauhausTextEdit(QTextEdit):
    """Área de texto Bauhaus"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setup_style()
    
    def setup_style(self):
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)


class BauhausComboBox(QComboBox):
    """ComboBox Bauhaus"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setup_style()
    
    def setup_style(self):
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)


class BauhausSpinBox(QSpinBox):
    """SpinBox Bauhaus"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setup_style()
    
    def setup_style(self):
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)


class BauhausDoubleSpinBox(QDoubleSpinBox):
    """DoubleSpinBox Bauhaus"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setup_style()
    
    def setup_style(self):
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)


# ============================================================================
# CARDS E FRAMES
# ============================================================================

class BauhausCard(QFrame):
    """Card Bauhaus padrão"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setup_style()
    
    def setup_style(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.setLayout(layout)


class BauhausStatCard(QFrame):
    """Card de estatística Bauhaus"""
    
    def __init__(self, title: str = "", value: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.title_label = QLabel(title)
        self.title_label.setObjectName("StatTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        self.setup_style()
    
    def setup_style(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
        self.setLayout(layout)
    
    def set_value(self, value: str):
        """Atualiza o valor exibido"""
        self.value_label.setText(value)
    
    def set_title(self, title: str):
        """Atualiza o título"""
        self.title_label.setText(title)
    
    def set_alert(self, is_alert: bool):
        """Define se o card está em estado de alerta"""
        self.setProperty("alert", "true" if is_alert else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ============================================================================
# LABELS E BADGES
# ============================================================================

class BauhausPageTitle(QLabel):
    """Título de página Bauhaus"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("PageTitle")
        self.setup_style()
    
    def setup_style(self):
        font = QFont()
        font.setPointSize(24)
        font.setWeight(QFont.Weight.Bold)
        self.setFont(font)


class BauhausSectionTitle(QLabel):
    """Título de seção Bauhaus"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("SectionTitle")
        self.setup_style()
    
    def setup_style(self):
        font = QFont()
        font.setPointSize(18)
        font.setWeight(QFont.Weight.Bold)
        self.setFont(font)


class BauhausBadge(QLabel):
    """Badge de status Bauhaus"""
    
    def __init__(self, text: str = "", badge_type: str = "info", parent=None):
        super().__init__(text, parent)
        self.badge_type = badge_type
        self.set_type(badge_type)
        self.setup_style()
    
    def setup_style(self):
        font = QFont()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def set_type(self, badge_type: str):
        """Define o tipo de badge (success, error, warning, info)"""
        self.badge_type = badge_type
        self.setObjectName(f"Badge{badge_type.capitalize()}")
        self.style().unpolish(self)
        self.style().polish(self)


# ============================================================================
# CONTAINERS
# ============================================================================

class BauhausContainer(QFrame):
    """Container genérico Bauhaus com layout vertical"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Container")
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.setLayout(layout)
    
    def add_widget(self, widget):
        """Adiciona um widget ao container"""
        self.layout().addWidget(widget)
    
    def add_layout(self, layout):
        """Adiciona um layout ao container"""
        self.layout().addLayout(layout)


class BauhausHorizontalContainer(QFrame):
    """Container genérico Bauhaus com layout horizontal"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HorizontalContainer")
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.setLayout(layout)
    
    def add_widget(self, widget):
        """Adiciona um widget ao container"""
        self.layout().addWidget(widget)
    
    def add_layout(self, layout):
        """Adiciona um layout ao container"""
        self.layout().addLayout(layout)


# ============================================================================
# FORM HELPERS
# ============================================================================

class BauhausFormField(QFrame):
    """Campo de formulário com label e input"""
    
    def __init__(self, label: str = "", input_type: str = "text", parent=None):
        super().__init__(parent)
        self.label = QLabel(label)
        self.label.setObjectName("FormLabel")
        
        if input_type == "text":
            self.input = BauhausLineEdit()
        elif input_type == "textarea":
            self.input = BauhausTextEdit()
        elif input_type == "combo":
            self.input = BauhausComboBox()
        elif input_type == "spin":
            self.input = BauhausSpinBox()
        elif input_type == "double":
            self.input = BauhausDoubleSpinBox()
        else:
            self.input = BauhausLineEdit()
        
        self.setup_style()
    
    def setup_style(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        self.setLayout(layout)
    
    def get_value(self):
        """Retorna o valor do input"""
        if hasattr(self.input, 'text'):
            return self.input.text()
        elif hasattr(self.input, 'toPlainText'):
            return self.input.toPlainText()
        elif hasattr(self.input, 'value'):
            return self.input.value()
        elif hasattr(self.input, 'currentText'):
            return self.input.currentText()
        return None
    
    def set_value(self, value):
        """Define o valor do input"""
        if hasattr(self.input, 'setText'):
            self.input.setText(str(value))
        elif hasattr(self.input, 'setPlainText'):
            self.input.setPlainText(str(value))
        elif hasattr(self.input, 'setValue'):
            self.input.setValue(value)


# ============================================================================
# DIVIDER
# ============================================================================

class BauhausDivider(QFrame):
    """Divisor horizontal Bauhaus"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setStyleSheet(f"""
            QFrame {{
                border: none;
                border-top: 1px solid {BAUHAUS_PALETTE['medium_gray']};
                margin: {SPACING['md']} 0;
            }}
        """)
        self.setMaximumHeight(1)
