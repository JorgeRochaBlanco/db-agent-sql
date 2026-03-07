"""Create a demo SQLite database with sample data."""

import sqlite3
from datetime import datetime, timedelta
import random

def create_demo_database(db_path: str = "./demo_database.db"):
    """Create demo database with sample data."""
    
    print(f"Creating demo database at {db_path}...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS order_items")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Create users table
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            country TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create products table
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create orders table
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create order_items table
    cursor.execute("""
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    # Insert sample users
    users = [
        ("Alice Johnson", "alice@example.com", "USA", 1),
        ("Bob Smith", "bob@example.com", "UK", 1),
        ("Charlie Brown", "charlie@example.com", "Canada", 1),
        ("Diana Prince", "diana@example.com", "USA", 1),
        ("Eve Wilson", "eve@example.com", "Australia", 0),
        ("Frank Miller", "frank@example.com", "Germany", 1),
        ("Grace Lee", "grace@example.com", "South Korea", 1),
        ("Henry Davis", "henry@example.com", "France", 1),
        ("Iris Chen", "iris@example.com", "China", 1),
        ("Jack Taylor", "jack@example.com", "USA", 0),
    ]
    
    cursor.executemany(
        "INSERT INTO users (name, email, country, active) VALUES (?, ?, ?, ?)",
        users
    )
    
    # Insert sample products
    products = [
        ("Laptop Pro", "Electronics", 1299.99, 50),
        ("Wireless Mouse", "Electronics", 29.99, 200),
        ("Mechanical Keyboard", "Electronics", 149.99, 100),
        ("USB-C Hub", "Electronics", 49.99, 150),
        ("Monitor 27\"", "Electronics", 399.99, 75),
        ("Desk Chair", "Furniture", 299.99, 30),
        ("Standing Desk", "Furniture", 599.99, 20),
        ("Desk Lamp", "Furniture", 79.99, 100),
        ("Notebook Set", "Stationery", 19.99, 500),
        ("Pen Collection", "Stationery", 24.99, 300),
        ("Headphones", "Electronics", 199.99, 80),
        ("Webcam HD", "Electronics", 89.99, 60),
        ("Phone Stand", "Accessories", 15.99, 250),
        ("Cable Organizer", "Accessories", 12.99, 400),
        ("Laptop Bag", "Accessories", 59.99, 120),
    ]
    
    cursor.executemany(
        "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
        products
    )
    
    # Insert sample orders
    base_date = datetime.now() - timedelta(days=90)
    
    for i in range(50):
        user_id = random.randint(1, 10)
        status = random.choice(['completed', 'completed', 'completed', 'pending', 'cancelled'])
        created_at = base_date + timedelta(days=random.randint(0, 90))
        
        # Create order
        cursor.execute(
            "INSERT INTO orders (user_id, total, status, created_at) VALUES (?, ?, ?, ?)",
            (user_id, 0, status, created_at)  # Total will be updated
        )
        order_id = cursor.lastrowid
        
        # Add order items
        num_items = random.randint(1, 5)
        total = 0
        
        for _ in range(num_items):
            product_id = random.randint(1, 15)
            quantity = random.randint(1, 3)
            
            # Get product price
            cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
            price = cursor.fetchone()[0]
            
            item_total = price * quantity
            total += item_total
            
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, product_id, quantity, price)
            )
        
        # Update order total
        cursor.execute("UPDATE orders SET total = ? WHERE id = ?", (total, order_id))
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("✅ Demo database created successfully!")
    print(f"\nDatabase: {db_path}")
    print(f"Tables: users, products, orders, order_items")
    print(f"Sample data: {len(users)} users, {len(products)} products, 50 orders")
    print("\nYou can now use this database in the Streamlit demo!")


if __name__ == "__main__":
    create_demo_database()
