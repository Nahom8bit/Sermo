from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                           QDialog, QLineEdit, QSpinBox, QDoubleSpinBox,
                           QMessageBox, QFormLayout, QHeaderView, QComboBox,
                           QFrame, QStatusBar, QTabWidget, QTextEdit, QCalendarWidget,
                           QFileDialog, QGroupBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import logging
from datetime import datetime, timedelta
import csv
import json
import os

logger = logging.getLogger('TerranPOS')

class DateRangeSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date Range")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Quick selection buttons
        quick_select = QHBoxLayout()
        today_btn = QPushButton("Today")
        week_btn = QPushButton("This Week")
        month_btn = QPushButton("This Month")
        year_btn = QPushButton("This Year")
        
        today_btn.clicked.connect(self.select_today)
        week_btn.clicked.connect(self.select_week)
        month_btn.clicked.connect(self.select_month)
        year_btn.clicked.connect(self.select_year)
        
        quick_select.addWidget(today_btn)
        quick_select.addWidget(week_btn)
        quick_select.addWidget(month_btn)
        quick_select.addWidget(year_btn)
        layout.addLayout(quick_select)
        
        # Start date
        start_group = QGroupBox("Start Date")
        start_layout = QVBoxLayout()
        self.start_calendar = QCalendarWidget()
        start_layout.addWidget(self.start_calendar)
        start_group.setLayout(start_layout)
        layout.addWidget(start_group)
        
        # End date
        end_group = QGroupBox("End Date")
        end_layout = QVBoxLayout()
        self.end_calendar = QCalendarWidget()
        end_layout.addWidget(self.end_calendar)
        end_group.setLayout(end_layout)
        layout.addWidget(end_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
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
            QCalendarWidget {
                background-color: #333333;
                color: white;
            }
            QCalendarWidget QToolButton {
                color: white;
                background-color: #444444;
            }
            QCalendarWidget QMenu {
                background-color: #444444;
                color: white;
            }
            QCalendarWidget QSpinBox {
                background-color: #444444;
                color: white;
                selection-background-color: #666666;
            }
        """)
    
    def select_today(self):
        today = QDate.currentDate()
        self.start_calendar.setSelectedDate(today)
        self.end_calendar.setSelectedDate(today)
    
    def select_week(self):
        today = QDate.currentDate()
        start = today.addDays(-today.dayOfWeek() + 1)
        self.start_calendar.setSelectedDate(start)
        self.end_calendar.setSelectedDate(today)
    
    def select_month(self):
        today = QDate.currentDate()
        start = QDate(today.year(), today.month(), 1)
        self.start_calendar.setSelectedDate(start)
        self.end_calendar.setSelectedDate(today)
    
    def select_year(self):
        today = QDate.currentDate()
        start = QDate(today.year(), 1, 1)
        self.start_calendar.setSelectedDate(start)
        self.end_calendar.setSelectedDate(today)
    
    def get_dates(self):
        return {
            'start': self.start_calendar.selectedDate().toPyDate(),
            'end': self.end_calendar.selectedDate().toPyDate()
        }

class ReportsWindow(QMainWindow):
    def __init__(self, db_manager, current_user):
        super().__init__()
        self.db_manager = db_manager
        self.current_user = current_user
        
        # Initialize current date range with today's date
        today = datetime.now().date()
        self.current_date_range = {
            'start': today,
            'end': today
        }
        
        # Initialize UI
        self.setup_ui()
        
        # Load initial reports
        self.load_reports()
        
        # Log window access
        self.db_manager.log_user_activity(
            self.current_user['id'],
            "access",
            "reports",
            "Accessed reports window"
        )
    
    def check_permission(self, permission):
        """Check if current user has a specific permission"""
        return self.db_manager.has_permission(self.current_user['id'], permission)
    
    def generate_sales_report(self):
        if not self.check_permission('reports_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to view sales reports")
            return
        
        try:
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            
            # Generate report
            report_data = self.db_manager.generate_sales_report(start_date, end_date)
            
            # Display report
            self.display_report(report_data, "Sales Report")
            
            # Log activity
            self.db_manager.log_user_activity(
                self.current_user['id'],
                "view",
                "reports",
                f"Generated sales report from {start_date} to {end_date}"
            )
        
        except Exception as e:
            logger.error(f"Error generating sales report: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to generate sales report: {str(e)}")
    
    def generate_inventory_report(self):
        if not self.check_permission('reports_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to view inventory reports")
            return
        
        try:
            # Generate report
            report_data = self.db_manager.generate_inventory_report()
            
            # Display report
            self.display_report(report_data, "Inventory Report")
            
            # Log activity
            self.db_manager.log_user_activity(
                self.current_user['id'],
                "view",
                "reports",
                "Generated inventory report"
            )
        
        except Exception as e:
            logger.error(f"Error generating inventory report: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to generate inventory report: {str(e)}")
    
    def generate_revenue_report(self):
        if not self.check_permission('reports_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to view revenue reports")
            return
        
        try:
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            
            # Generate report
            report_data = self.db_manager.generate_revenue_report(start_date, end_date)
            
            # Display report
            self.display_report(report_data, "Revenue Report")
            
            # Log activity
            self.db_manager.log_user_activity(
                self.current_user['id'],
                "view",
                "reports",
                f"Generated revenue report from {start_date} to {end_date}"
            )
        
        except Exception as e:
            logger.error(f"Error generating revenue report: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to generate revenue report: {str(e)}")
    
    def generate_product_performance_report(self):
        if not self.check_permission('reports_view'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to view product performance reports")
            return
        
        try:
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            
            # Generate report
            report_data = self.db_manager.generate_product_performance_report(start_date, end_date)
            
            # Display report
            self.display_report(report_data, "Product Performance Report")
            
            # Log activity
            self.db_manager.log_user_activity(
                self.current_user['id'],
                "view",
                "reports",
                f"Generated product performance report from {start_date} to {end_date}"
            )
        
        except Exception as e:
            logger.error(f"Error generating product performance report: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to generate product performance report: {str(e)}")
    
    def export_report(self):
        if not self.check_permission('reports_export'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to export reports")
            return
        
        try:
            if not hasattr(self, 'current_report_data') or not self.current_report_data:
                QMessageBox.warning(self, "Warning", "Please generate a report first")
                return
            
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Export Report",
                "report_export.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_name:
                with open(file_name, 'w', newline='') as file:
                    writer = csv.writer(file)
                    
                    # Write headers
                    writer.writerow(self.current_report_data['headers'])
                    
                    # Write data
                    for row in self.current_report_data['data']:
                        writer.writerow(row)
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "export",
                    "reports",
                    f"Exported report to {file_name}"
                )
                
                self.status_bar.showMessage("Report exported successfully")
        
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}")
    
    def print_report(self):
        if not self.check_permission('reports_print'):
            QMessageBox.warning(self, "Access Denied", "You don't have permission to print reports")
            return
        
        try:
            if not hasattr(self, 'current_report_data') or not self.current_report_data:
                QMessageBox.warning(self, "Warning", "Please generate a report first")
                return
            
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                document = QTextDocument()
                html = self.generate_report_html()
                document.setHtml(html)
                document.print_(printer)
                
                # Log activity
                self.db_manager.log_user_activity(
                    self.current_user['id'],
                    "print",
                    "reports",
                    "Printed report"
                )
                
                self.status_bar.showMessage("Report printed successfully")
        
        except Exception as e:
            logger.error(f"Error printing report: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to print report: {str(e)}")
    
    def display_report(self, report_data, title):
        """Display report data in the table view"""
        self.current_report_data = report_data
        self.report_title_label.setText(title)
        
        # Clear existing table
        self.report_table.clear()
        self.report_table.setRowCount(0)
        self.report_table.setColumnCount(len(report_data['headers']))
        
        # Set headers
        self.report_table.setHorizontalHeaderLabels(report_data['headers'])
        
        # Add data
        for row_data in report_data['data']:
            row = self.report_table.rowCount()
            self.report_table.insertRow(row)
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                self.report_table.setItem(row, col, item)
        
        # Adjust column widths
        self.report_table.resizeColumnsToContents()
        
        # Update status
        self.status_bar.showMessage(f"{title} generated successfully")
    
    def setup_ui(self):
        self.setWindowTitle("Reports")
        self.setMinimumSize(1000, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Date range selector
        date_layout = QHBoxLayout()
        self.date_label = QLabel(f"Date Range: {self.format_date_range()}")
        change_date_btn = QPushButton("Change Date Range")
        change_date_btn.clicked.connect(self.change_date_range)
        date_layout.addWidget(self.date_label)
        date_layout.addWidget(change_date_btn)
        layout.addLayout(date_layout)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Sales Reports Tab
        sales_tab = QWidget()
        sales_layout = QVBoxLayout(sales_tab)
        
        # Sales summary
        sales_summary = QGroupBox("Sales Summary")
        summary_layout = QFormLayout(sales_summary)
        self.total_sales_label = QLabel("$0.00")
        self.total_transactions_label = QLabel("0")
        self.average_sale_label = QLabel("$0.00")
        summary_layout.addRow("Total Sales:", self.total_sales_label)
        summary_layout.addRow("Total Transactions:", self.total_transactions_label)
        summary_layout.addRow("Average Sale:", self.average_sale_label)
        sales_layout.addWidget(sales_summary)
        
        # Sales table
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(6)
        self.sales_table.setHorizontalHeaderLabels([
            "Date", "Receipt #", "Client", "Items", "Total", "Payment Method"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        sales_layout.addWidget(self.sales_table)
        
        # Export button for sales
        export_sales_btn = QPushButton("Export Sales Data")
        export_sales_btn.clicked.connect(lambda: self.export_data("sales"))
        sales_layout.addWidget(export_sales_btn)
        
        tabs.addTab(sales_tab, "Sales Reports")
        
        # Inventory Reports Tab
        inventory_tab = QWidget()
        inventory_layout = QVBoxLayout(inventory_tab)
        
        # Inventory summary
        inventory_summary = QGroupBox("Inventory Summary")
        inv_summary_layout = QFormLayout(inventory_summary)
        self.total_items_label = QLabel("0")
        self.low_stock_label = QLabel("0")
        self.inventory_value_label = QLabel("$0.00")
        inv_summary_layout.addRow("Total Items:", self.total_items_label)
        inv_summary_layout.addRow("Low Stock Items:", self.low_stock_label)
        inv_summary_layout.addRow("Total Inventory Value:", self.inventory_value_label)
        inventory_layout.addWidget(inventory_summary)
        
        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(6)
        self.inventory_table.setHorizontalHeaderLabels([
            "Product", "Category", "Stock", "Price", "Value", "Status"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        inventory_layout.addWidget(self.inventory_table)
        
        # Export button for inventory
        export_inventory_btn = QPushButton("Export Inventory Data")
        export_inventory_btn.clicked.connect(lambda: self.export_data("inventory"))
        inventory_layout.addWidget(export_inventory_btn)
        
        tabs.addTab(inventory_tab, "Inventory Reports")
        
        # Financial Reports Tab
        financial_tab = QWidget()
        financial_layout = QVBoxLayout(financial_tab)
        
        # Financial summary
        financial_summary = QGroupBox("Financial Summary")
        fin_summary_layout = QFormLayout(financial_summary)
        self.gross_sales_label = QLabel("$0.00")
        self.tax_collected_label = QLabel("$0.00")
        self.net_sales_label = QLabel("$0.00")
        fin_summary_layout.addRow("Gross Sales:", self.gross_sales_label)
        fin_summary_layout.addRow("Tax Collected:", self.tax_collected_label)
        fin_summary_layout.addRow("Net Sales:", self.net_sales_label)
        financial_layout.addWidget(financial_summary)
        
        # Financial table
        self.financial_table = QTableWidget()
        self.financial_table.setColumnCount(5)
        self.financial_table.setHorizontalHeaderLabels([
            "Date", "Description", "Gross Amount", "Tax", "Net Amount"
        ])
        self.financial_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        financial_layout.addWidget(self.financial_table)
        
        # Export button for financials
        export_financial_btn = QPushButton("Export Financial Data")
        export_financial_btn.clicked.connect(lambda: self.export_data("financial"))
        financial_layout.addWidget(export_financial_btn)
        
        tabs.addTab(financial_tab, "Financial Reports")
        
        # Custom Reports Tab
        custom_tab = QWidget()
        custom_layout = QVBoxLayout(custom_tab)
        
        # Report type selector
        type_layout = QHBoxLayout()
        type_label = QLabel("Report Type:")
        self.report_type = QComboBox()
        self.report_type.addItems([
            "Top Selling Products",
            "Sales by Category",
            "Sales by Payment Method",
            "Stock Movement",
            "Daily Sales Summary"
        ])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.report_type)
        custom_layout.addLayout(type_layout)
        
        # Custom report table
        self.custom_table = QTableWidget()
        custom_layout.addWidget(self.custom_table)
        
        # Generate and export buttons
        button_layout = QHBoxLayout()
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_custom_report)
        export_custom_btn = QPushButton("Export Custom Report")
        export_custom_btn.clicked.connect(lambda: self.export_data("custom"))
        button_layout.addWidget(generate_btn)
        button_layout.addWidget(export_custom_btn)
        custom_layout.addLayout(button_layout)
        
        tabs.addTab(custom_tab, "Custom Reports")
        
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
            QLabel, QGroupBox {
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
            QComboBox {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
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
    
    def format_date_range(self):
        if not hasattr(self, 'current_date_range'):
            today = datetime.now().date()
            self.current_date_range = {'start': today, 'end': today}
        return (f"{self.current_date_range['start'].strftime('%Y-%m-%d')} to "
                f"{self.current_date_range['end'].strftime('%Y-%m-%d')}")
    
    def change_date_range(self):
        dialog = DateRangeSelector(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_date_range = dialog.get_dates()
            self.date_label.setText(f"Date Range: {self.format_date_range()}")
            try:
                self.load_reports()
                self.status_bar.showMessage("Reports updated successfully")
            except Exception as e:
                logger.error(f"Error updating reports: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to update reports: {str(e)}")
    
    def load_reports(self):
        """Load all reports with current date range"""
        try:
            self.load_sales_report()
            self.load_inventory_report()
            self.load_financial_report()
            self.status_bar.showMessage("Reports loaded successfully")
        except Exception as e:
            logger.error(f"Error loading reports: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load reports: {str(e)}")
    
    def load_sales_report(self):
        try:
            # Get sales data from database
            sales_data = self.db_manager.get_sales_report(
                self.current_date_range['start'],
                self.current_date_range['end']
            )
            
            # Update summary
            total_sales = sum(sale['total_amount'] for sale in sales_data)
            total_transactions = len(sales_data)
            avg_sale = total_sales / total_transactions if total_transactions > 0 else 0
            
            self.total_sales_label.setText(f"${total_sales:.2f}")
            self.total_transactions_label.setText(str(total_transactions))
            self.average_sale_label.setText(f"${avg_sale:.2f}")
            
            # Update table
            self.sales_table.setRowCount(len(sales_data))
            for row, sale in enumerate(sales_data):
                self.sales_table.setItem(row, 0, QTableWidgetItem(sale['date']))
                self.sales_table.setItem(row, 1, QTableWidgetItem(str(sale['id'])))
                self.sales_table.setItem(row, 2, QTableWidgetItem(sale['client_name']))
                self.sales_table.setItem(row, 3, QTableWidgetItem(str(sale['items'])))
                self.sales_table.setItem(row, 4, QTableWidgetItem(f"${sale['total_amount']:.2f}"))
                self.sales_table.setItem(row, 5, QTableWidgetItem(sale['payment_method']))
        
        except Exception as e:
            logger.error(f"Error loading sales report: {str(e)}", exc_info=True)
            raise
    
    def load_inventory_report(self):
        try:
            # Get inventory data from database
            inventory_data = self.db_manager.get_inventory_report()
            
            # Update summary
            total_items = len(inventory_data)
            low_stock = sum(1 for item in inventory_data if item['status'] == 'Low Stock')
            total_value = sum(item['value'] for item in inventory_data)
            
            self.total_items_label.setText(str(total_items))
            self.low_stock_label.setText(str(low_stock))
            self.inventory_value_label.setText(f"${total_value:.2f}")
            
            # Update table
            self.inventory_table.setRowCount(len(inventory_data))
            for row, item in enumerate(inventory_data):
                self.inventory_table.setItem(row, 0, QTableWidgetItem(item['name']))
                self.inventory_table.setItem(row, 1, QTableWidgetItem(item['category']))
                self.inventory_table.setItem(row, 2, QTableWidgetItem(str(item['stock'])))
                self.inventory_table.setItem(row, 3, QTableWidgetItem(f"${item['price']:.2f}"))
                self.inventory_table.setItem(row, 4, QTableWidgetItem(f"${item['value']:.2f}"))
                
                status_item = QTableWidgetItem(item['status'])
                if item['status'] == 'Low Stock':
                    status_item.setBackground(QColor("#8B0000"))
                self.inventory_table.setItem(row, 5, status_item)
        
        except Exception as e:
            logger.error(f"Error loading inventory report: {str(e)}", exc_info=True)
            raise
    
    def load_financial_report(self):
        try:
            # Get financial data from database
            financial_data = self.db_manager.get_financial_report(
                self.current_date_range['start'],
                self.current_date_range['end']
            )
            
            # Update summary
            gross_sales = sum(trans['gross_amount'] for trans in financial_data)
            tax_collected = sum(trans['tax'] for trans in financial_data)
            net_sales = sum(trans['net_amount'] for trans in financial_data)
            
            self.gross_sales_label.setText(f"${gross_sales:.2f}")
            self.tax_collected_label.setText(f"${tax_collected:.2f}")
            self.net_sales_label.setText(f"${net_sales:.2f}")
            
            # Update table
            self.financial_table.setRowCount(len(financial_data))
            for row, trans in enumerate(financial_data):
                self.financial_table.setItem(row, 0, QTableWidgetItem(trans['date']))
                self.financial_table.setItem(row, 1, QTableWidgetItem(trans['description']))
                self.financial_table.setItem(row, 2, QTableWidgetItem(f"${trans['gross_amount']:.2f}"))
                self.financial_table.setItem(row, 3, QTableWidgetItem(f"${trans['tax']:.2f}"))
                self.financial_table.setItem(row, 4, QTableWidgetItem(f"${trans['net_amount']:.2f}"))
        
        except Exception as e:
            logger.error(f"Error loading financial report: {str(e)}", exc_info=True)
            raise
    
    def generate_custom_report(self):
        try:
            report_type = self.report_type.currentText()
            
            # Get custom report data from database
            report_data = self.db_manager.get_custom_report(
                report_type,
                self.current_date_range['start'],
                self.current_date_range['end']
            )
            
            # Configure table based on report type
            if report_type == "Top Selling Products":
                self.custom_table.setColumnCount(4)
                self.custom_table.setHorizontalHeaderLabels([
                    "Product", "Quantity Sold", "Total Revenue", "% of Sales"
                ])
            elif report_type == "Sales by Category":
                self.custom_table.setColumnCount(4)
                self.custom_table.setHorizontalHeaderLabels([
                    "Category", "Items Sold", "Total Revenue", "% of Sales"
                ])
            elif report_type == "Sales by Payment Method":
                self.custom_table.setColumnCount(3)
                self.custom_table.setHorizontalHeaderLabels([
                    "Payment Method", "Number of Sales", "Total Amount"
                ])
            elif report_type == "Stock Movement":
                self.custom_table.setColumnCount(5)
                self.custom_table.setHorizontalHeaderLabels([
                    "Product", "Initial Stock", "Received", "Sold", "Current Stock"
                ])
            elif report_type == "Daily Sales Summary":
                self.custom_table.setColumnCount(4)
                self.custom_table.setHorizontalHeaderLabels([
                    "Date", "Number of Sales", "Total Revenue", "Average Sale"
                ])
            
            # Update table
            self.custom_table.setRowCount(len(report_data))
            for row, data in enumerate(report_data):
                for col, value in enumerate(data.values()):
                    if isinstance(value, float):
                        item_text = f"${value:.2f}"
                    elif isinstance(value, (int, str)):
                        item_text = str(value)
                    else:
                        item_text = str(value)
                    
                    self.custom_table.setItem(row, col, QTableWidgetItem(item_text))
            
            self.status_bar.showMessage(f"Generated {report_type} report successfully")
        
        except Exception as e:
            logger.error(f"Error generating custom report: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to generate custom report: {str(e)}")
    
    def export_data(self, report_type):
        try:
            # Get the table based on report type
            if report_type == "sales":
                table = self.sales_table
                default_name = "sales_report"
            elif report_type == "inventory":
                table = self.inventory_table
                default_name = "inventory_report"
            elif report_type == "financial":
                table = self.financial_table
                default_name = "financial_report"
            else:  # custom
                table = self.custom_table
                default_name = f"custom_report_{self.report_type.currentText().lower().replace(' ', '_')}"
            
            # Get file name from user
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Export Report",
                f"{default_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_name:
                with open(file_name, 'w', newline='') as file:
                    writer = csv.writer(file)
                    
                    # Write headers
                    headers = []
                    for col in range(table.columnCount()):
                        headers.append(table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(table.rowCount()):
                        row_data = []
                        for col in range(table.columnCount()):
                            item = table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                self.status_bar.showMessage(f"Report exported successfully to {file_name}")
        
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}") 