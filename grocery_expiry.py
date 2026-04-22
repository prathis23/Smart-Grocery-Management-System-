"""
Grocery Management System - Python CLI
Expiry handling with color-coded status, alerts, and CRUD operations.
"""

import json
import os
from datetime import date, datetime, timedelta

# ─── ANSI Colors ─────────────────────────────────────────────────────────────
RED    = "\033[91m"
ORANGE = "\033[93m"
YELLOW = "\033[33m"
GREEN  = "\033[92m"
BLUE   = "\033[94m"
GRAY   = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

DATA_FILE = "grocery_data.json"

# ─── Expiry Logic ─────────────────────────────────────────────────────────────

def get_expiry_status(expiry_date_str):
    """
    Returns (label, color, days_left) based on expiry date.
    Tiers:
      - Expired       : past today
      - Expires Today : 0 days left
      - Critical      : 1–3 days
      - Warning       : 4–7 days
      - Good          : 7+ days
      - No Date       : not set
    """
    if not expiry_date_str:
        return "No Date", GRAY, None

    try:
        expiry = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    except ValueError:
        return "Invalid Date", RED, None

    today = date.today()
    diff = (expiry - today).days

    if diff < 0:
        return f"Expired {abs(diff)}d ago", RED, diff
    elif diff == 0:
        return "Expires Today", ORANGE, 0
    elif diff <= 3:
        return f"{diff}d left (Critical)", YELLOW, diff
    elif diff <= 7:
        return f"{diff}d left (Soon)", GREEN, diff
    else:
        return f"{diff}d left", BLUE, diff


def is_expired(item):
    _, _, days = get_expiry_status(item.get("expiry_date", ""))
    return days is not None and days < 0


def is_expiring_soon(item, within_days=3):
    _, _, days = get_expiry_status(item.get("expiry_date", ""))
    return days is not None and 0 <= days <= within_days


# ─── Data Persistence ─────────────────────────────────────────────────────────

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_data(items):
    with open(DATA_FILE, "w") as f:
        json.dump(items, f, indent=2)


def next_id(items):
    return max((i["id"] for i in items), default=0) + 1


# ─── Display Helpers ──────────────────────────────────────────────────────────

def print_header(title):
    print(f"\n{BOLD}{'─'*60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'─'*60}{RESET}")


def print_item_row(item, index=None):
    label, color, _ = get_expiry_status(item.get("expiry_date", ""))
    prefix = f"  [{index}] " if index is not None else "   "
    expiry_display = item.get("expiry_date") or "N/A"
    print(
        f"{prefix}{BOLD}{item['name']:<20}{RESET}"
        f"  {GRAY}{item['category']:<12}{RESET}"
        f"  {item['quantity']} {item['unit']:<6}"
        f"  Exp: {expiry_display:<12}"
        f"  {color}{label}{RESET}"
    )


def print_table(items):
    if not items:
        print(f"\n  {GRAY}No items to display.{RESET}")
        return
    print(f"\n  {BOLD}{'#':<4} {'Name':<20} {'Category':<12} {'Qty':<10} {'Expiry':<14} Status{RESET}")
    print(f"  {'─'*72}")
    for i, item in enumerate(items, 1):
        print_item_row(item, i)


# ─── CRUD Operations ──────────────────────────────────────────────────────────

def add_item(items):
    print_header("ADD NEW ITEM")
    name = input("  Item name       : ").strip()
    if not name:
        print(f"  {RED}Name cannot be empty.{RESET}")
        return

    print(f"  Categories: Dairy, Produce, Meat, Bakery, Frozen, Pantry, Beverages, Other")
    category = input("  Category        : ").strip().capitalize() or "Other"

    try:
        quantity = float(input("  Quantity        : ").strip())
    except ValueError:
        print(f"  {RED}Invalid quantity.{RESET}")
        return

    unit = input("  Unit (kg/L/pcs) : ").strip() or "units"

    expiry_str = input("  Expiry date (YYYY-MM-DD, blank=skip): ").strip()
    if expiry_str:
        try:
            datetime.strptime(expiry_str, "%Y-%m-%d")
        except ValueError:
            print(f"  {RED}Invalid date format. Use YYYY-MM-DD.{RESET}")
            return

    item = {
        "id": next_id(items),
        "name": name,
        "category": category,
        "quantity": quantity,
        "unit": unit,
        "expiry_date": expiry_str,
        "added_on": str(date.today()),
    }
    items.append(item)
    save_data(items)
    print(f"\n  {GREEN}✔ '{name}' added successfully!{RESET}")


def view_all(items):
    print_header("ALL GROCERY ITEMS")
    if not items:
        print(f"  {GRAY}No items in inventory.{RESET}")
        return
    sorted_items = sorted(items, key=lambda x: (
        get_expiry_status(x.get("expiry_date", ""))[2] if get_expiry_status(x.get("expiry_date", ""))[2] is not None else 9999
    ))
    print_table(sorted_items)


def view_expiry_alerts(items):
    print_header("⚠  EXPIRY ALERTS")

    expired = [i for i in items if is_expired(i)]
    expiring_today = [i for i in items if get_expiry_status(i.get("expiry_date",""))[2] == 0]
    expiring_soon = [i for i in items if is_expiring_soon(i, 3) and not is_expired(i) and get_expiry_status(i.get("expiry_date",""))[2] != 0]

    if expired:
        print(f"\n  {RED}{BOLD}EXPIRED ({len(expired)} items){RESET}")
        print_table(expired)

    if expiring_today:
        print(f"\n  {ORANGE}{BOLD}EXPIRES TODAY ({len(expiring_today)} items){RESET}")
        print_table(expiring_today)

    if expiring_soon:
        print(f"\n  {YELLOW}{BOLD}EXPIRING WITHIN 3 DAYS ({len(expiring_soon)} items){RESET}")
        print_table(expiring_soon)

    if not expired and not expiring_today and not expiring_soon:
        print(f"\n  {GREEN}✔ All items are within safe expiry range!{RESET}")


def edit_item(items):
    print_header("EDIT ITEM")
    view_all(items)
    if not items:
        return

    try:
        item_id = int(input("\n  Enter item ID to edit: ").strip())
    except ValueError:
        print(f"  {RED}Invalid ID.{RESET}")
        return

    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        print(f"  {RED}Item with ID {item_id} not found.{RESET}")
        return

    print(f"\n  Editing: {BOLD}{item['name']}{RESET}  (press Enter to keep current value)")

    name = input(f"  Name       [{item['name']}]: ").strip()
    if name: item["name"] = name

    category = input(f"  Category   [{item['category']}]: ").strip()
    if category: item["category"] = category.capitalize()

    qty_str = input(f"  Quantity   [{item['quantity']}]: ").strip()
    if qty_str:
        try: item["quantity"] = float(qty_str)
        except ValueError: print(f"  {YELLOW}Invalid quantity, skipped.{RESET}")

    unit = input(f"  Unit       [{item['unit']}]: ").strip()
    if unit: item["unit"] = unit

    expiry = input(f"  Expiry     [{item.get('expiry_date','N/A')}] (YYYY-MM-DD): ").strip()
    if expiry:
        try:
            datetime.strptime(expiry, "%Y-%m-%d")
            item["expiry_date"] = expiry
        except ValueError:
            print(f"  {YELLOW}Invalid date, skipped.{RESET}")

    save_data(items)
    print(f"\n  {GREEN}✔ Item updated successfully!{RESET}")


def delete_item(items):
    print_header("DELETE ITEM")
    view_all(items)
    if not items:
        return

    try:
        item_id = int(input("\n  Enter item ID to delete: ").strip())
    except ValueError:
        print(f"  {RED}Invalid ID.{RESET}")
        return

    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        print(f"  {RED}Item with ID {item_id} not found.{RESET}")
        return

    confirm = input(f"  Delete '{item['name']}'? (y/n): ").strip().lower()
    if confirm == "y":
        items.remove(item)
        save_data(items)
        print(f"  {GREEN}✔ '{item['name']}' deleted.{RESET}")
    else:
        print(f"  {GRAY}Cancelled.{RESET}")


def clear_expired(items):
    print_header("CLEAR EXPIRED ITEMS")
    expired = [i for i in items if is_expired(i)]
    if not expired:
        print(f"  {GREEN}No expired items to remove.{RESET}")
        return

    print(f"\n  {RED}Found {len(expired)} expired item(s):{RESET}")
    print_table(expired)

    confirm = input(f"\n  Remove all expired items? (y/n): ").strip().lower()
    if confirm == "y":
        for item in expired:
            items.remove(item)
        save_data(items)
        print(f"  {GREEN}✔ {len(expired)} expired item(s) removed.{RESET}")
    else:
        print(f"  {GRAY}Cancelled.{RESET}")


def search_items(items):
    print_header("SEARCH ITEMS")
    query = input("  Search by name or category: ").strip().lower()
    if not query:
        return
    results = [i for i in items if query in i["name"].lower() or query in i["category"].lower()]
    print(f"\n  Found {len(results)} result(s):")
    print_table(results)


def show_summary(items):
    print_header("INVENTORY SUMMARY")
    total = len(items)
    expired_count = sum(1 for i in items if is_expired(i))
    today_count = sum(1 for i in items if get_expiry_status(i.get("expiry_date",""))[2] == 0)
    soon_count = sum(1 for i in items if is_expiring_soon(i, 3) and not is_expired(i) and get_expiry_status(i.get("expiry_date",""))[2] != 0)
    good_count = total - expired_count - today_count - soon_count

    print(f"\n  {BOLD}Total Items   :{RESET}  {total}")
    print(f"  {RED}Expired       :{RESET}  {expired_count}")
    print(f"  {ORANGE}Expires Today :{RESET}  {today_count}")
    print(f"  {YELLOW}Within 3 Days :{RESET}  {soon_count}")
    print(f"  {GREEN}Good          :{RESET}  {good_count}")

    cats = {}
    for i in items:
        cats[i["category"]] = cats.get(i["category"], 0) + 1
    if cats:
        print(f"\n  {BOLD}By Category:{RESET}")
        for cat, count in sorted(cats.items()):
            print(f"    {GRAY}{cat:<15}{RESET} {count} item(s)")


# ─── Main Menu ────────────────────────────────────────────────────────────────

def main():
    items = load_data()

    # Auto-alert on startup
    expired_count = sum(1 for i in items if is_expired(i))
    today_count = sum(1 for i in items if get_expiry_status(i.get("expiry_date", ""))[2] == 0)
    if expired_count or today_count:
        print(f"\n  {RED}{BOLD}⚠  ALERT: {expired_count} expired, {today_count} expiring today!{RESET}")

    while True:
        print(f"\n{BOLD}{'═'*40}{RESET}")
        print(f"{BOLD}   🛒  GROCERY MANAGER{RESET}")
        print(f"{BOLD}{'═'*40}{RESET}")
        print("  1. View All Items")
        print("  2. Add Item")
        print("  3. Edit Item")
        print("  4. Delete Item")
        print(f"  5. {RED}Expiry Alerts{RESET}")
        print(f"  6. {RED}Clear Expired Items{RESET}")
        print("  7. Search Items")
        print("  8. Inventory Summary")
        print("  0. Exit")
        print(f"{BOLD}{'─'*40}{RESET}")

        choice = input("  Choose option: ").strip()

        if choice == "1":
            view_all(items)
        elif choice == "2":
            add_item(items)
        elif choice == "3":
            edit_item(items)
        elif choice == "4":
            delete_item(items)
        elif choice == "5":
            view_expiry_alerts(items)
        elif choice == "6":
            clear_expired(items)
        elif choice == "7":
            search_items(items)
        elif choice == "8":
            show_summary(items)
        elif choice == "0":
            print(f"\n  {GREEN}Goodbye!{RESET}\n")
            break
        else:
            print(f"  {RED}Invalid option. Try again.{RESET}")


if __name__ == "__main__":
    main()