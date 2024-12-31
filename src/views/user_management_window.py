from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                           QDialog, QLineEdit, QComboBox, QMessageBox,
                           QFormLayout, QHeaderView, QCheckBox, QTabWidget,
                           QFrame, QStatusBar, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger('TerranPOS')

class UserDialog(QDialog):
    def __init__(self, parent=None, db_manager=None, user=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user = user
        self.setWindowTitle("Add User" if not user else "Edit User")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Username
        self.username_input = QLineEdit()
        if user:
            self.username_input.setText(user[1])
            self.username_input.setEnabled(False)  # Can't change username
        layout.addRow("Username:", self.username_input)
        
        # Password (only for new users)
        if not user:
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow("Password:", self.password_input)
            
            self.confirm_password = QLineEdit()
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow("Confirm Password:", self.confirm_password)
        
        # Full Name
        self.fullname_input = QLineEdit()
        if user:
            self.fullname_input.setText(user[2])
        layout.addRow("Full Name:", self.fullname_input)
        
        # Email
        self.email_input = QLineEdit()
        if user:
            self.email_input.setText(user[3])
        layout.addRow("Email:", self.email_input)
        
        # Role
        self.role_combo = QComboBox()
        roles = self.db_manager.get_all_roles()
        for role in roles:
            self.role_combo.addItem(role[1], role[0])
        if user:
            index = self.role_combo.findText(user[4])
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
        layout.addRow("Role:", self.role_combo)
        
        # Active status (only for editing)
        if user:
            self.active_check = QCheckBox("Active")
            self.active_check.setChecked(user[5])
            layout.addRow("Status:", self.active_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit, QComboBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
                margin: 2px;
            }
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                padding: 5px 10px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QCheckBox {
                color: white;
            }
        """)
    
    def validate_and_accept(self):
        if not self.user:  # New user
            if not all([self.username_input.text(),
                       self.password_input.text(),
                       self.confirm_password.text(),
                       self.fullname_input.text()]):
                QMessageBox.warning(self, "Error", "All fields except email are required")
                return
            
            if self.password_input.text() != self.confirm_password.text():
                QMessageBox.warning(self, "Error", "Passwords do not match")
                return
            
            if len(self.password_input.text()) < 8:
                QMessageBox.warning(self, "Error", "Password must be at least 8 characters long")
                return
        else:  # Edit user
            if not all([self.username_input.text(),
                       self.fullname_input.text()]):
                QMessageBox.warning(self, "Error", "Username and full name are required")
                return
        
        self.accept()
    
    def get_user_data(self):
        data = {
            'username': self.username_input.text(),
            'full_name': self.fullname_input.text(),
            'email': self.email_input.text(),
            'role': self.role_combo.currentText()
        }
        
        if not self.user:  # New user
            data['password'] = self.password_input.text()
        else:  # Edit user
            data['is_active'] = self.active_check.isChecked()
        
        return data

class RolePermissionsDialog(QDialog):
    def __init__(self, parent=None, db_manager=None, role_id=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.role_id = role_id
        self.setWindowTitle("Role Permissions")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Permissions table
        self.permissions_table = QTableWidget()
        self.permissions_table.setColumnCount(4)
        self.permissions_table.setHorizontalHeaderLabels([
            "Module", "Permission", "Description", "Granted"
        ])
        self.permissions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.permissions_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.load_permissions()
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QTableWidget {
                background-color: #333333;
                color: white;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #444444;
                color: white;
                padding: 5px;
                border: 1px solid #555555;
            }
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                padding: 5px 10px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QCheckBox {
                color: white;
            }
        """)
    
    def load_permissions(self):
        try:
            # Get all permissions
            cursor = self.db_manager.conn.cursor()
            cursor.execute("SELECT * FROM permissions ORDER BY module, name")
            all_permissions = cursor.fetchall()
            
            # Get granted permissions for this role
            cursor.execute(
                "SELECT permission_id FROM role_permissions WHERE role_id = ?",
                (self.role_id,)
            )
            granted_permissions = {row[0] for row in cursor.fetchall()}
            
            # Populate table
            self.permissions_table.setRowCount(len(all_permissions))
            for row, perm in enumerate(all_permissions):
                # Module
                self.permissions_table.setItem(row, 0, QTableWidgetItem(perm[3]))
                
                # Permission name
                self.permissions_table.setItem(row, 1, QTableWidgetItem(perm[1]))
                
                # Description
                self.permissions_table.setItem(row, 2, QTableWidgetItem(perm[2]))
                
                # Granted checkbox
                checkbox = QCheckBox()
                checkbox.setChecked(perm[0] in granted_permissions)
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.permissions_table.setCellWidget(row, 3, checkbox_widget)
                
                # Store permission ID
                self.permissions_table.setItem(row, 0, 
                    QTableWidgetItem(perm[3])).setData(Qt.ItemDataRole.UserRole, perm[0])
        
        except Exception as e:
            logger.error(f"Error loading permissions: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load permissions: {str(e)}")
    
    def get_granted_permissions(self):
        granted = []
        for row in range(self.permissions_table.rowCount()):
            perm_id = self.permissions_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            checkbox = self.permissions_table.cellWidget(row, 3).findChild(QCheckBox)
            if checkbox.isChecked():
                granted.append(perm_id)
        return granted

class UserManagementWindow(QMainWindow):
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        self.setWindowTitle("User Management")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Users tab
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)
        
        # Users toolbar
        users_toolbar = QHBoxLayout()
        add_user_btn = QPushButton("Add User")
        add_user_btn.clicked.connect(self.add_user)
        users_toolbar.addWidget(add_user_btn)
        users_toolbar.addStretch()
        users_layout.addLayout(users_toolbar)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Username", "Full Name", "Email", "Role", "Status", "Actions"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        users_layout.addWidget(self.users_table)
        
        tabs.addTab(users_tab, "Users")
        
        # Roles tab
        roles_tab = QWidget()
        roles_layout = QVBoxLayout(roles_tab)
        
        # Roles table
        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(4)
        self.roles_table.setHorizontalHeaderLabels([
            "ID", "Name", "Description", "Actions"
        ])
        self.roles_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        roles_layout.addWidget(self.roles_table)
        
        tabs.addTab(roles_tab, "Roles")
        
        # Activity Log tab
        activity_tab = QWidget()
        activity_layout = QVBoxLayout(activity_tab)
        
        # Activity table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(6)
        self.activity_table.setHorizontalHeaderLabels([
            "User", "Activity", "Module", "Description", "IP Address", "Timestamp"
        ])
        self.activity_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        activity_layout.addWidget(self.activity_table)
        
        tabs.addTab(activity_tab, "Activity Log")
        
        layout.addWidget(tabs)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Apply styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QTableWidget {
                background-color: #333333;
                color: white;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #444444;
                color: white;
                padding: 5px;
                border: 1px solid #555555;
            }
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                padding: 5px 10px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
            }
            QTabBar::tab {
                background-color: #333333;
                color: white;
                padding: 8px 16px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background-color: #444444;
            }
        """)
    
    def load_data(self):
        self.load_users()
        self.load_roles()
        self.load_activity_log()
    
    def load_users(self):
        try:
            users = self.db_manager.get_all_users()
            self.users_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                # ID
                id_item = QTableWidgetItem(str(user[0]))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.users_table.setItem(row, 0, id_item)
                
                # Username
                self.users_table.setItem(row, 1, QTableWidgetItem(user[1]))
                
                # Full Name
                self.users_table.setItem(row, 2, QTableWidgetItem(user[2]))
                
                # Email
                self.users_table.setItem(row, 3, QTableWidgetItem(user[3] or ""))
                
                # Role
                self.users_table.setItem(row, 4, QTableWidgetItem(user[4]))
                
                # Status
                status = "Active" if user[5] else "Inactive"
                status_item = QTableWidgetItem(status)
                status_item.setForeground(
                    Qt.GlobalColor.green if user[5] else Qt.GlobalColor.red
                )
                self.users_table.setItem(row, 5, status_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, u=user: self.edit_user(u))
                
                reset_pwd_btn = QPushButton("Reset Password")
                reset_pwd_btn.clicked.connect(lambda checked, u=user: self.reset_password(u))
                
                actions_layout.addWidget(edit_btn)
                if user[0] != self.current_user['id']:  # Can't reset own password here
                    actions_layout.addWidget(reset_pwd_btn)
                
                self.users_table.setCellWidget(row, 6, actions_widget)
            
            self.status_bar.showMessage(f"Loaded {len(users)} users")
            
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load users: {str(e)}")
    
    def load_roles(self):
        try:
            roles = self.db_manager.get_all_roles()
            self.roles_table.setRowCount(len(roles))
            
            for row, role in enumerate(roles):
                # ID
                id_item = QTableWidgetItem(str(role[0]))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.roles_table.setItem(row, 0, id_item)
                
                # Name
                self.roles_table.setItem(row, 1, QTableWidgetItem(role[1]))
                
                # Description
                self.roles_table.setItem(row, 2, QTableWidgetItem(role[2] or ""))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                
                permissions_btn = QPushButton("Permissions")
                permissions_btn.clicked.connect(lambda checked, r=role: self.manage_permissions(r))
                actions_layout.addWidget(permissions_btn)
                
                self.roles_table.setCellWidget(row, 3, actions_widget)
            
            self.status_bar.showMessage(f"Loaded {len(roles)} roles")
            
        except Exception as e:
            logger.error(f"Error loading roles: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load roles: {str(e)}")
    
    def load_activity_log(self):
        try:
            activities = self.db_manager.get_user_activity_log()
            self.activity_table.setRowCount(len(activities))
            
            for row, activity in enumerate(activities):
                for col, value in enumerate(activity):
                    self.activity_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            self.status_bar.showMessage(f"Loaded {len(activities)} activities")
            
        except Exception as e:
            logger.error(f"Error loading activity log: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load activity log: {str(e)}")
    
    def add_user(self):
        try:
            dialog = UserDialog(self, self.db_manager)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                user_data = dialog.get_user_data()
                
                # Create user
                user_id = self.db_manager.create_user(
                    user_data['username'],
                    user_data['password'],
                    user_data['full_name'],
                    user_data['email'],
                    user_data['role']
                )
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "create",
                    "user_management",
                    f"Created user: {user_data['username']}"
                )
                
                self.load_users()
                self.status_bar.showMessage("User created successfully")
        
        except Exception as e:
            logger.error(f"Error adding user: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")
    
    def edit_user(self, user):
        try:
            dialog = UserDialog(self, self.db_manager, user)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                user_data = dialog.get_user_data()
                
                # Update user
                self.db_manager.update_user(
                    user[0],
                    user_data['full_name'],
                    user_data['email'],
                    user_data['role'],
                    user_data['is_active']
                )
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "update",
                    "user_management",
                    f"Updated user: {user[1]}"
                )
                
                self.load_users()
                self.status_bar.showMessage("User updated successfully")
        
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to update user: {str(e)}")
    
    def reset_password(self, user):
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Reset",
                f"Are you sure you want to reset the password for {user[1]}?\n"
                "The password will be reset to a temporary value that must be changed on next login.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Generate temporary password
                import random
                import string
                temp_password = ''.join(
                    random.choices(string.ascii_letters + string.digits, k=12)
                )
                
                # Update password
                self.db_manager.change_password(user[0], None, temp_password)
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "reset_password",
                    "user_management",
                    f"Reset password for user: {user[1]}"
                )
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Password has been reset for {user[1]}.\n"
                    f"Temporary password: {temp_password}\n\n"
                    "Please provide this password to the user securely."
                )
        
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to reset password: {str(e)}")
    
    def manage_permissions(self, role):
        try:
            dialog = RolePermissionsDialog(self, self.db_manager, role[0])
            if dialog.exec() == QDialog.DialogCode.Accepted:
                granted_permissions = dialog.get_granted_permissions()
                
                # Start transaction
                cursor = self.db_manager.conn.cursor()
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Remove all current permissions
                    cursor.execute(
                        "DELETE FROM role_permissions WHERE role_id = ?",
                        (role[0],)
                    )
                    
                    # Add new permissions
                    for perm_id in granted_permissions:
                        cursor.execute(
                            """INSERT INTO role_permissions (role_id, permission_id)
                               VALUES (?, ?)""",
                            (role[0], perm_id)
                        )
                    
                    self.db_manager.conn.commit()
                    
                    # Log activity
                    self.db_manager.log_user_activity(
                        self.current_user['id'],
                        "update_permissions",
                        "user_management",
                        f"Updated permissions for role: {role[1]}"
                    )
                    
                    self.status_bar.showMessage("Role permissions updated successfully")
                    
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    raise e
        
        except Exception as e:
            logger.error(f"Error managing permissions: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to update permissions: {str(e)}") 