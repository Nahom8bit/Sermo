import sys
from PyQt6.QtWidgets import QApplication
from database.db_manager import DatabaseManager
from views.main_window import MainWindow

def main():
    # Create the application
    app = QApplication(sys.argv)
    
    # Initialize database
    db_manager = DatabaseManager()
    
    # Create main window (it will show login window)
    window = MainWindow(db_manager)
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 