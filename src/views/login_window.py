from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QLineEdit, QMessageBox,
                           QFrame, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import logging
import socket

logger = logging.getLogger('TerranPOS')

class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Password")
        self.setModal(True)
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Current password
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password.setPlaceholderText("Current Password")
        layout.addWidget(self.current_password)
        
        # New password
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setPlaceholderText("New Password")
        layout.addWidget(self.new_password)
        
        # Confirm new password
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setPlaceholderText("Confirm New Password")
        layout.addWidget(self.confirm_password)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLineEdit {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
                margin: 5px;
            }
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                padding: 5px 10px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
    
    def validate_and_accept(self):
        if not all([self.current_password.text(),
                   self.new_password.text(),
                   self.confirm_password.text()]):
            QMessageBox.warning(self, "Error", "All fields are required")
            return
        
        if self.new_password.text() != self.confirm_password.text():
            QMessageBox.warning(self, "Error", "New passwords do not match")
            return
        
        if len(self.new_password.text()) < 8:
            QMessageBox.warning(self, "Error", "Password must be at least 8 characters long")
            return
        
        self.accept()
    
    def get_passwords(self):
        return {
            'current': self.current_password.text(),
            'new': self.new_password.text()
        }

class LoginWindow(QMainWindow):
    login_successful = pyqtSignal(dict)  # Emits user data on successful login
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setup_ui()
        self.first_login = False
    
    def setup_ui(self):
        self.setWindowTitle("Terran Systems - Login")
        self.setFixedSize(400, 500)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo/Title
        title = QLabel("Terran Systems")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add some spacing
        layout.addSpacing(40)
        
        # Login form
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(40)
        self.username_input.setFont(QFont("Arial", 12))
        form_layout.addWidget(self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setMinimumHeight(40)
        self.password_input.setFont(QFont("Arial", 12))
        self.password_input.returnPressed.connect(self.login)
        form_layout.addWidget(self.password_input)
        
        # Login button
        login_btn = QPushButton("Login")
        login_btn.setMinimumHeight(40)
        login_btn.setFont(QFont("Arial", 12))
        login_btn.clicked.connect(self.login)
        form_layout.addWidget(login_btn)
        
        layout.addWidget(form_frame)
        
        # Error message label (hidden by default)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #ff0000;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Version info
        version_label = QLabel("Version 1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # Apply styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 8px;
                margin: 5px;
                border-radius: 4px;
                font-size: 12pt;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                margin: 5px;
                border-radius: 4px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QFrame {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 20px;
            }
        """)
    
    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()
    
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        try:
            # Attempt authentication
            user_data = self.db_manager.authenticate_user(username, password)
            
            if user_data:
                # Get IP address for session
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                
                # Create session
                session_token = self.db_manager.create_user_session(user_data['id'], ip_address)
                user_data['session_token'] = session_token
                
                # Check if this is the default admin user's first login
                if (username == "admin" and 
                    password == "admin123" and 
                    user_data['role'] == "admin"):
                    self.first_login = True
                    self.prompt_password_change(user_data)
                else:
                    # Log the successful login
                    self.db_manager.log_user_activity(
                        user_data['id'],
                        "login",
                        "auth",
                        f"User logged in from {ip_address}",
                        ip_address
                    )
                    
                    # Emit success signal with user data
                    self.login_successful.emit(user_data)
                    
                    # Clear and hide the window
                    self.username_input.clear()
                    self.password_input.clear()
                    self.hide()
            else:
                self.show_error("Invalid username or password")
        
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            self.show_error("An error occurred during login")
    
    def prompt_password_change(self, user_data):
        dialog = ChangePasswordDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            passwords = dialog.get_passwords()
            try:
                if self.db_manager.change_password(
                    user_data['id'],
                    passwords['current'],
                    passwords['new']
                ):
                    QMessageBox.information(
                        self,
                        "Success",
                        "Password changed successfully. Please log in with your new password."
                    )
                    self.password_input.clear()
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to change password. Please check your current password."
                    )
            except Exception as e:
                logger.error(f"Password change error: {str(e)}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Error",
                    "An error occurred while changing the password"
                )
        else:
            QMessageBox.warning(
                self,
                "Warning",
                "You must change your password before continuing"
            ) 