from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                           QDialog, QLineEdit, QSpinBox, QDoubleSpinBox,
                           QMessageBox, QFormLayout, QHeaderView, QComboBox,
                           QFrame, QStatusBar, QTabWidget, QTextEdit, QGridLayout,
                           QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QSizeF
from PyQt6.QtGui import QColor, QIcon, QFont, QPainter, QPageSize
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
import logging
from datetime import datetime
import sqlite3

logger = logging.getLogger('TerranPOS')

class PaymentDialog(QDialog):
    def __init__(self, parent=None, total_amount=0.0):
        super().__init__(parent)
        self.total_amount = total_amount
        self.setWindowTitle("Payment")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Total amount display
        total_label = QLabel(f"Total Amount: ${total_amount:.2f}")
        total_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addRow(total_label)
        
        # Payment amount input
        self.payment_input = QDoubleSpinBox()
        self.payment_input.setRange(0, 1000000)
        self.payment_input.setDecimals(2)
        self.payment_input.setPrefix("$")
        self.payment_input.setValue(total_amount)
        self.payment_input.valueChanged.connect(self.calculate_change)
        layout.addRow("Payment Amount:", self.payment_input)
        
        # Change display
        self.change_label = QLabel("Change: $0.00")
        layout.addRow(self.change_label)
        
        # Payment method
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Card", "Other"])
        layout.addRow("Payment Method:", self.payment_method)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        layout.addRow("Notes:", self.notes_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        complete_btn = QPushButton("Complete Payment")
        cancel_btn = QPushButton("Cancel")
        
        complete_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(complete_btn)
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
    
    def calculate_change(self):
        change = self.payment_input.value() - self.total_amount
        self.change_label.setText(f"Change: ${change:.2f}")
    
    def validate_and_accept(self):
        if self.payment_input.value() < self.total_amount:
            QMessageBox.warning(self, "Error", "Payment amount must be at least the total amount")
            return
        self.accept()
    
    def get_payment_data(self):
        return {
            'amount': self.payment_input.value(),
            'method': self.payment_method.currentText(),
            'notes': self.notes_input.toPlainText(),
            'change': self.payment_input.value() - self.total_amount
        }

class ClientInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Client Information")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Client name input
        self.name_input = QLineEdit()
        layout.addRow("Client Name:", self.name_input)
        
        # NIF/Tax ID input
        self.nif_input = QLineEdit()
        layout.addRow("NIF/Tax ID:", self.nif_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.accept)
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
            QLineEdit {
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
    
    def get_client_data(self):
        return {
            'name': self.name_input.text(),
            'nif': self.nif_input.text()
        }

class POSWindow(QMainWindow):
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        self.cart_items = []
        self.client_info = {'name': '', 'nif': ''}
        self.setup_ui()
        self.load_products()
        
        # Log window access
        self.db_manager.log_user_activity(
            self.current_user['id'],
            "access",
            "pos",
            "Accessed POS window"
        )
    
    def check_permission(self, permission):
        """Check if current user has a specific permission"""
        return self.db_manager.has_permission(self.current_user['id'], permission)
    
    def setup_ui(self):
        self.setWindowTitle("Point of Sale")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Left panel - Product selection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Category filter and search
        filter_layout = QHBoxLayout()
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.load_categories()
        self.category_filter.currentIndexChanged.connect(self.filter_products)
        filter_layout.addWidget(self.category_filter)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products...")
        self.search_input.textChanged.connect(self.filter_products)
        filter_layout.addWidget(self.search_input)
        
        left_layout.addLayout(filter_layout)
        
        # Products grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.products_grid = QGridLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        left_layout.addWidget(scroll_area)
        
        # Right panel - Cart and actions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Client info
        client_layout = QHBoxLayout()
        self.client_label = QLabel("Client: Not specified")
        edit_client_btn = QPushButton("Edit Client")
        edit_client_btn.clicked.connect(self.edit_client_info)
        client_layout.addWidget(self.client_label)
        client_layout.addWidget(edit_client_btn)
        right_layout.addLayout(client_layout)
        
        # Cart
        cart_label = QLabel("Shopping Cart")
        cart_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(cart_label)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels([
            "ID", "Product", "Price", "Quantity", "Total", "Actions"
        ])
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.cart_table)
        
        # Totals
        totals_frame = QFrame()
        totals_frame.setFrameShape(QFrame.Shape.StyledPanel)
        totals_layout = QFormLayout(totals_frame)
        
        self.subtotal_label = QLabel("$0.00")
        self.tax_label = QLabel("$0.00")
        self.total_label = QLabel("$0.00")
        self.total_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        totals_layout.addRow("Tax (23%):", self.tax_label)
        totals_layout.addRow("Total:", self.total_label)
        
        right_layout.addWidget(totals_frame)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        clear_cart_btn = QPushButton("Clear Cart")
        clear_cart_btn.clicked.connect(self.clear_cart)
        button_layout.addWidget(clear_cart_btn)
        
        checkout_btn = QPushButton("Checkout")
        checkout_btn.clicked.connect(self.checkout)
        checkout_btn.setStyleSheet("background-color: #4CAF50;")  # Green color for checkout
        button_layout.addWidget(checkout_btn)
        
        right_layout.addLayout(button_layout)
        
        # Add panels to main layout
        layout.addWidget(left_panel, stretch=2)
        layout.addWidget(right_panel, stretch=1)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Apply styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
            }
            QTableWidget {
                background-color: #333333;
                color: white;
                gridline-color: #555555;
            }
            QTableWidget::item {
                padding: 5px;
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
            QLineEdit, QComboBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QFrame {
                background-color: #333333;
                border: 1px solid #555555;
                padding: 10px;
            }
            QScrollArea {
                border: none;
            }
        """)
    
    def load_categories(self):
        self.category_filter.clear()
        self.category_filter.addItem("All Categories", None)
        categories = self.db_manager.get_all_categories()
        for category in categories:
            self.category_filter.addItem(category[1], category[0])
    
    def load_products(self):
        try:
            # Clear existing products
            while self.products_grid.count():
                item = self.products_grid.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            
            # Get products
            products = self.db_manager.get_all_products()
            row = 0
            col = 0
            max_cols = 3
            
            for product in products:
                if product[3] > 0:  # Only show products with stock
                    product_card = QFrame()
                    product_card.setFrameShape(QFrame.Shape.StyledPanel)
                    card_layout = QVBoxLayout(product_card)
                    
                    # Product name
                    name_label = QLabel(product[1])
                    name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    card_layout.addWidget(name_label)
                    
                    # Price
                    price_label = QLabel(f"${product[4]:.2f}")
                    price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    card_layout.addWidget(price_label)
                    
                    # Stock
                    stock_label = QLabel(f"In stock: {product[3]}")
                    stock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    card_layout.addWidget(stock_label)
                    
                    # Add to cart button
                    add_btn = QPushButton("Add to Cart")
                    add_btn.clicked.connect(lambda checked, p=product: self.add_to_cart(p))
                    card_layout.addWidget(add_btn)
                    
                    self.products_grid.addWidget(product_card, row, col)
                    
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1
            
            # Add stretch to fill empty space
            self.products_grid.setRowStretch(row + 1, 1)
            self.products_grid.setColumnStretch(max_cols, 1)
            
        except Exception as e:
            logger.error(f"Error loading products: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")
    
    def filter_products(self):
        search_text = self.search_input.text().lower()
        selected_category = self.category_filter.currentData()
        
        for row in range(self.products_grid.rowCount()):
            for col in range(self.products_grid.columnCount()):
                item = self.products_grid.itemAtPosition(row, col)
                if item and item.widget():
                    widget = item.widget()
                    product_name = widget.findChild(QLabel).text().lower()
                    
                    show_widget = True
                    if search_text and search_text not in product_name:
                        show_widget = False
                    
                    widget.setVisible(show_widget)
    
    def add_to_cart(self, product):
        # Check if product is already in cart
        for item in self.cart_items:
            if item['id'] == product[0]:
                if item['quantity'] < product[3]:  # Check stock
                    item['quantity'] += 1
                    self.update_cart_display()
                else:
                    QMessageBox.warning(self, "Warning", "Not enough stock available")
                return
        
        # Add new item to cart
        self.cart_items.append({
            'id': product[0],
            'name': product[1],
            'price': product[4],
            'quantity': 1
        })
        self.update_cart_display()
    
    def update_cart_display(self):
        self.cart_table.setRowCount(len(self.cart_items))
        
        subtotal = 0
        for row, item in enumerate(self.cart_items):
            # ID
            self.cart_table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            
            # Product name
            self.cart_table.setItem(row, 1, QTableWidgetItem(item['name']))
            
            # Price
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"${item['price']:.2f}"))
            
            # Quantity
            quantity_spin = QSpinBox()
            quantity_spin.setRange(1, 100)
            quantity_spin.setValue(item['quantity'])
            quantity_spin.valueChanged.connect(lambda value, r=row: self.update_quantity(r, value))
            self.cart_table.setCellWidget(row, 3, quantity_spin)
            
            # Total
            total = item['price'] * item['quantity']
            subtotal += total
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"${total:.2f}"))
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, r=row: self.remove_from_cart(r))
            self.cart_table.setCellWidget(row, 5, remove_btn)
        
        # Update totals
        tax = subtotal * 0.23  # 23% tax
        total = subtotal + tax
        
        self.subtotal_label.setText(f"${subtotal:.2f}")
        self.tax_label.setText(f"${tax:.2f}")
        self.total_label.setText(f"${total:.2f}")
    
    def update_quantity(self, row, value):
        self.cart_items[row]['quantity'] = value
        self.update_cart_display()
    
    def remove_from_cart(self, row):
        self.cart_items.pop(row)
        self.update_cart_display()
    
    def clear_cart(self):
        if self.cart_items:
            reply = QMessageBox.question(
                self, "Confirm Clear",
                "Are you sure you want to clear the cart?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.cart_items.clear()
                self.update_cart_display()
    
    def edit_client_info(self):
        dialog = ClientInfoDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.client_info = dialog.get_client_data()
            name_display = self.client_info['name'] or "Not specified"
            self.client_label.setText(f"Client: {name_display}")
    
    def checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Error", "Cart is empty")
            return
        
        # Check if user has permission to process sales
        if not self.check_permission('pos_access'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to process sales")
            return
        
        # Calculate total
        subtotal = sum(item['price'] * item['quantity'] for item in self.cart_items)
        tax = subtotal * 0.23
        total = subtotal + tax
        
        # Show payment dialog
        payment_dialog = PaymentDialog(self, total)
        if payment_dialog.exec() == QDialog.DialogCode.Accepted:
            payment_data = payment_dialog.get_payment_data()
            
            try:
                # Create sale in database
                sale_id = self.db_manager.create_sale(
                    self.cart_items,
                    self.client_info['name'],
                    self.client_info['nif']
                )
                
                if sale_id:
                    # Show receipt
                    self.show_receipt(sale_id, payment_data)
                    
                    # Clear cart and client info
                    self.cart_items.clear()
                    self.client_info = {'name': '', 'nif': ''}
                    self.client_label.setText("Client: Not specified")
                    self.update_cart_display()
                    
                    # Refresh product display
                    self.load_products()
                    
                    # Log activity
                    self.db_manager.log_user_activity(
                        self.current_user['id'],
                        "sale",
                        "pos",
                        f"Completed sale #{sale_id}"
                    )
                    
                    self.status_bar.showMessage("Sale completed successfully")
                else:
                    raise Exception("Failed to create sale in database")
                
            except Exception as e:
                logger.error(f"Error completing sale: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to complete sale: {str(e)}")
    
    def show_receipt(self, sale_id, payment_data):
        try:
            sale_details = self.db_manager.get_sale_details(sale_id)
            if not sale_details:
                raise ValueError("No sale details found")
            
            receipt = QDialog(self)
            receipt.setWindowTitle("Receipt")
            receipt.setModal(True)
            receipt.setMinimumWidth(400)
            
            layout = QVBoxLayout(receipt)
            
            # Company info
            company_label = QLabel("Terran POS System")
            company_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            company_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(company_label)
            
            # Receipt details
            details_text = QTextEdit()
            details_text.setReadOnly(True)
            
            receipt_content = []
            receipt_content.append("=" * 40)
            receipt_content.append(f"Receipt #{sale_details[0][0]}")  # sale_id
            receipt_content.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            receipt_content.append("-" * 40)
            
            if sale_details[0][1]:  # client_name
                receipt_content.append(f"Client: {sale_details[0][1]}")
            if sale_details[0][2]:  # nif
                receipt_content.append(f"NIF: {sale_details[0][2]}")
            
            receipt_content.append("-" * 40)
            receipt_content.append("Items:")
            
            subtotal = 0
            for detail in sale_details:
                quantity = detail[5]  # quantity
                price = detail[6]    # price_at_sale
                product_name = detail[7]  # product_name
                amount = quantity * price
                receipt_content.append(
                    f"{product_name}\n"
                    f"  {quantity} x ${price:.2f} = ${amount:.2f}"
                )
                subtotal += amount
            
            tax = subtotal * 0.23
            total = subtotal + tax
            
            receipt_content.append("-" * 40)
            receipt_content.append(f"Subtotal: ${subtotal:.2f}")
            receipt_content.append(f"Tax (23%): ${tax:.2f}")
            receipt_content.append(f"Total: ${total:.2f}")
            receipt_content.append(f"Payment Method: {payment_data['method']}")
            receipt_content.append(f"Amount Paid: ${payment_data['amount']:.2f}")
            receipt_content.append(f"Change: ${payment_data['change']:.2f}")
            
            if payment_data['notes']:
                receipt_content.append("-" * 40)
                receipt_content.append("Notes:")
                receipt_content.append(payment_data['notes'])
            
            receipt_content.append("=" * 40)
            receipt_content.append("Thank you for your purchase!")
            
            details_text.setText("\n".join(receipt_content))
            layout.addWidget(details_text)
            
            # Print button
            print_btn = QPushButton("Print")
            print_btn.clicked.connect(lambda: self.print_receipt(receipt_content))
            layout.addWidget(print_btn)
            
            receipt.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    color: white;
                }
                QLabel, QTextEdit {
                    color: white;
                }
                QTextEdit {
                    background-color: #333333;
                    border: 1px solid #555555;
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
            
            receipt.exec()
            
        except Exception as e:
            logger.error(f"Error showing receipt: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to show receipt: {str(e)}")
    
    def print_receipt(self, receipt_content):
        try:
            # Create printer
            printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
            
            # Set custom page size for 58mm receipt printer (58mm = ~2.28 inches)
            custom_width_mm = 58
            custom_height_mm = 3000  # Long enough for most receipts
            custom_page_size = QPageSize(QSizeF(custom_width_mm, custom_height_mm), QPageSize.Unit.Millimeter)
            printer.setPageSize(custom_page_size)
            
            # Show printer dialog
            dialog = QPrintDialog(printer, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            # Create painter
            painter = QPainter()
            if not painter.begin(printer):
                QMessageBox.critical(self, "Error", "Could not start printing")
                return
            
            try:
                # Set up font and metrics
                font = QFont("Courier", 9)  # Monospace font for receipt
                painter.setFont(font)
                
                # Calculate metrics
                metrics = painter.fontMetrics()
                line_spacing = metrics.lineSpacing()
                
                # Get page rect in device pixels
                page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                margin_x = page_rect.width() * 0.1  # 10% margin
                margin_y = line_spacing
                
                # Calculate available width for text
                available_width = page_rect.width() - (2 * margin_x)
                current_y = margin_y
                
                # Function to wrap text to fit receipt width
                def wrap_text(text):
                    words = text.split()
                    if not words:
                        return []
                    lines = []
                    current_line = words[0]
                    
                    for word in words[1:]:
                        test_line = current_line + " " + word
                        if metrics.horizontalAdvance(test_line) <= available_width:
                            current_line = test_line
                        else:
                            lines.append(current_line)
                            current_line = word
                    
                    if current_line:
                        lines.append(current_line)
                    return lines
                
                # Print each line
                for line in receipt_content:
                    # Center align the company name and thank you message
                    if line.startswith("Terran POS") or line.startswith("Thank you"):
                        text_width = metrics.horizontalAdvance(line)
                        x = (page_rect.width() - text_width) / 2
                        painter.drawText(int(x), int(current_y), line)
                        current_y += line_spacing
                        continue
                    
                    # For separator lines, adjust to width
                    if set(line).issubset({'-', '='}):
                        separator_char = line[0]
                        num_chars = int(available_width / metrics.horizontalAdvance(separator_char))
                        line = separator_char * num_chars
                        painter.drawText(int(margin_x), int(current_y), line)
                        current_y += line_spacing
                        continue
                    
                    # Handle regular lines
                    if metrics.horizontalAdvance(line) > available_width:
                        # Wrap long lines
                        wrapped_lines = wrap_text(line)
                        for wrapped_line in wrapped_lines:
                            painter.drawText(int(margin_x), int(current_y), wrapped_line)
                            current_y += line_spacing
                    else:
                        painter.drawText(int(margin_x), int(current_y), line)
                        current_y += line_spacing
                    
                    # Check if we need a new page
                    if current_y >= page_rect.height() - margin_y:
                        printer.newPage()
                        current_y = margin_y
                
                painter.end()
                self.status_bar.showMessage("Receipt printed successfully")
                
            except Exception as e:
                painter.end()
                raise e
                
        except Exception as e:
            logger.error(f"Error printing receipt: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to print receipt: {str(e)}")
            
    def format_receipt_line(self, left_text, right_text, width):
        """Helper function to format a line with left and right aligned text"""
        space_between = width - len(left_text) - len(right_text)
        if space_between > 0:
            return left_text + " " * space_between + right_text
        return left_text + " " + right_text 