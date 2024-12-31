from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                           QDialog, QLineEdit, QSpinBox, QTimeEdit, QCalendarWidget,
                           QMessageBox, QFormLayout, QHeaderView, QComboBox,
                           QFrame, QStatusBar, QTabWidget, QTextEdit, QFileDialog,
                           QGroupBox, QCheckBox, QListWidget, QSplitter)
from PyQt6.QtCore import Qt, QTimer, QTime, QDate
from PyQt6.QtGui import QFont
import logging
import sqlite3
import shutil
import os
from datetime import datetime, timedelta
import json

logger = logging.getLogger('TerranPOS')

class BackupScheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Schedule Backup")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Frequency selection
        freq_group = QGroupBox("Backup Frequency")
        freq_layout = QVBoxLayout()
        
        self.daily_radio = QCheckBox("Daily")
        self.weekly_radio = QCheckBox("Weekly")
        self.monthly_radio = QCheckBox("Monthly")
        
        freq_layout.addWidget(self.daily_radio)
        freq_layout.addWidget(self.weekly_radio)
        freq_layout.addWidget(self.monthly_radio)
        
        freq_group.setLayout(freq_layout)
        layout.addWidget(freq_group)
        
        # Time selection
        time_group = QGroupBox("Backup Time")
        time_layout = QHBoxLayout()
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(23, 0))  # Default to 23:00
        time_layout.addWidget(self.time_edit)
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)
        
        # Retention policy
        retention_group = QGroupBox("Retention Policy")
        retention_layout = QFormLayout()
        self.retention_days = QSpinBox()
        self.retention_days.setRange(1, 365)
        self.retention_days.setValue(30)  # Default to 30 days
        retention_layout.addRow("Keep backups for (days):", self.retention_days)
        retention_group.setLayout(retention_layout)
        layout.addWidget(retention_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog, QGroupBox {
                background-color: #2b2b2b;
                color: white;
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
            QSpinBox, QTimeEdit {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QCheckBox {
                color: white;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                background-color: #444444;
                border: 1px solid #555555;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
            }
        """)
    
    def get_schedule(self):
        return {
            'daily': self.daily_radio.isChecked(),
            'weekly': self.weekly_radio.isChecked(),
            'monthly': self.monthly_radio.isChecked(),
            'time': self.time_edit.time().toString("HH:mm"),
            'retention_days': self.retention_days.value()
        }

class BackupWindow(QMainWindow):
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()
        
        # Log window access
        self.db_manager.log_user_activity(
            self.current_user['id'],
            "access",
            "backup",
            "Accessed backup window"
        )
    
    def check_permission(self, permission):
        """Check if current user has a specific permission"""
        return self.db_manager.has_permission(self.current_user['id'], permission)
    
    def create_backup(self):
        if not self.check_permission('backup_create'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to create backups")
            return
        
        try:
            backup_dir = self.backup_dir_edit.text()
            if not backup_dir:
                QMessageBox.warning(self, "Warning", "Please select a backup directory")
                return
            
            # Create backup
            backup_file = self.db_manager.create_backup(backup_dir)
            
            # Log activity
            self.db_manager.log_user_activity(
                self.current_user['id'],
                "create",
                "backup",
                f"Created backup: {backup_file}"
            )
            
            self.status_bar.showMessage(f"Backup created successfully: {backup_file}")
            self.load_backup_history()
        
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to create backup: {str(e)}")
    
    def restore_backup(self):
        if not self.check_permission('backup_restore'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to restore backups")
            return
        
        try:
            selected_items = self.backup_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Warning", "Please select a backup to restore")
                return
            
            backup_file = selected_items[0].text()
            
            reply = QMessageBox.question(
                self,
                "Confirm Restore",
                f"Are you sure you want to restore from backup '{backup_file}'?\nThis will overwrite current data!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Restore backup
                self.db_manager.restore_backup(backup_file)
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "restore",
                    "backup",
                    f"Restored from backup: {backup_file}"
                )
                
                self.status_bar.showMessage(f"Backup restored successfully: {backup_file}")
        
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to restore backup: {str(e)}")
    
    def delete_backup(self):
        if not self.check_permission('backup_delete'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to delete backups")
            return
        
        try:
            selected_items = self.backup_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Warning", "Please select a backup to delete")
                return
            
            backup_file = selected_items[0].text()
            
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete backup '{backup_file}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Delete backup
                self.db_manager.delete_backup(backup_file)
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "delete",
                    "backup",
                    f"Deleted backup: {backup_file}"
                )
                
                self.status_bar.showMessage(f"Backup deleted successfully: {backup_file}")
                self.load_backup_history()
        
        except Exception as e:
            logger.error(f"Error deleting backup: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to delete backup: {str(e)}")
    
    def schedule_backup(self):
        if not self.check_permission('backup_schedule'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to schedule backups")
            return
        
        try:
            backup_dir = self.backup_dir_edit.text()
            if not backup_dir:
                QMessageBox.warning(self, "Warning", "Please select a backup directory")
                return
            
            frequency = self.frequency_combo.currentText()
            time = self.time_edit.time().toString("HH:mm")
            
            # Schedule backup
            self.db_manager.schedule_backup(backup_dir, frequency, time)
            
            # Log activity
            self.db_manager.log_user_activity(
                self.current_user['id'],
                "schedule",
                "backup",
                f"Scheduled {frequency} backup at {time}"
            )
            
            self.status_bar.showMessage(f"Backup scheduled successfully: {frequency} at {time}")
            self.load_backup_schedule()
        
        except Exception as e:
            logger.error(f"Error scheduling backup: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to schedule backup: {str(e)}")
    
    def cancel_scheduled_backup(self):
        if not self.check_permission('backup_schedule'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to manage backup schedules")
            return
        
        try:
            selected_items = self.schedule_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Warning", "Please select a scheduled backup to cancel")
                return
            
            schedule_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
            
            # Cancel scheduled backup
            self.db_manager.cancel_scheduled_backup(schedule_id)
            
            # Log activity
            self.db_manager.log_user_activity(
                self.current_user['id'],
                "cancel",
                "backup",
                f"Cancelled scheduled backup {schedule_id}"
            )
            
            self.status_bar.showMessage("Scheduled backup cancelled successfully")
            self.load_backup_schedule()
        
        except Exception as e:
            logger.error(f"Error cancelling scheduled backup: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to cancel scheduled backup: {str(e)}")
    
    def browse_backup_dir(self):
        if not self.check_permission('backup_create'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to create backups")
            return
        
        try:
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Backup Directory",
                "",
                QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
            )
            
            if directory:
                self.backup_dir_edit.setText(directory)
        
        except Exception as e:
            logger.error(f"Error selecting backup directory: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to select backup directory: {str(e)}")
    
    def load_backup_history(self):
        if not self.check_permission('backup_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to view backup history")
            return
        
        try:
            # Clear existing items
            self.backup_list.clear()
            
            # Load backup history
            backups = self.db_manager.get_backup_history()
            
            # Add items to list
            for backup in backups:
                item = QListWidgetItem(backup['file_name'])
                item.setToolTip(f"Created: {backup['created_at']}\nSize: {backup['size']}")
                self.backup_list.addItem(item)
        
        except Exception as e:
            logger.error(f"Error loading backup history: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load backup history: {str(e)}")
    
    def load_backup_schedule(self):
        if not self.check_permission('backup_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to view backup schedules")
            return
        
        try:
            # Clear existing items
            self.schedule_list.clear()
            
            # Load backup schedules
            schedules = self.db_manager.get_backup_schedules()
            
            # Add items to list
            for schedule in schedules:
                item = QListWidgetItem(
                    f"{schedule['frequency']} at {schedule['time']} - {schedule['directory']}"
                )
                item.setData(Qt.ItemDataRole.UserRole, schedule['id'])
                item.setToolTip(f"Created by: {schedule['created_by']}\nLast run: {schedule['last_run']}")
                self.schedule_list.addItem(item)
        
        except Exception as e:
            logger.error(f"Error loading backup schedules: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load backup schedules: {str(e)}")
    
    def setup_ui(self):
        # Set window properties
        self.setWindowTitle("Backup Manager")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create backup section
        backup_group = QGroupBox("Create Backup")
        backup_layout = QHBoxLayout()
        
        self.backup_dir_edit = QLineEdit()
        self.backup_dir_edit.setPlaceholderText("Select backup directory")
        backup_layout.addWidget(self.backup_dir_edit)
        
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_backup_dir)
        backup_layout.addWidget(browse_button)
        
        create_button = QPushButton("Create Backup")
        create_button.clicked.connect(self.create_backup)
        backup_layout.addWidget(create_button)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Create schedule section
        schedule_group = QGroupBox("Schedule Backup")
        schedule_layout = QHBoxLayout()
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Daily", "Weekly", "Monthly"])
        schedule_layout.addWidget(self.frequency_combo)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        schedule_layout.addWidget(self.time_edit)
        
        schedule_button = QPushButton("Schedule")
        schedule_button.clicked.connect(self.schedule_backup)
        schedule_layout.addWidget(schedule_button)
        
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)
        
        # Create splitter for lists
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create backup history list
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        
        history_label = QLabel("Backup History")
        history_layout.addWidget(history_label)
        
        self.backup_list = QListWidget()
        history_layout.addWidget(self.backup_list)
        
        history_buttons = QHBoxLayout()
        
        restore_button = QPushButton("Restore")
        restore_button.clicked.connect(self.restore_backup)
        history_buttons.addWidget(restore_button)
        
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_backup)
        history_buttons.addWidget(delete_button)
        
        history_layout.addLayout(history_buttons)
        splitter.addWidget(history_widget)
        
        # Create schedule list
        schedule_widget = QWidget()
        schedule_layout = QVBoxLayout(schedule_widget)
        
        schedule_label = QLabel("Scheduled Backups")
        schedule_layout.addWidget(schedule_label)
        
        self.schedule_list = QListWidget()
        schedule_layout.addWidget(self.schedule_list)
        
        cancel_button = QPushButton("Cancel Schedule")
        cancel_button.clicked.connect(self.cancel_scheduled_backup)
        schedule_layout.addWidget(cancel_button)
        
        splitter.addWidget(schedule_widget)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Load initial data
        self.load_backup_history()
        self.load_backup_schedule() 