"""
Página de login
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget, QFrame, QGraphicsDropShadowEffect,
    QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addStretch()

        card = QFrame()
        card.setObjectName("LoginCard")
        card.setMaximumWidth(460)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor("#cecece"))
        card.setGraphicsEffect(shadow)
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(32, 32, 32, 24)
        card_layout.setSpacing(12)

        title = QLabel("Edge Property Security AI")
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("Secure analytics for properties and retail")
        subtitle.setObjectName("LoginSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        tabs = QTabWidget()
        tabs.setObjectName("LoginTabs")

        login_widget = self.create_login_tab()
        tabs.addTab(login_widget, "Login")

        register_widget = self.create_register_tab()
        tabs.addTab(register_widget, "Register")

        card_layout.addWidget(tabs)
        card.setLayout(card_layout)

        main_layout.addWidget(card, 0, Qt.AlignHCenter)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def create_login_tab(self) -> QWidget:
        """Cria a aba de login"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter your username")
        layout.addWidget(self.login_username)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setPlaceholderText("Enter your password")
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
        layout.setSpacing(8)

        # Username
        layout.addWidget(QLabel("Username:"))
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Choose a username")
        layout.addWidget(self.register_username)

        # Email
        layout.addWidget(QLabel("Email:"))
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("you@company.com")
        layout.addWidget(self.register_email)

        # Password
        layout.addWidget(QLabel("Password:"))
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_password.setPlaceholderText("Create a strong password")
        layout.addWidget(self.register_password)

        # Confirm Password
        layout.addWidget(QLabel("Confirm Password:"))
        self.register_confirm = QLineEdit()
        self.register_confirm.setEchoMode(QLineEdit.Password)
        self.register_confirm.setPlaceholderText("Repeat the password")
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
            error_msg = self.auth_manager.get_last_error() or "Invalid username or password"
            if error_msg == "Email not verified":
                resend = QMessageBox.question(
                    self,
                    "Email not verified",
                    "Your email is not verified. Resend verification code?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if resend == QMessageBox.Yes:
                    email = self.auth_manager.get_email_for_username(self.login_username.text().strip())
                    if email and self.auth_manager.send_verification_code(email):
                        QMessageBox.information(self, "Success", "Verification code sent.")
                    else:
                        QMessageBox.critical(self, "Error", self.auth_manager.get_last_error() or "Failed to send code")
            else:
                QMessageBox.critical(self, "Error", error_msg)

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
            QMessageBox.information(self, "Success", "Registration created. Check your email for the code.")
            self._verify_email_flow(email)
            self.register_username.clear()
            self.register_email.clear()
            self.register_password.clear()
            self.register_confirm.clear()
        else:
            error_msg = self.auth_manager.get_last_error() or "Registration failed."
            if error_msg == "SMTP not configured":
                error_msg = "SMTP not configured. Set email settings in Settings before registering."
            QMessageBox.critical(self, "Error", error_msg)

    def _verify_email_flow(self, email: str):
        """Solicita o codigo de verificacao e valida."""
        for _ in range(3):
            code, ok = QInputDialog.getText(
                self,
                "Email Verification",
                "Enter the verification code sent to your email:"
            )
            if not ok:
                return

            if self.auth_manager.verify_email_code(email, code.strip()):
                QMessageBox.information(self, "Verified", "Email verified. You can now login.")
                return

            retry = QMessageBox.question(
                self,
                "Invalid Code",
                "Invalid or expired code. Resend and try again?",
                QMessageBox.Yes | QMessageBox.No
            )
            if retry == QMessageBox.Yes:
                if not self.auth_manager.send_verification_code(email):
                    QMessageBox.critical(self, "Error", self.auth_manager.get_last_error() or "Failed to resend code")
                    return
            else:
                return
