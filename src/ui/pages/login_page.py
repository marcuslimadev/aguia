"""
Página de login - Padrão Windows
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QFrame, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread
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
        
        # Status label para feedback inline
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(30)
        self.status_label.hide()
        card_layout.addWidget(self.status_label)
        
        # Progress bar para processos demorados
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.hide()
        card_layout.addWidget(self.progress_bar)

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

    def show_status(self, message: str, status_type: str = "info", duration: int = 5000):
        """Show inline status message"""
        self.status_label.setText(message)
        self.status_label.setProperty("feedbackType", status_type)
        self.status_label.setStyleSheet(self.status_label.styleSheet())  # Refresh style
        self.status_label.show()
        
        if duration > 0:
            QTimer.singleShot(duration, self.status_label.hide)
    
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
            self.show_status("✗ Please enter username and password", "error")
            return
        
        # Mostrar progress bar
        self.progress_bar.show()
        self.status_label.hide()
        
        # Processar em thread separada (simulando delay)
        QTimer.singleShot(100, lambda: self._do_login(username, password))
    
    def _do_login(self, username, password):
        """Executa login após pequeno delay para mostrar progress"""
        if self.auth_manager.login(username, password):
            logger.info(f"Login successful: {username}")
            self.progress_bar.hide()
            self.show_status(f"✓ Welcome {username}!", "success", 1000)
            QTimer.singleShot(1000, self.login_successful.emit)
        else:
            logger.warning(f"Login failed: {username}")
            self.progress_bar.hide()
            self.show_status("✗ Invalid username or password", "error")

    def handle_register(self):
        """Processar registro"""
        username = self.register_username.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        confirm = self.register_confirm.text()

        if not username or not password:
            self.show_status("✗ Username and password are required", "error")
            return

        if len(username) < 3:
            self.show_status("✗ Username must be at least 3 characters", "error")
            return

        if len(password) < 6:
            self.show_status("✗ Password must be at least 6 characters", "error")
            return

        if password != confirm:
            self.show_status("✗ Passwords do not match", "error")
            return
        
        # Mostrar progress bar
        self.progress_bar.show()
        self.status_label.hide()
        
        # Processar registro
        QTimer.singleShot(100, lambda: self._do_register(username, email, password))
    
    def _do_register(self, username, email, password):
        """Executa registro após pequeno delay"""
        try:
            if self.auth_manager.register_user(username, password, email or None):
                logger.info(f"Registration successful: {username}")
                self.progress_bar.hide()
                self.show_status(
                    f"✓ User '{username}' created! Trial: 7 days | 2 cameras. You can now login.",
                    "success",
                    7000
                )
                
                self.register_username.clear()
                self.register_email.clear()
                self.register_password.clear()
                self.register_confirm.clear()
                
        except ValueError as ve:
            logger.error(f"Registration validation error: {ve}")
            self.progress_bar.hide()
            self.show_status(f"✗ {str(ve)}", "error")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            self.progress_bar.hide()
            self.show_status(f"✗ Failed to create account: {str(e)}", "error")
