from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                           QDialog, QLineEdit, QSpinBox, QDoubleSpinBox,
                           QMessageBox, QFormLayout, QHeaderView, QComboBox,
                           QFrame, QStatusBar, QTabWidget, QTextEdit, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon
import logging
from datetime import datetime
import sqlite3
import csv

logger = logging.getLogger('TerranPOS')

class StockReceiveDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle(f"Receive Stock - {product[1]}")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Supplier input
        self.supplier_input = QLineEdit()
        layout.addRow("Supplier:", self.supplier_input)
        
        # Quantity input
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 100000)
        layout.addRow("Quantity:", self.quantity_input)
        
        # Purchase price input
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setRange(0, 1000000)
        self.purchase_price_input.setDecimals(2)
        self.purchase_price_input.setPrefix("$")
        self.purchase_price_input.setValue(product[3])  # Set current price as default
        layout.addRow("Purchase Price per Unit:", self.purchase_price_input)
        
        # New selling price input
        self.selling_price_input = QDoubleSpinBox()
        self.selling_price_input.setRange(0, 1000000)
        self.selling_price_input.setDecimals(2)
        self.selling_price_input.setPrefix("$")
        self.selling_price_input.setValue(product[3])
        layout.addRow("New Selling Price:", self.selling_price_input)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addRow("Notes:", self.notes_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
    
    def get_stock_data(self):
        return {
            'supplier': self.supplier_input.text(),
            'quantity': self.quantity_input.value(),
            'purchase_price': self.purchase_price_input.value(),
            'selling_price': self.selling_price_input.value(),
            'notes': self.notes_input.toPlainText()
        }

class CategoryDialog(QDialog):
    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        self.category = category
        self.setWindowTitle("Add Category" if not category else "Edit Category")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        
        if category:
            self.name_input.setText(category[1])
            self.description_input.setText(category[2])
        
        layout.addRow("Category Name:", self.name_input)
        layout.addRow("Description:", self.description_input)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)
    
    def get_category_data(self):
        return {
            'name': self.name_input.text(),
            'description': self.description_input.toPlainText()
        }

class AddEditProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Add Product" if not product else "Edit Product")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QFormLayout(self)
        
        # Create input fields
        self.name_input = QLineEdit()
        self.category_combo = QComboBox()
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 100000)
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 1000000)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        
        # Alert threshold
        self.alert_threshold = QSpinBox()
        self.alert_threshold.setRange(0, 1000)
        self.alert_threshold.setValue(10)  # Default alert threshold
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        
        # Load categories
        self.load_categories()
        
        # Add fields to layout
        layout.addRow("Product Name:", self.name_input)
        layout.addRow("Category:", self.category_combo)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Price:", self.price_input)
        layout.addRow("Low Stock Alert Threshold:", self.alert_threshold)
        layout.addRow("Description:", self.description_input)
        
        # Add buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
        
        # If editing, populate fields
        if product:
            self.name_input.setText(product[1])  # name
            self.quantity_input.setValue(product[3])  # quantity
            self.price_input.setValue(product[4])  # price
            self.alert_threshold.setValue(product[5])  # alert_threshold
            self.description_input.setText(product[6] or "")  # description
            
            # Set category
            index = self.category_combo.findData(product[2])  # category_id
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        
        # Apply dark theme styles
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
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
        """)
    
    def load_categories(self):
        try:
            categories = self.parent().db_manager.get_all_categories()
            self.category_combo.clear()
            for category in categories:
                self.category_combo.addItem(category[1], category[0])
        except Exception as e:
            logger.error(f"Error loading categories: {str(e)}")
            self.category_combo.addItem("General", 1)  # Fallback to default category
    
    def get_product_data(self):
        return {
            'name': self.name_input.text(),
            'category_id': self.category_combo.currentData(),
            'quantity': self.quantity_input.value(),
            'price': self.price_input.value(),
            'alert_threshold': self.alert_threshold.value(),
            'description': self.description_input.toPlainText()
        }

class CategoryManagementDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Category Management")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton("Add Category")
        add_btn.clicked.connect(self.add_category)
        toolbar.addWidget(add_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Categories table
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(4)
        self.categories_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Actions"])
        self.categories_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.categories_table)
        
        self.load_categories()
        
        # Style
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
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
    
    def load_categories(self):
        categories = self.db_manager.get_all_categories()
        self.categories_table.setRowCount(len(categories))
        
        for row, category in enumerate(categories):
            # ID
            id_item = QTableWidgetItem(str(category[0]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.categories_table.setItem(row, 0, id_item)
            
            # Name
            self.categories_table.setItem(row, 1, QTableWidgetItem(category[1]))
            
            # Description
            self.categories_table.setItem(row, 2, QTableWidgetItem(category[2] or ""))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, c=category: self.edit_category(c))
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, c=category: self.delete_category(c))
            
            actions_layout.addWidget(edit_btn)
            if category[0] != 1:  # Don't allow deleting the default category
                actions_layout.addWidget(delete_btn)
            
            self.categories_table.setCellWidget(row, 3, actions_widget)
    
    def add_category(self):
        dialog = CategoryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            category_data = dialog.get_category_data()
            try:
                self.db_manager.add_category(
                    category_data['name'],
                    category_data['description']
                )
                self.load_categories()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Error", "Category name must be unique")
    
    def edit_category(self, category):
        dialog = CategoryDialog(self, category)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            category_data = dialog.get_category_data()
            try:
                self.db_manager.update_category(
                    category[0],
                    category_data['name'],
                    category_data['description']
                )
                self.load_categories()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Error", "Category name must be unique")
    
    def delete_category(self, category):
        if category[0] == 1:
            QMessageBox.warning(self, "Error", "Cannot delete the default category")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete category '{category[1]}'?\n"
            "All products will be moved to the default category.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.delete_category(category[0])
            self.load_categories()

class LowStockDialog(QDialog):
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Low Stock Alert")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Add warning label
        warning_label = QLabel("⚠️ The following items are running low on stock:")
        warning_label.setStyleSheet("color: #ff9999; font-weight: bold; font-size: 14px;")
        layout.addWidget(warning_label)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Product", "Category", "Current Stock", "Alert Threshold", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_low_stock_products()
        
        # Style
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
            QPushButton {
                background-color: #444444;
                color: white;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
    
    def load_low_stock_products(self):
        products = self.db_manager.get_low_stock_products()
        self.table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(product[1]))  # Name
            self.table.setItem(row, 1, QTableWidgetItem(product[-1]))  # Category name
            
            quantity_item = QTableWidgetItem(str(product[3]))
            quantity_item.setBackground(QColor("#8B0000"))
            self.table.setItem(row, 2, quantity_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(str(product[5])))  # Alert threshold
            
            # Action button
            receive_btn = QPushButton("Receive Stock")
            receive_btn.clicked.connect(lambda checked, p=product: self.parent().receive_stock(p))
            self.table.setCellWidget(row, 4, receive_btn)

class InventoryWindow(QMainWindow):
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.setup_ui()
        self.load_inventory()
        self.check_low_stock()
        
        # Log window access
        self.db_manager.log_user_activity(
            self.current_user['id'],
            "access",
            "inventory",
            "Accessed inventory window"
        )
    
    def check_permission(self, permission):
        """Check if current user has a specific permission"""
        return self.db_manager.has_permission(self.current_user['id'], permission)
    
    def setup_ui(self):
        self.setWindowTitle("Inventory Management")
        self.setMinimumSize(800, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Products tab
        products_tab = QWidget()
        products_layout = QVBoxLayout(products_tab)
        
        # Create toolbar
        toolbar = QHBoxLayout()
        
        # Add Product button
        add_btn = QPushButton("Add Product")
        add_btn.setIcon(QIcon.fromTheme("list-add"))
        add_btn.clicked.connect(self.add_product)
        toolbar.addWidget(add_btn)
        
        # Receive Stock button
        receive_btn = QPushButton("Receive Stock")
        receive_btn.clicked.connect(self.receive_stock)
        toolbar.addWidget(receive_btn)
        
        # Categories button
        categories_btn = QPushButton("Manage Categories")
        categories_btn.clicked.connect(self.manage_categories)
        toolbar.addWidget(categories_btn)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.clicked.connect(self.load_inventory)
        toolbar.addWidget(refresh_btn)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products...")
        self.search_input.textChanged.connect(self.filter_inventory)
        toolbar.addWidget(self.search_input)
        
        # Add category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.load_category_filter()
        self.category_filter.currentIndexChanged.connect(self.filter_inventory)
        toolbar.addWidget(self.category_filter)
        
        # Add low stock alert button with counter
        self.low_stock_btn = QPushButton("Low Stock (0)")
        self.low_stock_btn.clicked.connect(self.show_low_stock_dialog)
        toolbar.addWidget(self.low_stock_btn)
        
        toolbar.addStretch()
        
        # Add toolbar to layout
        products_layout.addLayout(toolbar)
        
        # Create inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(8)
        self.inventory_table.setHorizontalHeaderLabels([
            "ID", "Name", "Category", "Quantity", "Price", 
            "Alert Threshold", "Last Updated", "Actions"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        products_layout.addWidget(self.inventory_table)
        
        # Add products tab
        tabs.addTab(products_tab, "Products")
        
        # Add stock history tab
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Product", "Supplier", "Quantity", 
            "Purchase Price", "Selling Price", "Notes"
        ])
        history_layout.addWidget(self.history_table)
        tabs.addTab(history_tab, "Stock History")
        
        # Add tabs to main layout
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
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #333333;
                color: white;
                padding: 8px 20px;
                border: 1px solid #555555;
            }
            QTabBar::tab:selected {
                background-color: #444444;
            }
            QTableWidget {
                background-color: #333333;
                color: white;
                gridline-color: #555555;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #555555;
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
            QLineEdit {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QStatusBar {
                background-color: #333333;
                color: white;
            }
            QComboBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
        """)
    
    def load_category_filter(self):
        self.category_filter.clear()
        self.category_filter.addItem("All Categories", None)
        categories = self.db_manager.get_all_categories()
        for category in categories:
            self.category_filter.addItem(category[1], category[0])
    
    def check_low_stock(self):
        low_stock = self.db_manager.get_low_stock_products()
        self.low_stock_btn.setText(f"Low Stock ({len(low_stock)})")
        if len(low_stock) > 0:
            self.low_stock_btn.setStyleSheet("background-color: #8B0000;")
        else:
            self.low_stock_btn.setStyleSheet("")
    
    def show_low_stock_dialog(self):
        dialog = LowStockDialog(self, self.db_manager)
        dialog.exec()
    
    def manage_categories(self):
        if not self.check_permission('inventory_edit'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to manage categories")
            return
        
        try:
            dialog = CategoryManagementDialog(self, self.db_manager)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_category_filter()
                self.load_inventory()
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "manage",
                    "inventory",
                    "Managed product categories"
                )
        
        except Exception as e:
            logger.error(f"Error managing categories: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to manage categories: {str(e)}")
    
    def load_inventory(self):
        try:
            products = self.db_manager.get_all_products()
            self.inventory_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # ID
                id_item = QTableWidgetItem(str(product[0]))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.inventory_table.setItem(row, 0, id_item)
                
                # Name
                self.inventory_table.setItem(row, 1, QTableWidgetItem(product[1]))
                
                # Category
                self.inventory_table.setItem(row, 2, QTableWidgetItem(product[-1]))
                
                # Quantity
                quantity_item = QTableWidgetItem(str(product[3]))
                if product[3] <= product[5]:  # If quantity <= alert_threshold
                    quantity_item.setBackground(QColor("#8B0000"))
                self.inventory_table.setItem(row, 3, quantity_item)
                
                # Price
                self.inventory_table.setItem(row, 4, QTableWidgetItem(f"${product[4]:.2f}"))
                
                # Alert Threshold
                self.inventory_table.setItem(row, 5, QTableWidgetItem(str(product[5])))
                
                # Last Updated
                self.inventory_table.setItem(row, 6, QTableWidgetItem(str(product[8])))
                
                # Action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
                receive_btn = QPushButton("Receive")
                receive_btn.clicked.connect(lambda checked, p=product: self.receive_stock(p))
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, p=product: self.delete_product(p))
                
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(receive_btn)
                actions_layout.addWidget(delete_btn)
                self.inventory_table.setCellWidget(row, 7, actions_widget)
            
            # Load stock history
            self.load_stock_history()
            
            # Update low stock button
            self.check_low_stock()
            
            self.status_bar.showMessage(f"Loaded {len(products)} products")
            logger.info("Inventory loaded successfully")
        except Exception as e:
            logger.error(f"Error loading inventory: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load inventory: {str(e)}")
    
    def load_stock_history(self):
        try:
            history = self.db_manager.get_stock_history()
            self.history_table.setRowCount(len(history))
            
            for row, record in enumerate(history):
                self.history_table.setItem(row, 0, QTableWidgetItem(str(record[7])))  # Date
                self.history_table.setItem(row, 1, QTableWidgetItem(record[-1]))  # Product name
                self.history_table.setItem(row, 2, QTableWidgetItem(record[2]))  # Supplier
                self.history_table.setItem(row, 3, QTableWidgetItem(str(record[3])))  # Quantity
                self.history_table.setItem(row, 4, QTableWidgetItem(f"${record[4]:.2f}"))  # Purchase Price
                self.history_table.setItem(row, 5, QTableWidgetItem(f"${record[5]:.2f}"))  # Selling Price
                self.history_table.setItem(row, 6, QTableWidgetItem(record[6] or ""))  # Notes
        except Exception as e:
            logger.error(f"Error loading stock history: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load stock history: {str(e)}")
    
    def filter_inventory(self):
        search_text = self.search_input.text().lower()
        selected_category = self.category_filter.currentData()
        
        for row in range(self.inventory_table.rowCount()):
            show_row = True
            
            # Category filter
            if selected_category is not None:
                category_item = self.inventory_table.item(row, 2)
                if category_item and int(self.inventory_table.item(row, 0).text()) != selected_category:
                    show_row = False
            
            # Text search
            if show_row and search_text:
                show_row = False
                for col in range(1, 5):  # Search in name, category, quantity, and price columns
                    item = self.inventory_table.item(row, col)
                    if item and search_text in item.text().lower():
                        show_row = True
                        break
            
            self.inventory_table.setRowHidden(row, not show_row)
    
    def receive_stock(self, product):
        if not self.check_permission('inventory_edit'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to receive stock")
            return
        
        try:
            dialog = StockReceiveDialog(self, product)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                stock_data = dialog.get_stock_data()
                
                # Add stock receiving record
                self.db_manager.add_stock_receiving(
                    product[0],
                    stock_data['supplier'],
                    stock_data['quantity'],
                    stock_data['purchase_price'],
                    stock_data['selling_price'],
                    stock_data['notes']
                )
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "receive",
                    "inventory",
                    f"Received stock for product: {product[1]}"
                )
                
                self.load_inventory()
                self.check_low_stock()
                self.status_bar.showMessage("Stock received successfully")
        
        except Exception as e:
            logger.error(f"Error receiving stock: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to receive stock: {str(e)}")
    
    def add_product(self):
        if not self.check_permission('inventory_add'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to add products")
            return
        
        try:
            dialog = AddEditProductDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                product_data = dialog.get_product_data()
                
                # Add product
                product_id = self.db_manager.add_product(
                    product_data['name'],
                    product_data['quantity'],
                    product_data['price'],
                    product_data['category_id'],
                    product_data['alert_threshold'],
                    product_data['description']
                )
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "create",
                    "inventory",
                    f"Added product: {product_data['name']}"
                )
                
                self.load_inventory()
                self.check_low_stock()
                self.status_bar.showMessage("Product added successfully")
        
        except Exception as e:
            logger.error(f"Error adding product: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to add product: {str(e)}")
    
    def edit_product(self, product):
        if not self.check_permission('inventory_edit'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to edit products")
            return
        
        try:
            dialog = AddEditProductDialog(self, product)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                product_data = dialog.get_product_data()
                
                # Update product
                self.db_manager.update_product(
                    product[0],
                    product_data['name'],
                    product_data['quantity'],
                    product_data['price'],
                    product_data['category_id'],
                    product_data['alert_threshold'],
                    product_data['description']
                )
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "update",
                    "inventory",
                    f"Updated product: {product_data['name']}"
                )
                
                self.load_inventory()
                self.check_low_stock()
                self.status_bar.showMessage("Product updated successfully")
        
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to update product: {str(e)}")
    
    def delete_product(self, product):
        if not self.check_permission('inventory_delete'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to delete products")
            return
        
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete product '{product[1]}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Delete product
                self.db_manager.remove_product(product[0])
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "delete",
                    "inventory",
                    f"Deleted product: {product[1]}"
                )
                
                self.load_inventory()
                self.check_low_stock()
                self.status_bar.showMessage("Product deleted successfully")
        
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to delete product: {str(e)}")