import sqlite3
from datetime import datetime
from pathlib import Path
import shutil
import hashlib
import logging

logger = logging.getLogger('TerranPOS')

class DatabaseManager:
    def __init__(self):
        self.db_path = Path("data/pos.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create inventory table with category and alert threshold
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                alert_threshold INTEGER DEFAULT 10,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        # Create stock_receiving table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_receiving (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                supplier TEXT,
                quantity INTEGER NOT NULL,
                purchase_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                notes TEXT,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES inventory (id)
            )
        ''')

        # Create sales table with client information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                nif TEXT,
                total_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create sale_items table for individual items in a sale
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                price_at_sale REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (id),
                FOREIGN KEY (product_id) REFERENCES inventory (id)
            )
        ''')

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE,
                role TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create roles table for role-based access control
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create permissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                module TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create role_permissions table (many-to-many relationship)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER,
                permission_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES roles (id),
                FOREIGN KEY (permission_id) REFERENCES permissions (id)
            )
        ''')

        # Create user_sessions table for tracking active sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT NOT NULL UNIQUE,
                ip_address TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Create user_activity_log table for audit trail
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_type TEXT NOT NULL,
                module TEXT NOT NULL,
                description TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Insert default roles
        default_roles = [
            ('admin', 'Full system access with all permissions'),
            ('manager', 'Store management access with limited system settings'),
            ('cashier', 'Basic POS and inventory operations'),
            ('inventory', 'Inventory management access')
        ]
        
        for role_name, description in default_roles:
            cursor.execute(
                "INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)",
                (role_name, description)
            )

        # Insert default permissions
        default_permissions = [
            # User Management Permissions
            ('user_view', 'View users', 'user_management'),
            ('user_create', 'Create users', 'user_management'),
            ('user_edit', 'Edit users', 'user_management'),
            ('user_delete', 'Delete users', 'user_management'),
            
            # POS Permissions
            ('pos_access', 'Access POS system', 'pos'),
            ('pos_void', 'Void transactions', 'pos'),
            ('pos_discount', 'Apply discounts', 'pos'),
            ('pos_refund', 'Process refunds', 'pos'),
            
            # Inventory Permissions
            ('inventory_view', 'View inventory', 'inventory'),
            ('inventory_add', 'Add inventory items', 'inventory'),
            ('inventory_edit', 'Edit inventory items', 'inventory'),
            ('inventory_delete', 'Delete inventory items', 'inventory'),
            
            # Report Permissions
            ('reports_view', 'View reports', 'reports'),
            ('reports_export', 'Export reports', 'reports'),
            ('reports_create', 'Create custom reports', 'reports'),
            
            # Backup Permissions
            ('backup_create', 'Create backups', 'backup'),
            ('backup_restore', 'Restore backups', 'backup'),
            
            # Settings Permissions
            ('settings_view', 'View settings', 'settings'),
            ('settings_edit', 'Edit settings', 'settings')
        ]
        
        for perm_name, description, module in default_permissions:
            cursor.execute(
                "INSERT OR IGNORE INTO permissions (name, description, module) VALUES (?, ?, ?)",
                (perm_name, description, module)
            )

        # Assign default permissions to roles
        # Get role IDs
        cursor.execute("SELECT id, name FROM roles")
        roles = {name: id for id, name in cursor.fetchall()}
        
        # Get permission IDs
        cursor.execute("SELECT id, name FROM permissions")
        permissions = {name: id for id, name in cursor.fetchall()}
        
        # Define role permissions
        role_permissions = {
            'admin': [perm[0] for perm in default_permissions],  # Admin gets all permissions
            'manager': [
                'pos_access', 'pos_void', 'pos_discount', 'pos_refund',
                'inventory_view', 'inventory_add', 'inventory_edit',
                'reports_view', 'reports_export',
                'settings_view',
                'user_view'
            ],
            'cashier': [
                'pos_access',
                'inventory_view',
                'reports_view'
            ],
            'inventory': [
                'inventory_view', 'inventory_add', 'inventory_edit',
                'reports_view'
            ]
        }
        
        # Assign permissions to roles
        for role_name, perms in role_permissions.items():
            role_id = roles[role_name]
            for perm_name in perms:
                perm_id = permissions[perm_name]
                cursor.execute(
                    "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                    (role_id, perm_id)
                )

        # Create default root user if not exists
        root_password = "terran_root_2024"  # This should be changed on first login
        root_password_hash = hashlib.sha256(root_password.encode()).hexdigest()
        
        cursor.execute(
            """INSERT OR IGNORE INTO users 
               (username, password_hash, full_name, email, role) 
               VALUES (?, ?, ?, ?, ?)""",
            ("root", root_password_hash, "Root Administrator", "root@terransystems.local", "admin")
        )
        
        # Insert default category if it doesn't exist
        cursor.execute(
            "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
            ("General", "Default category for all products")
        )
        
        # Insert preset categories
        preset_categories = [
            ('Electronics', 'Electronic devices and accessories'),
            ('Groceries', 'Food and household consumables'),
            ('Clothing', 'Apparel and fashion items'),
            ('Home & Garden', 'Home improvement and gardening supplies'),
            ('Beauty & Personal Care', 'Cosmetics and personal hygiene products'),
            ('Sports & Outdoors', 'Sporting goods and outdoor equipment'),
            ('Books & Stationery', 'Books, office supplies, and stationery items'),
            ('Toys & Games', 'Toys, games, and entertainment items'),
            ('Automotive', 'Car parts and accessories'),
            ('Health & Wellness', 'Health supplements and medical supplies'),
            ('Pet Supplies', 'Pet food and accessories'),
            ('Furniture', 'Home and office furniture'),
            ('Beverages', 'Drinks and liquid refreshments'),
            ('Snacks', 'Light food and snack items'),
            ('Cleaning Supplies', 'Cleaning products and materials'),
            ('Tools & Hardware', 'Tools and construction materials'),
            ('Baby & Kids', 'Baby care and children\'s items'),
            ('Jewelry & Accessories', 'Jewelry and fashion accessories'),
            ('Arts & Crafts', 'Art supplies and craft materials'),
            ('Kitchen & Dining', 'Kitchen appliances and dining items')
        ]
        
        for name, description in preset_categories:
            cursor.execute(
                "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
                (name, description)
            )
        
        self.conn.commit()

    # Category Management
    def add_category(self, name: str, description: str = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, description)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_category(self, id: int, name: str, description: str = None) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE categories SET name=?, description=? WHERE id=?",
            (name, description, id)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_category(self, id: int) -> bool:
        cursor = self.conn.cursor()
        # Move products to default category first
        cursor.execute(
            "UPDATE inventory SET category_id=1 WHERE category_id=?",
            (id,)
        )
        cursor.execute("DELETE FROM categories WHERE id=?", (id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_all_categories(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name")
        return cursor.fetchall()

    # Stock Receiving
    def add_stock_receiving(self, product_id: int, supplier: str, quantity: int,
                          purchase_price: float, selling_price: float, notes: str = None) -> int:
        cursor = self.conn.cursor()
        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Add stock receiving record
            cursor.execute(
                """INSERT INTO stock_receiving 
                   (product_id, supplier, quantity, purchase_price, selling_price, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (product_id, supplier, quantity, purchase_price, selling_price, notes)
            )
            
            # Update product quantity and price
            cursor.execute(
                """UPDATE inventory 
                   SET quantity = quantity + ?,
                       price = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (quantity, selling_price, product_id)
            )
            
            # Commit transaction
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e

    def get_stock_history(self, product_id: int = None, start_date=None, end_date=None):
        cursor = self.conn.cursor()
        query = """
            SELECT sr.*, i.name as product_name
            FROM stock_receiving sr
            JOIN inventory i ON sr.product_id = i.id
            WHERE 1=1
        """
        params = []
        
        if product_id:
            query += " AND sr.product_id = ?"
            params.append(product_id)
        
        if start_date:
            query += " AND sr.received_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND sr.received_at <= ?"
            params.append(end_date)
        
        query += " ORDER BY sr.received_at DESC"
        
        cursor.execute(query, params)
        return cursor.fetchall()

    # Inventory Management
    def add_product(self, name: str, quantity: int, price: float, category_id: int = 1,
                   alert_threshold: int = 10, description: str = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO inventory 
               (name, category_id, quantity, price, alert_threshold, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, category_id, quantity, price, alert_threshold, description)
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_product(self, id: int, name: str, quantity: int, price: float,
                      category_id: int = None, alert_threshold: int = None,
                      description: str = None) -> bool:
        cursor = self.conn.cursor()
        
        # Get current product data
        cursor.execute("SELECT * FROM inventory WHERE id=?", (id,))
        current = cursor.fetchone()
        if not current:
            return False
        
        # Use current values if new ones aren't provided
        category_id = category_id if category_id is not None else current[2]
        alert_threshold = alert_threshold if alert_threshold is not None else current[5]
        description = description if description is not None else current[6]
        
        cursor.execute(
            """UPDATE inventory 
               SET name=?, category_id=?, quantity=?, price=?,
                   alert_threshold=?, description=?, updated_at=CURRENT_TIMESTAMP 
               WHERE id=?""",
            (name, category_id, quantity, price, alert_threshold, description, id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def remove_product(self, id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE id=?", (id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_product(self, id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, c.name as category_name
               FROM inventory i
               JOIN categories c ON i.category_id = c.id
               WHERE i.id = ?""",
            (id,)
        )
        return cursor.fetchone()

    def get_all_products(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, c.name as category_name
               FROM inventory i
               JOIN categories c ON i.category_id = c.id
               ORDER BY i.name"""
        )
        return cursor.fetchall()

    def get_low_stock_products(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, c.name as category_name
               FROM inventory i
               JOIN categories c ON i.category_id = c.id
               WHERE i.quantity <= i.alert_threshold
               ORDER BY i.name"""
        )
        return cursor.fetchall()

    def get_products_by_category(self, category_id: int):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, c.name as category_name
               FROM inventory i
               JOIN categories c ON i.category_id = c.id
               WHERE i.category_id = ?
               ORDER BY i.name""",
            (category_id,)
        )
        return cursor.fetchall()

    def search_products(self, search_term: str):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT i.*, c.name as category_name
               FROM inventory i
               JOIN categories c ON i.category_id = c.id
               WHERE i.name LIKE ? OR i.description LIKE ?
               ORDER BY i.name""",
            (f"%{search_term}%", f"%{search_term}%")
        )
        return cursor.fetchall()

    def create_sale(self, cart_items, client_name=None, client_nif=None):
        cursor = self.conn.cursor()
        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Calculate total amount
            total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
            
            # Create sale record
            cursor.execute(
                """INSERT INTO sales (client_name, nif, total_amount)
                   VALUES (?, ?, ?)""",
                (client_name, client_nif, total_amount)
            )
            sale_id = cursor.lastrowid
            
            # Add sale items and update inventory
            for item in cart_items:
                # Add sale item
                cursor.execute(
                    """INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale)
                       VALUES (?, ?, ?, ?)""",
                    (sale_id, item['id'], item['quantity'], item['price'])
                )
                
                # Update inventory quantity
                cursor.execute(
                    """UPDATE inventory
                       SET quantity = quantity - ?,
                           updated_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (item['quantity'], item['id'])
                )
                
                # Check if we have enough stock
                cursor.execute("SELECT quantity FROM inventory WHERE id = ?", (item['id'],))
                remaining_stock = cursor.fetchone()[0]
                if remaining_stock < 0:
                    raise ValueError(f"Insufficient stock for product ID {item['id']}")
            
            # Commit transaction
            self.conn.commit()
            return sale_id
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e

    def get_sale_details(self, sale_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT 
                s.id as sale_id,
                s.client_name,
                s.nif,
                s.total_amount,
                s.created_at,
                si.quantity,
                si.price_at_sale,
                i.name as product_name
               FROM sales s
               JOIN sale_items si ON s.id = si.sale_id
               JOIN inventory i ON si.product_id = i.id
               WHERE s.id = ?""",
            (sale_id,)
        )
        return cursor.fetchall()

    # Report Functions
    def get_sales_report(self, start_date, end_date):
        """Get sales report data for the given date range"""
        cursor = self.conn.cursor()
        try:
            query = """
                SELECT 
                    s.id,
                    s.created_at as date,
                    s.client_name,
                    COUNT(si.id) as items,
                    s.total_amount,
                    GROUP_CONCAT(DISTINCT i.name) as products,
                    'Cash' as payment_method
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                LEFT JOIN inventory i ON si.product_id = i.id
                WHERE s.created_at BETWEEN ? AND ?
                GROUP BY s.id
                ORDER BY s.created_at DESC
            """
            cursor.execute(query, (start_date, end_date))
            
            # Convert to list of dictionaries for easier handling
            columns = ['id', 'date', 'client_name', 'items', 'total_amount', 'products', 'payment_method']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"Error getting sales report: {str(e)}")
            raise

    def get_inventory_report(self):
        """Get current inventory status report"""
        cursor = self.conn.cursor()
        try:
            query = """
                SELECT 
                    i.name,
                    c.name as category,
                    i.quantity as stock,
                    i.price,
                    i.quantity * i.price as value,
                    CASE 
                        WHEN i.quantity <= i.alert_threshold THEN 'Low Stock'
                        ELSE 'Normal'
                    END as status
                FROM inventory i
                JOIN categories c ON i.category_id = c.id
                ORDER BY i.name
            """
            cursor.execute(query)
            
            # Convert to list of dictionaries
            columns = ['name', 'category', 'stock', 'price', 'value', 'status']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"Error getting inventory report: {str(e)}")
            raise

    def get_financial_report(self, start_date, end_date):
        """Get financial report for the given date range"""
        cursor = self.conn.cursor()
        try:
            query = """
                SELECT 
                    s.created_at as date,
                    GROUP_CONCAT(i.name) as description,
                    s.total_amount as gross_amount,
                    s.total_amount * 0.23 as tax,
                    s.total_amount * 0.77 as net_amount
                FROM sales s
                LEFT JOIN sale_items si ON s.id = si.sale_id
                LEFT JOIN inventory i ON si.product_id = i.id
                WHERE s.created_at BETWEEN ? AND ?
                GROUP BY s.id
                ORDER BY s.created_at DESC
            """
            cursor.execute(query, (start_date, end_date))
            
            # Convert to list of dictionaries
            columns = ['date', 'description', 'gross_amount', 'tax', 'net_amount']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"Error getting financial report: {str(e)}")
            raise

    def get_custom_report(self, report_type, start_date, end_date):
        """Get custom report based on type and date range"""
        cursor = self.conn.cursor()
        try:
            if report_type == "Top Selling Products":
                query = """
                    SELECT 
                        i.name as product,
                        SUM(si.quantity) as quantity_sold,
                        SUM(si.quantity * si.price_at_sale) as total_revenue,
                        (SUM(si.quantity * si.price_at_sale) * 100.0 / 
                            (SELECT SUM(total_amount) FROM sales WHERE created_at BETWEEN ? AND ?)) 
                        as sales_percentage
                    FROM sale_items si
                    JOIN inventory i ON si.product_id = i.id
                    JOIN sales s ON si.sale_id = s.id
                    WHERE s.created_at BETWEEN ? AND ?
                    GROUP BY i.id
                    ORDER BY quantity_sold DESC
                """
                cursor.execute(query, (start_date, end_date, start_date, end_date))
                columns = ['product', 'quantity_sold', 'total_revenue', 'sales_percentage']
            
            elif report_type == "Sales by Category":
                query = """
                    SELECT 
                        c.name as category,
                        SUM(si.quantity) as items_sold,
                        SUM(si.quantity * si.price_at_sale) as total_revenue,
                        (SUM(si.quantity * si.price_at_sale) * 100.0 / 
                            (SELECT SUM(total_amount) FROM sales WHERE created_at BETWEEN ? AND ?)) 
                        as sales_percentage
                    FROM sale_items si
                    JOIN inventory i ON si.product_id = i.id
                    JOIN categories c ON i.category_id = c.id
                    JOIN sales s ON si.sale_id = s.id
                    WHERE s.created_at BETWEEN ? AND ?
                    GROUP BY c.id
                    ORDER BY total_revenue DESC
                """
                cursor.execute(query, (start_date, end_date, start_date, end_date))
                columns = ['category', 'items_sold', 'total_revenue', 'sales_percentage']
            
            elif report_type == "Daily Sales Summary":
                query = """
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as number_of_sales,
                        SUM(total_amount) as total_revenue,
                        AVG(total_amount) as average_sale
                    FROM sales
                    WHERE created_at BETWEEN ? AND ?
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """
                cursor.execute(query, (start_date, end_date))
                columns = ['date', 'number_of_sales', 'total_revenue', 'average_sale']
            
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            # Convert to list of dictionaries
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        except Exception as e:
            logger.error(f"Error getting custom report: {str(e)}")
            raise

    def backup_database(self, backup_file):
        """Create a backup of the database."""
        try:
            # Close current connection
            self.conn.close()
            
            # Copy database file
            shutil.copy2(str(self.db_path), backup_file)
            
            # Reopen connection
            self.conn = sqlite3.connect(str(self.db_path))
            
            return True
        except Exception as e:
            # Ensure connection is reopened even if backup fails
            self.conn = sqlite3.connect(str(self.db_path))
            raise e

    def restore_database(self, backup_file):
        """Restore the database from a backup file."""
        try:
            # Close current connection
            self.conn.close()
            
            # Verify backup file
            test_conn = sqlite3.connect(backup_file)
            test_conn.close()
            
            # Replace current database with backup
            shutil.copy2(backup_file, str(self.db_path))
            
            # Reopen connection
            self.conn = sqlite3.connect(str(self.db_path))
            
            return True
        except Exception as e:
            # Ensure connection is reopened even if restore fails
            self.conn = sqlite3.connect(str(self.db_path))
            raise e

    # User Management Methods
    def create_user(self, username: str, password: str, full_name: str, email: str, role: str) -> int:
        """Create a new user."""
        cursor = self.conn.cursor()
        try:
            # Hash the password
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute(
                """INSERT INTO users 
                   (username, password_hash, full_name, email, role)
                   VALUES (?, ?, ?, ?, ?)""",
                (username, password_hash, full_name, email, role)
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    def authenticate_user(self, username: str, password: str) -> dict:
        """Authenticate a user and return user data if successful."""
        cursor = self.conn.cursor()
        try:
            # Hash the provided password
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute(
                """SELECT id, username, full_name, email, role, is_active 
                   FROM users 
                   WHERE username = ? AND password_hash = ?""",
                (username, password_hash)
            )
            user = cursor.fetchone()
            
            if user and user[5]:  # Check if user exists and is active
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user[0],)
                )
                self.conn.commit()
                
                return {
                    'id': user[0],
                    'username': user[1],
                    'full_name': user[2],
                    'email': user[3],
                    'role': user[4]
                }
            return None
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            raise

    def create_user_session(self, user_id: int, ip_address: str) -> str:
        """Create a new session for a user and return the session token."""
        cursor = self.conn.cursor()
        try:
            import uuid
            import hashlib
            
            # Generate a unique session token
            session_token = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
            
            cursor.execute(
                """INSERT INTO user_sessions 
                   (user_id, session_token, ip_address)
                   VALUES (?, ?, ?)""",
                (user_id, session_token, ip_address)
            )
            self.conn.commit()
            return session_token
        except Exception as e:
            logger.error(f"Error creating user session: {str(e)}")
            raise

    def validate_session(self, session_token: str) -> dict:
        """Validate a session token and return user data if valid."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """SELECT u.id, u.username, u.full_name, u.role, u.is_active
                   FROM user_sessions s
                   JOIN users u ON s.user_id = u.id
                   WHERE s.session_token = ? AND s.is_active = TRUE""",
                (session_token,)
            )
            session = cursor.fetchone()
            
            if session and session[4]:  # Check if session exists and user is active
                # Update last activity
                cursor.execute(
                    """UPDATE user_sessions 
                       SET last_activity = CURRENT_TIMESTAMP 
                       WHERE session_token = ?""",
                    (session_token,)
                )
                self.conn.commit()
                
                return {
                    'id': session[0],
                    'username': session[1],
                    'full_name': session[2],
                    'role': session[3]
                }
            return None
        except Exception as e:
            logger.error(f"Error validating session: {str(e)}")
            raise

    def end_session(self, session_token: str) -> bool:
        """End a user session."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "UPDATE user_sessions SET is_active = FALSE WHERE session_token = ?",
                (session_token,)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            raise

    def get_user_permissions(self, user_id: int) -> list:
        """Get all permissions for a user based on their role."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """SELECT p.name, p.description, p.module
                   FROM users u
                   JOIN roles r ON u.role = r.name
                   JOIN role_permissions rp ON r.id = rp.role_id
                   JOIN permissions p ON rp.permission_id = p.id
                   WHERE u.id = ?""",
                (user_id,)
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}")
            raise

    def has_permission(self, user_id: int, permission_name: str) -> bool:
        """Check if a user has a specific permission."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """SELECT COUNT(*)
                   FROM users u
                   JOIN roles r ON u.role = r.name
                   JOIN role_permissions rp ON r.id = rp.role_id
                   JOIN permissions p ON rp.permission_id = p.id
                   WHERE u.id = ? AND p.name = ?""",
                (user_id, permission_name)
            )
            return cursor.fetchone()[0] > 0
        except Exception as e:
            logger.error(f"Error checking user permission: {str(e)}")
            raise

    def log_user_activity(self, user_id: int, activity_type: str, module: str, 
                         description: str, ip_address: str = None):
        """Log user activity for audit purposes."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO user_activity_log 
                   (user_id, activity_type, module, description, ip_address)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, activity_type, module, description, ip_address)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error logging user activity: {str(e)}")
            raise

    def get_user_activity_log(self, user_id: int = None, start_date=None, end_date=None) -> list:
        """Get user activity log with optional filters."""
        cursor = self.conn.cursor()
        try:
            query = """
                SELECT u.username, l.activity_type, l.module, l.description, 
                       l.ip_address, l.timestamp
                FROM user_activity_log l
                JOIN users u ON l.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if user_id:
                query += " AND l.user_id = ?"
                params.append(user_id)
            
            if start_date:
                query += " AND l.timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND l.timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY l.timestamp DESC"
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting user activity log: {str(e)}")
            raise

    def update_user(self, user_id: int, full_name: str = None, email: str = None, 
                   role: str = None, is_active: bool = None) -> bool:
        """Update user information."""
        cursor = self.conn.cursor()
        try:
            updates = []
            params = []
            
            if full_name is not None:
                updates.append("full_name = ?")
                params.append(full_name)
            
            if email is not None:
                updates.append("email = ?")
                params.append(email)
            
            if role is not None:
                updates.append("role = ?")
                params.append(role)
            
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                params.append(user_id)
                
                cursor.execute(query, params)
                self.conn.commit()
                return cursor.rowcount > 0
            return False
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise

    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change a user's password."""
        cursor = self.conn.cursor()
        try:
            # If current_password is None, skip verification (used for admin reset)
            if current_password is not None:
                # Verify current password
                current_hash = hashlib.sha256(current_password.encode()).hexdigest()
                cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE id = ? AND password_hash = ?",
                    (user_id, current_hash)
                )
                
                if cursor.fetchone()[0] == 0:
                    return False
            
            # Update to new password
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute(
                """UPDATE users 
                   SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (new_hash, user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            raise

    def get_all_users(self) -> list:
        """Get all users in the system."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """SELECT id, username, full_name, email, role, is_active, 
                          last_login, created_at
                   FROM users
                   ORDER BY username"""
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            raise

    def get_all_roles(self) -> list:
        """Get all roles in the system."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM roles ORDER BY name")
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting roles: {str(e)}")
            raise

    def get_role_permissions(self, role_id: int) -> list:
        """Get all permissions assigned to a role."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """SELECT p.name, p.description, p.module
                   FROM role_permissions rp
                   JOIN permissions p ON rp.permission_id = p.id
                   WHERE rp.role_id = ?
                   ORDER BY p.module, p.name""",
                (role_id,)
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting role permissions: {str(e)}")
            raise

    def get_setting(self, key: str) -> str:
        """Get a setting value from the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def update_setting(self, key: str, value: str) -> bool:
        """Update or insert a setting value"""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO settings (key, value, updated_at) 
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            (key, value)
        )
        self.conn.commit()
        return True

    def __del__(self):
        self.conn.close() 