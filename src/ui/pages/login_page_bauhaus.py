"""
Pagina de login - Bauhaus Design System
Forma segue funcao | Geometria pura | Alto contraste
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget, QFrame
)
from PySide6.QtCore import Qt, Signal
from config.bauhaus_design import *

logger = logging.getLogger(__name__)


class LoginPage(QWidget):
    """Interface Bauhaus: painel de controle industrial"""
    
    login_successful = Signal()

    def __init__(self, auth_manager, db_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        """Geometria funcional - Alto contraste"""
        # Fundo OFF_WHITE
        self.setStyleSheet(f"background-color: {OFF_WHITE};")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(SPACE_16, SPACE_12, SPACE_16, SPACE_12)
        main_layout.setSpacing(SPACE_8)

        # === HEADER === Preto estrutural
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
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        version = QLabel("v1.0.0 | SISTEMA DE SEGURANCA PROFISSIONAL")
        version.setStyleSheet(f"""
            QLabel {{
                color: {MID_GRAY};
                font-family: {FONT_FAMILY_MONO};
                font-size: {FONT_SIZE_SMALL}px;
                letter-spacing: 1px;
            }}
        """)
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(version)
        
        header.setLayout(header_layout)
        main_layout.addWidget(header)

        # === TRIAL BANNER === Preto com texto amarelo (MAXIMO CONTRASTE)
        trial_banner = QFrame()
        trial_banner.setStyleSheet(f"""
            QFrame {{
                background-color: {BLACK_BAUHAUS};
                border: 4px solid {YELLOW_BAUHAUS};
                padding: {SPACE_6}px;
            }}
        """)
        trial_layout = QVBoxLayout()
        trial_layout.setSpacing(0)
        
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
        trial_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trial_layout.addWidget(trial_label)
        
        trial_banner.setLayout(trial_layout)
        main_layout.addWidget(trial_banner)

        # === TABS ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(get_tab_style())

        login_widget = self.create_login_tab()
        self.tabs.addTab(login_widget, "LOGIN")

        register_widget = self.create_register_tab()
        self.tabs.addTab(register_widget, "REGISTRO")

        main_layout.addWidget(self.tabs)

        # === FOOTER ===
        footer = QLabel("MICROSOFT STORE | DADOS CRIPTOGRAFADOS | SISTEMA PROFISSIONAL")
        footer.setStyleSheet(f"""
            QLabel {{
                color: {DARK_GRAY};
                font-family: {FONT_FAMILY_MONO};
                font-size: {FONT_SIZE_SMALL}px;
                letter-spacing: 0.5px;
            }}
        """)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)

        self.setLayout(main_layout)

    def create_login_tab(self):
        """Tab LOGIN"""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {WHITE_BAUHAUS};")
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACE_8, SPACE_8, SPACE_8, SPACE_8)
        layout.setSpacing(SPACE_6)

        user_label = QLabel("USUARIO")
        user_label.setStyleSheet(get_label_section_style())
        layout.addWidget(user_label)
        
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Digite seu usuario")
        self.login_username.setMinimumHeight(SPACE_10)
        self.login_username.setStyleSheet(get_input_style())
        layout.addWidget(self.login_username)

        pass_label = QLabel("SENHA")
        pass_label.setStyleSheet(get_label_section_style())
        layout.addWidget(pass_label)
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Digite sua senha")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setMinimumHeight(SPACE_10)
        self.login_password.setStyleSheet(get_input_style())
        self.login_password.returnPressed.connect(self.handle_login)
        layout.addWidget(self.login_password)

        layout.addSpacing(SPACE_4)

        login_btn = QPushButton("ENTRAR")
        login_btn.setMinimumHeight(SPACE_12)
        login_btn.setStyleSheet(get_button_primary_style())
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_register_tab(self):
        """Tab REGISTRO"""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {WHITE_BAUHAUS};")
        layout = QVBoxLayout()
        layout.setContentsMargins(SPACE_8, SPACE_8, SPACE_8, SPACE_8)
        layout.setSpacing(SPACE_6)

        user_label = QLabel("USUARIO")
        user_label.setStyleSheet(get_label_section_style())
        layout.addWidget(user_label)
        
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Minimo 3 caracteres")
        self.register_username.setMinimumHeight(SPACE_10)
        self.register_username.setStyleSheet(get_input_style())
        layout.addWidget(self.register_username)

        email_label = QLabel("EMAIL (OPCIONAL)")
        email_label.setStyleSheet(get_label_section_style())
        layout.addWidget(email_label)
        
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("seu@email.com")
        self.register_email.setMinimumHeight(SPACE_10)
        self.register_email.setStyleSheet(get_input_style())
        layout.addWidget(self.register_email)

        pass_label = QLabel("SENHA")
        pass_label.setStyleSheet(get_label_section_style())
        layout.addWidget(pass_label)
        
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Minimo 6 caracteres")
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password.setMinimumHeight(SPACE_10)
        self.register_password.setStyleSheet(get_input_style())
        layout.addWidget(self.register_password)

        confirm_label = QLabel("CONFIRMAR SENHA")
        confirm_label.setStyleSheet(get_label_section_style())
        layout.addWidget(confirm_label)
        
        self.register_confirm = QLineEdit()
        self.register_confirm.setPlaceholderText("Digite novamente")
        self.register_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_confirm.setMinimumHeight(SPACE_10)
        self.register_confirm.setStyleSheet(get_input_style())
        self.register_confirm.returnPressed.connect(self.handle_register)
        layout.addWidget(self.register_confirm)

        layout.addSpacing(SPACE_4)

        register_btn = QPushButton("CRIAR CONTA TRIAL")
        register_btn.setMinimumHeight(SPACE_12)
        register_btn.setStyleSheet(get_button_primary_style())
        register_btn.clicked.connect(self.handle_register)
        layout.addWidget(register_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def handle_login(self):
        """Processar login"""
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not username or not password:
            QMessageBox.warning(self, "CAMPOS VAZIOS", "Preencha usuario e senha.")
            return

        if self.auth_manager.login(username, password):
            logger.info(f"[OK] Login: {username}")
            self.login_successful.emit()
        else:
            logger.warning(f"[AVISO] Falha no login: {username}")
            QMessageBox.critical(self, "ERRO DE AUTENTICACAO", "Usuario ou senha incorretos.")

    def handle_register(self):
        """Processar registro"""
        username = self.register_username.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        confirm = self.register_confirm.text()

        if not username or not password:
            QMessageBox.warning(self, "CAMPOS OBRIGATORIOS", "Usuario e senha sao obrigatorios.")
            return

        if len(username) < 3:
            QMessageBox.warning(self, "USUARIO INVALIDO", "Usuario deve ter minimo 3 caracteres.")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "SENHA FRACA", "Senha deve ter minimo 6 caracteres.")
            return

        if password != confirm:
            QMessageBox.warning(self, "SENHAS DIFERENTES", "As senhas nao coincidem.")
            return

        try:
            if self.auth_manager.register_user(username, password, email or None):
                logger.info(f"[OK] Registro: {username}")
                QMessageBox.information(
                    self,
                    "CONTA CRIADA",
                    f"Usuario '{username}' criado com sucesso!\n\n"
                    "TRIAL: 7 dias | 2 cameras | IA completa\n\n"
                    "Faca login agora."
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
            QMessageBox.critical(self, "USUARIO JA EXISTE", str(ve))
        except Exception as e:
            logger.error(f"[ERRO] Registro: {e}")
            QMessageBox.critical(self, "ERRO", f"Erro ao criar conta: {str(e)}")
