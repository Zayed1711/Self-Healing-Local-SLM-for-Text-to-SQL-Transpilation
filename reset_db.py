import sqlite3

# Connect to the database (in the current folder)
conn = sqlite3.connect('inventory_database.db')
cursor = conn.cursor()

# 1. Create the tables
cursor.executescript('''
CREATE TABLE IF NOT EXISTS Customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    city TEXT
);
CREATE TABLE IF NOT EXISTS Products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    price INTEGER,
    stock_quantity INTEGER
);

-- 2. Clear out any old messy data
DELETE FROM Customers;
DELETE FROM Products;

-- 3. Insert fresh dummy data
INSERT INTO Customers (customer_name, city) VALUES ('Ali', 'Dhaka'), ('Sara', 'Sylhet'), ('Rahim', 'Dhaka');
INSERT INTO Products (product_name, price, stock_quantity) VALUES ('Laptop', 50000, 10), ('Mouse', 300, 50), ('Keyboard', 800, 20), ('Monitor', 12000, 5);
''')

conn.commit()
conn.close()
print("Database perfectly rebuilt and data inserted!")