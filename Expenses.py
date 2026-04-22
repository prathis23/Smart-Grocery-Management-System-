import sqlite3
import random

# ---------------- DATABASE SETUP ----------------
conn = sqlite3.connect("grocery.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS groceries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    quantity INTEGER,
    price REAL,
    total REAL
)
''')
conn.commit()

# ---------------- GLOBAL ----------------
budget_limit = 1000   # You can change this
grocery_list = []

# ---------------- API SIMULATION ----------------
def get_product_price(product):
    # Simulating API price (random)
    price = random.randint(10, 100)
    print(f"(Auto price fetched for {product}: {price})")
    return price

# ---------------- ADD ITEM ----------------
def add_item():
    name = input("Enter item name: ")
    quantity = int(input("Enter quantity: "))

    choice = input("Fetch price automatically? (y/n): ")

    if choice.lower() == 'y':
        price = get_product_price(name)
    else:
        price = float(input("Enter price per item: "))

    total = quantity * price

    item = {
        "name": name,
        "quantity": quantity,
        "price": price,
        "total": total
    }

    grocery_list.append(item)

    # Save to DB
    cursor.execute("INSERT INTO groceries (name, quantity, price, total) VALUES (?, ?, ?, ?)",
                   (name, quantity, price, total))
    conn.commit()

    print("✅ Item added successfully!\n")

# ---------------- VIEW EXPENSE ----------------
def view_expenses():
    total_expense = 0
    print("\n--- Grocery Expenses ---")

    for item in grocery_list:
        print(f"{item['name']} - {item['quantity']} x {item['price']} = {item['total']}")
        total_expense += item['total']

    print(f"\nTotal Expense: {total_expense}")

    # Budget alert
    if total_expense > budget_limit:
        print("⚠️ Budget exceeded!")
    else:
        print("✅ Within budget")

# ---------------- VIEW FROM DATABASE ----------------
def view_from_db():
    print("\n--- Data from Database ---")
    cursor.execute("SELECT * FROM groceries")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

# ---------------- DELETE ITEM ----------------
def delete_item():
    name = input("Enter item name to delete: ")
    
    cursor.execute("DELETE FROM groceries WHERE name=?", (name,))
    conn.commit()
    
    print("🗑️ Item deleted from database")

# ---------------- MAIN MENU ----------------
def main():
    while True:
        print("\n====== SMART GROCERY SYSTEM ======")
        print("1. Add Item")
        print("2. View Expenses")
        print("3. View Database")
        print("4. Delete Item")
        print("5. Exit")

        choice = input("Enter choice: ")

        if choice == '1':
            add_item()
        elif choice == '2':
            view_expenses()
        elif choice == '3':
            view_from_db()
        elif choice == '4':
            delete_item()
        elif choice == '5':
            print("Exiting... Thank you!")
            break
        else:
            print("❌ Invalid choice")

# ---------------- RUN ----------------
main()
