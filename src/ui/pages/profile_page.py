"""
User Profile Page - Edit profile and email with verification
"""
import logging
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout
)
from PySide6.QtCore import QTimer

from config.config import EMAIL_VERIFICATION_TTL_MINUTES

logger = logging.getLogger(__name__)


class ProfilePage(QWidget):
    """Página de perfil do usuário"""
    
    def __init__(self, db_manager, auth_manager):
        super().__init__()
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.pending_email = None
        self.verification_code = None
        
        self.init_ui()
        self.load_profile()
    
    def init_ui(self):
        """Inicializa interface"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("User Profile")
        title.setProperty("class", "page-title")
        layout.addWidget(title)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(30)
        self.status_label.hide()
        layout.addWidget(self.status_label)
        
        # Profile Info Group
        profile_group = QGroupBox("Profile Information")
        profile_layout = QFormLayout()
        
        self.username_label = QLabel("")
        profile_layout.addRow("Username:", self.username_label)
        
        self.current_email_label = QLabel("")
        profile_layout.addRow("Current Email:", self.current_email_label)
        
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)
        
        # Change Email Group
        email_group = QGroupBox("Change Email")
        email_layout = QVBoxLayout()
        
        # New email input
        email_input_layout = QHBoxLayout()
        email_input_layout.addWidget(QLabel("New Email:"))
        self.new_email_input = QLineEdit()
        self.new_email_input.setPlaceholderText("name@example.com")
        email_input_layout.addWidget(self.new_email_input)
        
        self.send_code_btn = QPushButton("Send Verification Code")
        self.send_code_btn.clicked.connect(self.send_verification_code)
        email_input_layout.addWidget(self.send_code_btn)
        email_layout.addLayout(email_input_layout)
        
        # Verification code input (hidden by default)
        self.verification_widget = QWidget()
        verification_layout = QHBoxLayout()
        verification_layout.setContentsMargins(0, 0, 0, 0)
        
        verification_layout.addWidget(QLabel("Verification Code:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter 6-digit code")
        self.code_input.setMaxLength(6)
        verification_layout.addWidget(self.code_input)
        
        self.verify_btn = QPushButton("Verify & Update Email")
        self.verify_btn.clicked.connect(self.verify_code)
        verification_layout.addWidget(self.verify_btn)
        
        self.verification_widget.setLayout(verification_layout)
        self.verification_widget.hide()
        email_layout.addWidget(self.verification_widget)
        
        # Info text
        info_label = QLabel(f"A 6-digit verification code will be sent to your new email address.\nCode expires in {EMAIL_VERIFICATION_TTL_MINUTES} minutes.")
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        email_layout.addWidget(info_label)
        
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_profile(self):
        """Carrega dados do perfil"""
        user_id = self.auth_manager.get_user_id()
        if not user_id:
            return
        
        # Get username
        username = self.auth_manager.username
        self.username_label.setText(username or "N/A")
        
        # Get email
        email = self.db_manager.get_user_email(user_id)
        self.current_email_label.setText(email or "Not set")
    
    def send_verification_code(self):
        """Envia código de verificação para novo email"""
        new_email = self.new_email_input.text().strip()
        
        if not new_email:
            self.show_status("✗ Please enter a new email address", "error")
            return
        
        if "@" not in new_email or "." not in new_email:
            self.show_status("✗ Invalid email format", "error")
            return
        
        user_id = self.auth_manager.get_user_id()
        if not user_id:
            self.show_status("✗ Not logged in", "error")
            return
        
        # Generate 6-digit code
        self.verification_code = ''.join(random.choices(string.digits, k=6))
        self.pending_email = new_email
        
        # Save to database
        try:
            self.db_manager.create_email_verification(user_id, new_email, self.verification_code)
            logger.info(f"Created verification code for {new_email}")
        except Exception as e:
            logger.error(f"Error creating verification: {e}")
            self.show_status(f"✗ Database error: {e}", "error")
            return
        
        # Try to send email
        if self.send_verification_email(new_email, self.verification_code):
            self.show_status(f"✓ Verification code sent to {new_email}", "success", 0)
            self.verification_widget.show()
            self.send_code_btn.setEnabled(False)
            self.new_email_input.setEnabled(False)
        else:
            # Email failed but show code in UI for testing
            self.show_status(f"⚠ Email send failed. Code for testing: {self.verification_code}", "warning", 0)
            self.verification_widget.show()
    
    def send_verification_email(self, email: str, code: str) -> bool:
        """Envia email com código de verificação"""
        try:
            # Get SMTP settings from database
            user_id = self.auth_manager.get_user_id()
            smtp_settings = self.db_manager.get_email_settings(user_id)
            
            if not smtp_settings:
                logger.warning("No SMTP settings configured - cannot send email")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Email Verification Code - {code}"
            msg['From'] = smtp_settings['sender_email']
            msg['To'] = email
            
            # HTML body
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 5px;">
                    <h2 style="color: #333;">Email Verification</h2>
                    <p>Your verification code is:</p>
                    <div style="background-color: #cecaca; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                        <h1 style="color: #333; font-size: 36px; margin: 0; letter-spacing: 5px;">{code}</h1>
                    </div>
                    <p style="color: #666;">This code will expire in {EMAIL_VERIFICATION_TTL_MINUTES} minutes.</p>
                    <p style="color: #666; font-size: 12px;">If you didn't request this code, please ignore this email.</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_settings['smtp_server'], smtp_settings['smtp_port']) as server:
                server.starttls()
                server.login(smtp_settings['sender_email'], smtp_settings['sender_password'])
                server.send_message(msg)
            
            logger.info(f"Verification email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}", exc_info=True)
            return False
    
    def verify_code(self):
        """Verifica código e atualiza email"""
        code = self.code_input.text().strip()
        
        if not code:
            self.show_status("✗ Please enter the verification code", "error")
            return
        
        if len(code) != 6 or not code.isdigit():
            self.show_status("✗ Code must be 6 digits", "error")
            return
        
        user_id = self.auth_manager.get_user_id()
        if not user_id:
            self.show_status("✗ Not logged in", "error")
            return
        
        # Verify code
        try:
            if self.db_manager.verify_email_code(user_id, code):
                self.show_status("✓ Email updated successfully!", "success")
                
                # Reset form
                self.new_email_input.clear()
                self.code_input.clear()
                self.verification_widget.hide()
                self.send_code_btn.setEnabled(True)
                self.new_email_input.setEnabled(True)
                
                # Reload profile
                self.load_profile()
            else:
                self.show_status("✗ Invalid or expired code", "error")
        except Exception as e:
            logger.error(f"Error verifying code: {e}")
            self.show_status(f"✗ Verification error: {e}", "error")
    
    def show_status(self, message: str, status_type: str = "info", duration: int = 5000):
        """Mostra mensagem de status"""
        self.status_label.setText(message)
        self.status_label.setProperty("feedbackType", status_type)
        self.status_label.setStyleSheet(self.status_label.styleSheet())
        self.status_label.show()
        
        if duration > 0:
            QTimer.singleShot(duration, self.status_label.hide)
