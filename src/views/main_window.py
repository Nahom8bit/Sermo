from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMenuBar, QStatusBar,
                           QLabel, QFrame, QSizePolicy, QMenu, QDialog, QLineEdit, QFormLayout,
                           QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction
from datetime import datetime
import logging
import os
from .inventory_window import InventoryWindow
from .pos_window import POSWindow
from .reports_window import ReportsWindow
from .backup_window import BackupWindow
from .login_window import LoginWindow, ChangePasswordDialog
from .user_management_window import UserManagementWindow

# Set up logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, 'app.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('TerranPOS')

class CompanyInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Company Information")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit(parent.company_info.text())
        self.phone_input = QLineEdit(parent.company_phone.text())
        
        layout.addRow("Company Name:", self.name_input)
        layout.addRow("Company Phone:", self.phone_input)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        logger.info("Initializing Main Window")
        try:
            self.db_manager = db_manager
            self.current_user = None
            self.session_token = None
            
            # Initialize login window
            self.login_window = LoginWindow(self.db_manager)
            self.login_window.login_successful.connect(self.on_login_successful)
            
            # Set up session check timer
            self.session_timer = QTimer()
            self.session_timer.timeout.connect(self.check_session)
            self.session_timer.start(60000)  # Check every minute
            
            # Initialize UI (but don't show it yet)
            self.setup_ui()
            
            # Check system date
            self.check_system_date()
            
            # Ensure main window is hidden and show only login window
            self.hide()
            self.login_window.show()
            
            logger.info("Main Window initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Main Window: {str(e)}", exc_info=True)
            QMessageBox.critical(None, "Error", f"Failed to initialize application: {str(e)}")
    
    def setup_ui(self):
        self.setWindowTitle("Terran Systems")
        self.setMinimumSize(1024, 768)
        
        # Set window background color
        self.setStyleSheet("background-color: #2b2b2b;")
        
        # Create and set up the menu bar
        self.create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("background-color: #333333; color: white;")
        
        # Add company name label
        company_label = QLabel("Terran Systems")
        company_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        company_label.setFont(QFont("Arial", 48))
        company_label.setStyleSheet("color: white;")
        company_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(company_label)
        
        # Create footer
        self.create_footer()
        
        # Set up timer for updating time
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
    
    def create_menu_bar(self):
        try:
            menubar = self.menuBar()
            menubar.setStyleSheet("""
                QMenuBar {
                    background-color: #333333;
                    color: white;
                    padding: 5px;
                }
                QMenuBar::item {
                    padding: 5px 10px;
                    margin-right: 5px;
                }
                QMenuBar::item:selected {
                    background-color: #555555;
                }
                QMenu {
                    background-color: #333333;
                    color: white;
                    border: 1px solid #555555;
                }
                QMenu::item:selected {
                    background-color: #555555;
                }
            """)
            
            # Create Menu dropdown
            menu_menu = QMenu("Menu", self)
            
            # Company Information (requires settings_view permission)
            company_info_action = QAction("Company Information", self)
            company_info_action.triggered.connect(self.edit_company_info)
            menu_menu.addAction(company_info_action)
            
            menu_menu.addSeparator()
            
            # User Management (requires user_view permission)
            user_management_action = QAction("User Management", self)
            user_management_action.triggered.connect(self.open_user_management)
            menu_menu.addAction(user_management_action)
            
            # Change Password (available to all users)
            change_password_action = QAction("Change Password", self)
            change_password_action.triggered.connect(self.change_password)
            menu_menu.addAction(change_password_action)
            
            menu_menu.addSeparator()
            
            # Logout
            logout_action = QAction("Logout", self)
            logout_action.triggered.connect(self.logout)
            menu_menu.addAction(logout_action)
            
            menubar.addMenu(menu_menu)
            
            # Add other menu items as actions
            self.pos_action = QAction("POS", self)
            self.pos_action.triggered.connect(self.open_pos_window)
            menubar.addAction(self.pos_action)
            
            self.inventory_action = QAction("Inventory", self)
            self.inventory_action.triggered.connect(self.open_inventory_window)
            menubar.addAction(self.inventory_action)
            
            self.reports_action = QAction("Reports", self)
            self.reports_action.triggered.connect(self.open_reports_window)
            menubar.addAction(self.reports_action)
            
            self.backup_action = QAction("Backup", self)
            self.backup_action.triggered.connect(self.open_backup_window)
            menubar.addAction(self.backup_action)
            
            # Store menu actions for permission management
            self.menu_actions = {
                'company_info': company_info_action,
                'user_management': user_management_action,
                'pos': self.pos_action,
                'inventory': self.inventory_action,
                'reports': self.reports_action,
                'backup': self.backup_action
            }
            
            logger.info("Menu bar created successfully")
        except Exception as e:
            logger.error(f"Error creating menu bar: {str(e)}", exc_info=True)
            raise
    
    def update_menu_permissions(self):
        """Update menu items based on user permissions"""
        if not self.current_user:
            return
        
        try:
            # Get user permissions
            permissions = self.db_manager.get_user_permissions(self.current_user['id'])
            allowed_actions = {perm[0] for perm in permissions}
            
            # Update menu items
            self.menu_actions['company_info'].setVisible('settings_view' in allowed_actions)
            self.menu_actions['user_management'].setVisible('user_view' in allowed_actions)
            self.menu_actions['pos'].setVisible('pos_access' in allowed_actions)
            self.menu_actions['inventory'].setVisible('inventory_view' in allowed_actions)
            self.menu_actions['reports'].setVisible('reports_view' in allowed_actions)
            self.menu_actions['backup'].setVisible('backup_create' in allowed_actions)
            
        except Exception as e:
            logger.error(f"Error updating menu permissions: {str(e)}", exc_info=True)
    
    def check_session(self):
        """Validate current session and handle timeout"""
        if self.session_token:
            try:
                session_data = self.db_manager.validate_session(self.session_token)
                if not session_data:
                    self.handle_session_timeout()
            except Exception as e:
                logger.error(f"Error checking session: {str(e)}", exc_info=True)
                self.handle_session_timeout()
    
    def handle_session_timeout(self):
        """Handle session timeout by logging out user"""
        QMessageBox.warning(
            self,
            "Session Expired",
            "Your session has expired. Please log in again."
        )
        self.logout()
    
    def on_login_successful(self, user_data):
        """Handle successful login"""
        self.current_user = user_data
        self.session_token = user_data['session_token']
        
        # Update UI based on permissions
        self.update_menu_permissions()
        
        # Update status bar with user info
        self.status_bar.showMessage(f"Logged in as: {user_data['full_name']} ({user_data['role']})")
        
        # Show main window
        self.show()
    
    def logout(self):
        """Log out current user"""
        try:
            if self.session_token:
                self.db_manager.end_session(self.session_token)
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "logout",
                    "auth",
                    "User logged out"
                )
            
            # Clear current user and session
            self.current_user = None
            self.session_token = None
            
            # Hide main window and show login
            self.hide()
            self.login_window.show()
            
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}", exc_info=True)
    
    def change_password(self):
        """Open change password dialog"""
        try:
            dialog = ChangePasswordDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                passwords = dialog.get_passwords()
                if self.db_manager.change_password(
                    self.current_user['id'],
                    passwords['current'],
                    passwords['new']
                ):
                    QMessageBox.information(
                        self,
                        "Success",
                        "Password changed successfully"
                    )
                    
                    # Log activity
                    self.db_manager.log_user_activity(
                        self.current_user['id'],
                        "change_password",
                        "user_management",
                        "User changed their password"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        "Failed to change password. Please check your current password."
                    )
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", "Failed to change password")
    
    def check_permission(self, permission):
        """Check if current user has a specific permission"""
        if not self.current_user:
            return False
        return self.db_manager.has_permission(self.current_user['id'], permission)
    
    def open_user_management(self):
        """Open user management window"""
        if not self.check_permission('user_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to access user management")
            return
        
        try:
            self.user_management_window = UserManagementWindow(self.db_manager, self.current_user)
            self.user_management_window.show()
        except Exception as e:
            logger.error(f"Error opening user management: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", "Failed to open user management")
    
    def open_pos_window(self):
        if not self.check_permission('pos_access'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to access POS")
            return
        
        try:
            self.pos_window = POSWindow(self.db_manager, self.current_user)
            self.pos_window.show()
        except Exception as e:
            logger.error(f"Error opening POS window: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open POS window: {str(e)}")
    
    def open_inventory_window(self):
        if not self.check_permission('inventory_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to access inventory")
            return
        
        try:
            self.inventory_window = InventoryWindow(self.db_manager, self.current_user)
            self.inventory_window.show()
        except Exception as e:
            logger.error(f"Error opening Inventory window: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open Inventory window: {str(e)}")
    
    def open_reports_window(self):
        if not self.check_permission('reports_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to access reports")
            return
        
        try:
            self.reports_window = ReportsWindow(self.db_manager, self.current_user)
            self.reports_window.show()
        except Exception as e:
            logger.error(f"Error opening Reports window: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open Reports window: {str(e)}")
    
    def open_backup_window(self):
        if not self.check_permission('backup_create'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to access backup")
            return
        
        try:
            self.backup_window = BackupWindow(self.db_manager, self.current_user)
            self.backup_window.show()
        except Exception as e:
            logger.error(f"Error opening Backup window: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open Backup window: {str(e)}")
    
    def edit_company_info(self):
        if not self.check_permission('settings_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to edit company information")
            return
        
        try:
            dialog = CompanyInfoDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.company_info.setText(dialog.name_input.text())
                self.company_phone.setText(dialog.phone_input.text())
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "update",
                    "settings",
                    "Updated company information"
                )
                
                logger.info("Company information updated successfully")
        except Exception as e:
            logger.error(f"Error editing company info: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to update company information: {str(e)}")
    
    def create_footer(self):
        footer = QFrame()
        footer.setFrameShape(QFrame.Shape.StyledPanel)
        footer.setStyleSheet("background-color: #333333; color: white; padding: 5px;")
        
        # Use horizontal layout for footer
        footer_layout = QHBoxLayout(footer)
        
        # Left side - Company info
        company_info_layout = QVBoxLayout()
        self.company_info = QLabel("Company name")
        self.company_phone = QLabel("Company telephone")
        company_info_layout.addWidget(self.company_info)
        company_info_layout.addWidget(self.company_phone)
        
        # Right side - Time and date
        time_date_layout = QVBoxLayout()
        self.time_label = QLabel()
        self.date_label = QLabel()
        time_date_layout.addWidget(self.time_label)
        time_date_layout.addWidget(self.date_label)
        
        # Add layouts to footer
        footer_layout.addLayout(company_info_layout)
        footer_layout.addStretch()  # This pushes the time/date to the right
        footer_layout.addLayout(time_date_layout)
        
        self.update_time()  # Initial time update
        self.centralWidget().layout().addWidget(footer)
    
    def update_time(self):
        current_time = datetime.now()
        self.time_label.setText(f"Time: {current_time.strftime('%H:%M')}")
        self.date_label.setText(f"Date: {current_time.strftime('%d-%m-%y')}")
    
    def check_system_date(self):
        """Check if system date has changed since last use"""
        try:
            current_date = datetime.now().date()
            
            # Get last used date from database
            last_date = self.db_manager.get_setting('last_used_date')
            
            if last_date:
                last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
                if last_date != current_date:
                    reply = QMessageBox.question(
                        self,
                        'Date Change Detected',
                        f'The system date ({current_date}) is different from the last used date ({last_date}). '
                        'The application will be updated to use the current date. Continue?',
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.db_manager.update_setting('last_used_date', current_date.strftime('%Y-%m-%d'))
                        logger.info(f"System date updated from {last_date} to {current_date}")
                    else:
                        logger.warning("User cancelled date update. Exiting application.")
                        self.close()
            else:
                # First time running the application
                self.db_manager.update_setting('last_used_date', current_date.strftime('%Y-%m-%d'))
                logger.info(f"Initial system date set to {current_date}")
        
        except Exception as e:
            logger.error(f"Error checking system date: {str(e)}", exc_info=True)
            QMessageBox.warning(self, "Warning", "Failed to check system date. The application will continue with current date.")