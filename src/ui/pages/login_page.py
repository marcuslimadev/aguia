"""
Página de login - Padrão Windows
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget, QFrame
)
from PySide6.QtCore import Qt, Signal
import logging

logger = logging.getLogger(__name__)


class LoginPage(QWidget):
    """Página de login e registro"""

    login_successful = Signal()

    def __init__(self, auth_manager, db_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addStretch()

        # Card central
        card = QFrame()
        card.setMaximumWidth(400)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(16)

        # Título
        title = QLabel("Edge Property Security AI")
        title.setAlignment(Qt.AlignCenter)
        title_font = title.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        card_layout.addWidget(title)

        # Subtítulo
        subtitle = QLabel("Secure analytics for properties and retail")
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(20)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_login_tab(), "Login")
        tabs.addTab(self.create_register_tab(), "Register")
        card_layout.addWidget(tabs)

        card.setLayout(card_layout)
        main_layout.addWidget(card, 0, Qt.AlignHCenter)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_login_tab(self):
        """Cria a aba de login"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter your username")
        layout.addWidget(self.login_username)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setPlaceholderText("Enter your password")
        layout.addWidget(self.login_password)

        layout.addSpacing(10)

        # Botão Login
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_register_tab(self):
        """Cria a aba de registro"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Choose a username")
        layout.addWidget(self.register_username)

        # Email (opcional)
        layout.addWidget(QLabel("Email (optional):"))
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("your@email.com")
        layout.addWidget(self.register_email)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password.setPlaceholderText("Choose a password")
        layout.addWidget(self.register_password)

        # Confirm Password
        layout.addWidget(QLabel("Confirm Password:"))
        self.register_confirm = QLineEdit()
        self.register_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_confirm.setPlaceholderText("Confirm your password")
        layout.addWidget(self.register_confirm)

        layout.addSpacing(10)

        # Botão Register
        register_btn = QPushButton("Create Account")
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
            QMessageBox.warning(self, "Missing Fields", "Please enter username and password")
            return

        if self.auth_manager.login(username, password):
            logger.info(f"Login successful: {username}")
            self.login_successful.emit()
        else:
            logger.warning(f"Login failed: {username}")
            QMessageBox.critical(self, "Login Failed", "Invalid username or password")

    def handle_register(self):
        """Processar registro"""
        username = self.register_username.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        confirm = self.register_confirm.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing Fields", "Username and password are required")
            return

        if len(username) < 3:
            QMessageBox.warning(self, "Invalid Username", "Username must be at least 3 characters")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 6 characters")
            return

        if password != confirm:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match")
            return

        try:
            if self.auth_manager.register_user(username, password, email or None):
                logger.info(f"Registration successful: {username}")
                QMessageBox.information(
                    self,
                    "Account Created",
                    f"User '{username}' created successfully!\n\nTrial: 7 days | 2 cameras\n\nYou can now login."
                )
                
                self.register_username.clear()
                self.register_email.clear()
                self.register_password.clear()
                self.register_confirm.clear()
                
        except ValueError as ve:
            logger.error(f"Registration validation error: {ve}")
            QMessageBox.critical(self, "Registration Error", str(ve))
        except Exception as e:
            logger.error(f"Registration error: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create account: {str(e)}")
