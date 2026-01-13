"""
Página de login
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
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

        # Título
        title = QLabel("Edge Property Security AI")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Tabs para Login e Registro
        tabs = QTabWidget()

        # Aba de Login
        login_widget = self.create_login_tab()
        tabs.addTab(login_widget, "Login")

        # Aba de Registro
        register_widget = self.create_register_tab()
        tabs.addTab(register_widget, "Register")

        main_layout.addWidget(tabs)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_login_tab(self) -> QWidget:
        """Cria a aba de login"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Username
        layout.addWidget(QLabel("Username:"))
        self.login_username = QLineEdit()
        layout.addWidget(self.login_username)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.login_password)

        # Botão de Login
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.perform_login)
        layout.addWidget(login_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_register_tab(self) -> QWidget:
        """Cria a aba de registro"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Username
        layout.addWidget(QLabel("Username:"))
        self.register_username = QLineEdit()
        layout.addWidget(self.register_username)

        # Email
        layout.addWidget(QLabel("Email:"))
        self.register_email = QLineEdit()
        layout.addWidget(self.register_email)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.register_password)

        # Confirm Password
        layout.addWidget(QLabel("Confirm Password:"))
        self.register_confirm = QLineEdit()
        self.register_confirm.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.register_confirm)

        # Botão de Registro
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.perform_register)
        layout.addWidget(register_btn)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def perform_login(self):
        """Realiza o login"""
        username = self.login_username.text()
        password = self.login_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return

        if self.auth_manager.login(username, password):
            QMessageBox.information(self, "Success", "Login successful!")
            self.login_username.clear()
            self.login_password.clear()
            self.login_successful.emit()
        else:
            QMessageBox.critical(self, "Error", "Invalid username or password")

    def perform_register(self):
        """Realiza o registro"""
        username = self.register_username.text()
        email = self.register_email.text()
        password = self.register_password.text()
        confirm = self.register_confirm.text()

        if not username or not email or not password or not confirm:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return

        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        if self.auth_manager.register_user(username, password, email):
            QMessageBox.information(self, "Success", "Registration successful! You can now login.")
            self.register_username.clear()
            self.register_email.clear()
            self.register_password.clear()
            self.register_confirm.clear()
        else:
            QMessageBox.critical(self, "Error", "Registration failed. Username or email already exists.")
