"""
Login Page - MAXIMUM READABILITY ALERTS
Alertas com contraste extremo - fonte gigante - impossivel nao ler
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QTabWidget,
                               QMessageBox, QDialog)
from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtGui import QFont

from config.bauhaus_design import *
from src.utils import setup_logger

logger = setup_logger(__name__)


class MaxReadabilityDialog(QDialog):
    """Dialog de alerta com MAXIMO contraste e legibilidade"""
    
    def __init__(self, parent, title, message, alert_type="error"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(600, 300)
        
        # Cores por tipo
        if alert_type == "error":
            bg_color = RED_BAUHAUS
            text_color = WHITE_BAUHAUS
        elif alert_type == "warning":
            bg_color = YELLOW_BAUHAUS
            text_color = BLACK_BAUHAUS
        else:  # success
            bg_color = GREEN_BAUHAUS
            text_color = WHITE_BAUHAUS
        
        # Estilo do dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 8px solid {NEAR_BLACK};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACE_12, SPACE_12, SPACE_12, SPACE_12)
        layout.setSpacing(SPACE_8)
        
        # Titulo GIGANTE
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-family: {FONT_FAMILY_UI};
                font-size: 32px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 3px;
                padding: {SPACE_6}px;
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Mensagem GIGANTE
        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-family: {FONT_FAMILY_UI};
                font-size: 24px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 2px;
                padding: {SPACE_8}px;
            }}
        """)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # Botao OK GIGANTE
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {text_color};
                color: {bg_color};
                border: 4px solid {NEAR_BLACK};
                padding: {SPACE_6}px {SPACE_12}px;
                font-family: {FONT_FAMILY_UI};
                font-size: 28px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 2px;
                min-height: 80px;
            }}
            QPushButton:hover {{
                border: 6px solid {NEAR_BLACK};
            }}
        """)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
        
        self.setLayout(layout)


class LoginPage(QWidget):
    """Tela de autenticacao - Estetica funcional Bauhaus"""
    
    login_successful = Signal()

    def __init__(self, auth_manager, db_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        """Geometria funcional - Alto contraste"""
        self.setStyleSheet(f"background-color: {OFF_WHITE};")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(SPACE_16, SPACE_12, SPACE_16, SPACE_12)
        main_layout.setSpacing(SPACE_8)

        # HEADER
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {NEAR_BLACK};
                border: none;
                padding: {SPACE_8}px;
            }}
        """)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(SPACE_2)
        
        title = QLabel("EDGE PROPERTY SECURITY AI")
        title.setStyleSheet(f"""
            QLabel {{
                color: {WHITE_BAUHAUS};
                font-family: {FONT_FAMILY_UI};
                font-size: {FONT_SIZE_HUGE}px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
        """)
        title.setAlignment(Qt.AlignCenter)
        
        version = QLabel("v1.0.0")
        version.setStyleSheet(f"""
            QLabel {{
                color: {MID_GRAY};
                font-family: {FONT_FAMILY_MONO};
                font-size: {FONT_SIZE_SMALL}px;
                font-weight: 400;
            }}
        """)
        version.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(version)
        header.setLayout(header_layout)
        main_layout.addWidget(header)

        # TRIAL BANNER
        trial_banner = QFrame()
        trial_banner.setStyleSheet(f"""
            QFrame {{
                background-color: {BLACK_BAUHAUS};
                border: 4px solid {YELLOW_BAUHAUS};
                padding: {SPACE_6}px;
            }}
        """)
        
        trial_label = QLabel("TRIAL: 7 DIAS | 2 CAMERAS | IA COMPLETA")
        trial_label.setStyleSheet(f"""
            QLabel {{
                color: {YELLOW_BAUHAUS};
                font-family: {FONT_FAMILY_UI};
                font-size: {FONT_SIZE_XL}px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
        """)
        trial_label.setAlignment(Qt.AlignCenter)
        
        trial_layout = QVBoxLayout()
        trial_layout.setContentsMargins(0, 0, 0, 0)
        trial_layout.addWidget(trial_label)
        trial_banner.setLayout(trial_layout)
        main_layout.addWidget(trial_banner)

        main_layout.addSpacing(SPACE_8)

        # CARD CENTRAL
        card = QFrame()
        card.setStyleSheet(get_card_style())
        card.setMaximumWidth(500)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(SPACE_8, SPACE_8, SPACE_8, SPACE_8)
        card_layout.setSpacing(SPACE_6)

        # TABS
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(get_tab_style())
        
        login_tab = self.create_login_tab()
        self.tabs.addTab(login_tab, "LOGIN")
        
        register_tab = self.create_register_tab()
        self.tabs.addTab(register_tab, "REGISTRO")
        
        card_layout.addWidget(self.tabs)
        card.setLayout(card_layout)
        
        main_layout.addWidget(card, 0, Qt.AlignHCenter)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_login_tab(self) -> QWidget:
        """Aba de login"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(SPACE_4)
        layout.setContentsMargins(SPACE_6, SPACE_6, SPACE_6, SPACE_6)

        # USUARIO
        usuario_label = QLabel("USUARIO")
        usuario_label.setStyleSheet(get_label_section_style())
        layout.addWidget(usuario_label)
        
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Digite seu usuario")
        self.login_username.setStyleSheet(get_input_style())
        layout.addWidget(self.login_username)

        layout.addSpacing(SPACE_3)

        # SENHA
        senha_label = QLabel("SENHA")
        senha_label.setStyleSheet(get_label_section_style())
        layout.addWidget(senha_label)
        
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setPlaceholderText("Digite sua senha")
        self.login_password.setStyleSheet(get_input_style())
        layout.addWidget(self.login_password)

        layout.addSpacing(SPACE_6)

        # BOTAO ENTRAR
        login_btn = QPushButton("ENTRAR")
        login_btn.setStyleSheet(get_button_primary_style())
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_register_tab(self) -> QWidget:
        """Aba de registro"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(SPACE_4)
        layout.setContentsMargins(SPACE_6, SPACE_6, SPACE_6, SPACE_6)

        # USUARIO
        usuario_label = QLabel("USUARIO")
        usuario_label.setStyleSheet(get_label_section_style())
        layout.addWidget(usuario_label)
        
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Minimo 3 caracteres")
        self.register_username.setStyleSheet(get_input_style())
        layout.addWidget(self.register_username)

        layout.addSpacing(SPACE_2)

        # EMAIL (OPCIONAL)
        email_label = QLabel("EMAIL (OPCIONAL)")
        email_label.setStyleSheet(get_label_section_style())
        layout.addWidget(email_label)
        
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("exemplo@email.com")
        self.register_email.setStyleSheet(get_input_style())
        layout.addWidget(self.register_email)

        layout.addSpacing(SPACE_2)

        # SENHA
        senha_label = QLabel("SENHA")
        senha_label.setStyleSheet(get_label_section_style())
        layout.addWidget(senha_label)
        
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password.setPlaceholderText("Minimo 6 caracteres")
        self.register_password.setStyleSheet(get_input_style())
        layout.addWidget(self.register_password)

        layout.addSpacing(SPACE_2)

        # CONFIRMAR SENHA
        confirmar_label = QLabel("CONFIRMAR SENHA")
        confirmar_label.setStyleSheet(get_label_section_style())
        layout.addWidget(confirmar_label)
        
        self.register_confirm = QLineEdit()
        self.register_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_confirm.setPlaceholderText("Repita a senha")
        self.register_confirm.setStyleSheet(get_input_style())
        layout.addWidget(self.register_confirm)

        layout.addSpacing(SPACE_6)

        # BOTAO CRIAR CONTA
        register_btn = QPushButton("CRIAR CONTA TRIAL")
        register_btn.setStyleSheet(get_button_primary_style())
        register_btn.clicked.connect(self.handle_register)
        layout.addWidget(register_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    @Slot()
    def handle_login(self):
        """Processar login"""
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not username or not password:
            self.show_warning("CAMPOS VAZIOS", "PREENCHA USUARIO E SENHA")
            return

        if self.auth_manager.login(username, password):
            logger.info(f"[OK] Login: {username}")
            self.login_successful.emit()
        else:
            logger.warning(f"[AVISO] Falha no login: {username}")
            self.show_error("ERRO DE AUTENTICACAO", "USUARIO OU SENHA INCORRETOS")

    @Slot()
    def handle_register(self):
        """Processar registro"""
        username = self.register_username.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        confirm = self.register_confirm.text()

        if not username or not password:
            self.show_warning("CAMPOS OBRIGATORIOS", "USUARIO E SENHA SAO OBRIGATORIOS")
            return

        if len(username) < 3:
            self.show_warning("USUARIO INVALIDO", "USUARIO DEVE TER MINIMO 3 CARACTERES")
            return

        if len(password) < 6:
            self.show_warning("SENHA FRACA", "SENHA DEVE TER MINIMO 6 CARACTERES")
            return

        if password != confirm:
            self.show_warning("SENHAS DIFERENTES", "AS SENHAS NAO COINCIDEM")
            return

        try:
            if self.auth_manager.register_user(username, password, email or None):
                logger.info(f"[OK] Registro: {username}")
                self.show_success(
                    "CONTA CRIADA",
                    f"USUARIO '{username}' CRIADO COM SUCESSO!\n\n"
                    "TRIAL: 7 DIAS | 2 CAMERAS | IA COMPLETA\n\n"
                    "FACA LOGIN AGORA"
                )
                
                self.register_username.clear()
                self.register_email.clear()
                self.register_password.clear()
                self.register_confirm.clear()
                
                self.tabs.setCurrentIndex(0)
                self.login_username.setText(username)
                self.login_password.setFocus()
                
        except ValueError as ve:
            logger.error(f"[ERRO] Validacao: {ve}")
            self.show_error("USUARIO JA EXISTE", str(ve).upper())
        except Exception as e:
            logger.error(f"[ERRO] Registro: {e}")
            self.show_error("ERRO", f"ERRO AO CRIAR CONTA: {str(e).upper()}")

    def show_error(self, title: str, message: str):
        """Alert de ERRO - Vermelho GIGANTE - Impossivel nao ler"""
        dlg = MaxReadabilityDialog(self, title, message, "error")
        dlg.exec()

    def show_warning(self, title: str, message: str):
        """Alert de AVISO - Amarelo GIGANTE - Impossivel nao ler"""
        dlg = MaxReadabilityDialog(self, title, message, "warning")
        dlg.exec()

    def show_success(self, title: str, message: str):
        """Alert de SUCESSO - Verde GIGANTE - Impossivel nao ler"""
        dlg = MaxReadabilityDialog(self, title, message, "success")
        dlg.exec()
