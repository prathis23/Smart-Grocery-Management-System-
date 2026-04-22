#!/usr/bin/env python3
"""
Smart Grocery Inventory Management System
==========================================
Features:
- Add / update / remove grocery items
- Track quantity, unit, category, expiry date, and min-stock threshold
- Low-stock & expiry alerts
- Auto-generate a shopping list
- Search & filter items
- Persistent JSON storage
- Rich terminal UI (uses only stdlib + optional 'rich' library)
"""

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Try to use the 'rich' library for a prettier UI; fall back gracefully
# ---------------------------------------------------------------------------
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich import box
    from rich.text import Text
    from rich.columns import Columns
    RICH = True
except ImportError:
    RICH = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DATA_FILE = Path("grocery_inventory.json")
CATEGORIES = [
    "Fruits & Vegetables",
    "Dairy & Eggs",
    "Meat & Seafood",
    "Bakery & Bread",
    "Frozen Foods",
    "Beverages",
    "Snacks & Confectionery",
    "Condiments & Sauces",
    "Grains & Cereals",
    "Canned & Packaged",
    "Cleaning & Household",
    "Personal Care",
    "Other",
]
UNITS = ["kg", "g", "litre", "ml", "pieces", "dozen", "pack", "box", "bottle", "can", "bag"]
EXPIRY_WARNING_DAYS = 5   # warn if expiring within this many days

if RICH:
    console = Console()


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_data() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"items": {}, "next_id": 1}


def save_data(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def today_str() -> str:
    return date.today().isoformat()


def days_until_expiry(expiry_str: str) -> int | None:
    if not expiry_str:
        return None
    try:
        exp = date.fromisoformat(expiry_str)
        return (exp - date.today()).days
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Print helpers (rich or plain)
# ---------------------------------------------------------------------------

def print_header(title: str) -> None:
    if RICH:
        console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))
    else:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")


def print_success(msg: str) -> None:
    if RICH:
        console.print(f"[bold green]✔  {msg}[/bold green]")
    else:
        print(f"[OK] {msg}")


def print_error(msg: str) -> None:
    if RICH:
        console.print(f"[bold red]✘  {msg}[/bold red]")
    else:
        print(f"[ERROR] {msg}")


def print_warning(msg: str) -> None:
    if RICH:
        console.print(f"[bold yellow]⚠  {msg}[/bold yellow]")
    else:
        print(f"[WARN] {msg}")


def print_info(msg: str) -> None:
    if RICH:
        console.print(f"[dim]{msg}[/dim]")
    else:
        print(f"  {msg}")


def ask(prompt: str, default: str = "") -> str:
    if RICH:
        return Prompt.ask(prompt, default=default).strip()
    else:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default


def confirm(prompt: str, default: bool = False) -> bool:
    if RICH:
        return Confirm.ask(prompt, default=default)
    else:
        suffix = " [Y/n]" if default else " [y/N]"
        val = input(prompt + suffix + ": ").strip().lower()
        if val == "":
            return default
        return val in ("y", "yes")


# ---------------------------------------------------------------------------
# Core CRUD operations
# ---------------------------------------------------------------------------

def add_item(data: dict) -> None:
    print_header("Add New Item")

    name = ask("[bold]Item name[/bold]" if RICH else "Item name")
    if not name:
        print_error("Name cannot be empty.")
        return

    # Check duplicate
    for item in data["items"].values():
        if item["name"].lower() == name.lower():
            print_warning(f"'{name}' already exists (ID {item['id']}). Use 'Update' instead.")
            return

    # Category
    if RICH:
        console.print("\n[bold]Categories:[/bold]")
        for i, c in enumerate(CATEGORIES, 1):
            console.print(f"  [cyan]{i:>2}[/cyan]. {c}")
    else:
        print("\nCategories:")
        for i, c in enumerate(CATEGORIES, 1):
            print(f"  {i:>2}. {c}")

    cat_input = ask("Choose category number", "13")
    try:
        category = CATEGORIES[int(cat_input) - 1]
    except (ValueError, IndexError):
        category = CATEGORIES[-1]

    # Unit
    if RICH:
        console.print("\n[bold]Units:[/bold] " + ", ".join(f"[cyan]{u}[/cyan]" for u in UNITS))
    else:
        print("\nUnits: " + ", ".join(UNITS))
    unit = ask("Unit", "pieces")
    if unit not in UNITS:
        unit = "pieces"

    # Quantity
    qty_str = ask("Quantity", "1")
    try:
        quantity = float(qty_str)
    except ValueError:
        quantity = 1.0

    # Min threshold
    min_str = ask("Min stock threshold (reorder alert)", "1")
    try:
        min_stock = float(min_str)
    except ValueError:
        min_stock = 1.0

    # Price
    price_str = ask("Price per unit (₹)", "0")
    try:
        price = float(price_str)
    except ValueError:
        price = 0.0

    # Expiry
    expiry = ask("Expiry date (YYYY-MM-DD, leave blank if none)", "")
    if expiry:
        try:
            date.fromisoformat(expiry)
        except ValueError:
            print_warning("Invalid date format. Expiry not set.")
            expiry = ""

    item_id = str(data["next_id"])
    data["items"][item_id] = {
        "id": item_id,
        "name": name,
        "category": category,
        "unit": unit,
        "quantity": quantity,
        "min_stock": min_stock,
        "price": price,
        "expiry": expiry,
        "added_on": today_str(),
        "last_updated": today_str(),
    }
    data["next_id"] += 1
    save_data(data)
    print_success(f"'{name}' added to inventory (ID: {item_id}).")


def update_item(data: dict) -> None:
    print_header("Update Item")
    view_items(data, compact=True)
    if not data["items"]:
        return
    item_id = ask("Enter item ID to update")
    if item_id not in data["items"]:
        print_error("Item not found.")
        return

    item = data["items"][item_id]
    print_info(f"Updating: {item['name']} | Current qty: {item['quantity']} {item['unit']}")

    fields = {
        "1": "quantity",
        "2": "price",
        "3": "min_stock",
        "4": "expiry",
        "5": "name",
        "6": "unit",
    }
    if RICH:
        console.print("\n[bold]What to update?[/bold]")
        for k, v in fields.items():
            console.print(f"  [cyan]{k}[/cyan]. {v.replace('_', ' ').title()}")
    else:
        print("\nWhat to update?")
        for k, v in fields.items():
            print(f"  {k}. {v.replace('_', ' ').title()}")

    choice = ask("Choice", "1")
    field = fields.get(choice)
    if not field:
        print_error("Invalid choice.")
        return

    new_val = ask(f"New value for '{field}'", str(item[field]))
    if field in ("quantity", "price", "min_stock"):
        try:
            new_val = float(new_val)
        except ValueError:
            print_error("Must be a number.")
            return
    if field == "expiry" and new_val:
        try:
            date.fromisoformat(new_val)
        except ValueError:
            print_error("Invalid date.")
            return

    item[field] = new_val
    item["last_updated"] = today_str()
    save_data(data)
    print_success(f"'{item['name']}' updated.")


def remove_item(data: dict) -> None:
    print_header("Remove Item")
    view_items(data, compact=True)
    if not data["items"]:
        return
    item_id = ask("Enter item ID to remove")
    if item_id not in data["items"]:
        print_error("Item not found.")
        return
    name = data["items"][item_id]["name"]
    if confirm(f"Remove '{name}'?"):
        del data["items"][item_id]
        save_data(data)
        print_success(f"'{name}' removed.")
    else:
        print_info("Cancelled.")


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def view_items(data: dict, compact: bool = False, filter_fn=None) -> None:
    items = list(data["items"].values())
    if filter_fn:
        items = [i for i in items if filter_fn(i)]

    if not items:
        print_info("No items found.")
        return

    if RICH:
        tbl = Table(
            title="Grocery Inventory" if not compact else None,
            box=box.ROUNDED,
            header_style="bold magenta",
            show_lines=True,
        )
        cols = ["ID", "Name", "Category", "Qty", "Unit", "Min", "Price(₹)", "Expiry", "Status"]
        widths = [4, 20, 20, 6, 7, 5, 9, 12, 14]
        for col, w in zip(cols, widths):
            tbl.add_column(col, min_width=w, no_wrap=(col not in ("Name", "Category")))

        for item in sorted(items, key=lambda x: x["category"]):
            d = days_until_expiry(item["expiry"])
            low = item["quantity"] <= item["min_stock"]
            exp_str = item["expiry"] or "-"
            status_parts = []
            if low:
                status_parts.append("[red]LOW STOCK[/red]")
            if d is not None:
                if d < 0:
                    status_parts.append("[red]EXPIRED[/red]")
                elif d <= EXPIRY_WARNING_DAYS:
                    status_parts.append(f"[yellow]EXP {d}d[/yellow]")
            status = " | ".join(status_parts) if status_parts else "[green]OK[/green]"

            qty_str = f"{item['quantity']:.1f}".rstrip("0").rstrip(".")
            min_str = f"{item['min_stock']:.1f}".rstrip("0").rstrip(".")
            tbl.add_row(
                item["id"],
                item["name"],
                item["category"],
                f"[red]{qty_str}[/red]" if low else qty_str,
                item["unit"],
                min_str,
                f"₹{item['price']:.2f}",
                f"[red]{exp_str}[/red]" if (d is not None and d < 0) else
                (f"[yellow]{exp_str}[/yellow]" if (d is not None and d <= EXPIRY_WARNING_DAYS) else exp_str),
                status,
            )
        console.print(tbl)
    else:
        header = f"{'ID':<4} {'Name':<20} {'Category':<18} {'Qty':>5} {'Unit':<7} {'Expiry':<12} Status"
        print("\n" + header)
        print("-" * len(header))
        for item in sorted(items, key=lambda x: x["category"]):
            d = days_until_expiry(item["expiry"])
            low = item["quantity"] <= item["min_stock"]
            exp_str = item["expiry"] or "-"
            statuses = []
            if low:
                statuses.append("LOW")
            if d is not None and d < 0:
                statuses.append("EXPIRED")
            elif d is not None and d <= EXPIRY_WARNING_DAYS:
                statuses.append(f"EXP:{d}d")
            status = ",".join(statuses) if statuses else "OK"
            qty = f"{item['quantity']:.1f}".rstrip("0").rstrip(".")
            print(f"{item['id']:<4} {item['name']:<20} {item['category']:<18} {qty:>5} {item['unit']:<7} {exp_str:<12} {status}")


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

def show_alerts(data: dict) -> None:
    print_header("Smart Alerts")
    low_stock = []
    expiring_soon = []
    expired = []

    for item in data["items"].values():
        if item["quantity"] <= item["min_stock"]:
            low_stock.append(item)
        d = days_until_expiry(item["expiry"])
        if d is not None:
            if d < 0:
                expired.append((item, d))
            elif d <= EXPIRY_WARNING_DAYS:
                expiring_soon.append((item, d))

    if not low_stock and not expiring_soon and not expired:
        print_success("All items are well-stocked and fresh!")
        return

    if low_stock:
        if RICH:
            console.print("\n[bold red]🔴 Low Stock Items:[/bold red]")
            for it in low_stock:
                console.print(f"  • [yellow]{it['name']}[/yellow] — {it['quantity']} {it['unit']} (min: {it['min_stock']})")
        else:
            print("\n[LOW STOCK]")
            for it in low_stock:
                print(f"  - {it['name']}: {it['quantity']} {it['unit']} (min: {it['min_stock']})")

    if expiring_soon:
        if RICH:
            console.print("\n[bold yellow]⚠  Expiring Soon:[/bold yellow]")
            for it, d in expiring_soon:
                console.print(f"  • [yellow]{it['name']}[/yellow] — expires in [bold]{d}[/bold] day(s) ({it['expiry']})")
        else:
            print("\n[EXPIRING SOON]")
            for it, d in expiring_soon:
                print(f"  - {it['name']}: expires in {d} days ({it['expiry']})")

    if expired:
        if RICH:
            console.print("\n[bold red]💀 Expired Items:[/bold red]")
            for it, d in expired:
                console.print(f"  • [red]{it['name']}[/red] — expired {abs(d)} day(s) ago ({it['expiry']})")
        else:
            print("\n[EXPIRED]")
            for it, d in expired:
                print(f"  - {it['name']}: expired {abs(d)} days ago ({it['expiry']})")


# ---------------------------------------------------------------------------
# Shopping list
# ---------------------------------------------------------------------------

def shopping_list(data: dict) -> None:
    print_header("Auto-Generated Shopping List")
    needed = [it for it in data["items"].values() if it["quantity"] <= it["min_stock"]]
    if not needed:
        print_success("Nothing needed — you're fully stocked!")
        return

    total_est = 0.0
    if RICH:
        tbl = Table(box=box.SIMPLE_HEAVY, header_style="bold cyan")
        tbl.add_column("Item", min_width=20)
        tbl.add_column("Need", justify="right")
        tbl.add_column("Unit")
        tbl.add_column("Est. Cost (₹)", justify="right")
        for it in needed:
            need_qty = max(it["min_stock"] - it["quantity"], 1)
            est = need_qty * it["price"]
            total_est += est
            tbl.add_row(
                it["name"],
                f"{need_qty:.1f}".rstrip("0").rstrip("."),
                it["unit"],
                f"₹{est:.2f}" if it["price"] else "-",
            )
        console.print(tbl)
        console.print(f"\n[bold]Estimated Total:[/bold] [green]₹{total_est:.2f}[/green]")
    else:
        print(f"\n{'Item':<22} {'Need':>6} Unit       Est. Cost")
        print("-" * 55)
        for it in needed:
            need_qty = max(it["min_stock"] - it["quantity"], 1)
            est = need_qty * it["price"]
            total_est += est
            qty_s = f"{need_qty:.1f}".rstrip("0").rstrip(".")
            cost_s = f"₹{est:.2f}" if it["price"] else "-"
            print(f"{it['name']:<22} {qty_s:>6} {it['unit']:<10} {cost_s}")
        print(f"\nEstimated Total: ₹{total_est:.2f}")


# ---------------------------------------------------------------------------
# Search / Filter
# ---------------------------------------------------------------------------

def search_items(data: dict) -> None:
    print_header("Search & Filter")
    if RICH:
        console.print("  [cyan]1[/cyan]. Search by name\n  [cyan]2[/cyan]. Filter by category\n  [cyan]3[/cyan]. Show expired only\n  [cyan]4[/cyan]. Show low-stock only")
    else:
        print("  1. Search by name\n  2. Filter by category\n  3. Show expired only\n  4. Show low-stock only")

    choice = ask("Choice", "1")
    if choice == "1":
        term = ask("Search term").lower()
        view_items(data, filter_fn=lambda x: term in x["name"].lower())
    elif choice == "2":
        if RICH:
            for i, c in enumerate(CATEGORIES, 1):
                console.print(f"  [cyan]{i}[/cyan]. {c}")
        else:
            for i, c in enumerate(CATEGORIES, 1):
                print(f"  {i}. {c}")
        cat_n = ask("Category number", "1")
        try:
            cat = CATEGORIES[int(cat_n) - 1]
        except (ValueError, IndexError):
            cat = CATEGORIES[0]
        view_items(data, filter_fn=lambda x: x["category"] == cat)
    elif choice == "3":
        view_items(data, filter_fn=lambda x: (days_until_expiry(x["expiry"]) or 1) < 0)
    elif choice == "4":
        view_items(data, filter_fn=lambda x: x["quantity"] <= x["min_stock"])
    else:
        print_error("Invalid choice.")


# ---------------------------------------------------------------------------
# Statistics / Dashboard
# ---------------------------------------------------------------------------

def dashboard(data: dict) -> None:
    print_header("Dashboard & Statistics")
    items = list(data["items"].values())
    if not items:
        print_info("No data yet.")
        return

    total_items = len(items)
    low_count = sum(1 for it in items if it["quantity"] <= it["min_stock"])
    expired_count = sum(1 for it in items if (days_until_expiry(it["expiry"]) or 1) < 0)
    expiring_count = sum(1 for it in items if 0 <= (days_until_expiry(it["expiry"]) or -1) <= EXPIRY_WARNING_DAYS)
    total_value = sum(it["quantity"] * it["price"] for it in items)

    by_cat: dict[str, int] = {}
    for it in items:
        by_cat[it["category"]] = by_cat.get(it["category"], 0) + 1

    if RICH:
        panels = [
            Panel(f"[bold cyan]{total_items}[/bold cyan]\n[dim]Total Items[/dim]", expand=True),
            Panel(f"[bold red]{low_count}[/bold red]\n[dim]Low Stock[/dim]", expand=True),
            Panel(f"[bold yellow]{expiring_count}[/bold yellow]\n[dim]Expiring Soon[/dim]", expand=True),
            Panel(f"[bold red]{expired_count}[/bold red]\n[dim]Expired[/dim]", expand=True),
            Panel(f"[bold green]₹{total_value:,.2f}[/bold green]\n[dim]Inventory Value[/dim]", expand=True),
        ]
        console.print(Columns(panels))

        console.print("\n[bold]Items by Category:[/bold]")
        for cat, cnt in sorted(by_cat.items(), key=lambda x: -x[1]):
            bar = "█" * cnt
            console.print(f"  {cat:<30} [cyan]{bar}[/cyan] {cnt}")
    else:
        print(f"\n  Total Items   : {total_items}")
        print(f"  Low Stock     : {low_count}")
        print(f"  Expiring Soon : {expiring_count}")
        print(f"  Expired       : {expired_count}")
        print(f"  Inventory Val : ₹{total_value:,.2f}")
        print("\n  Items by Category:")
        for cat, cnt in sorted(by_cat.items(), key=lambda x: -x[1]):
            print(f"    {cat:<28} {'█'*cnt} {cnt}")


# ---------------------------------------------------------------------------
# Sample data loader
# ---------------------------------------------------------------------------

def load_sample_data(data: dict) -> None:
    if data["items"]:
        if not confirm("This will ADD sample items to existing inventory. Continue?", False):
            return
    samples = [
        ("Milk", "Dairy & Eggs", "litre", 2, 1, 60, (date.today() + timedelta(days=3)).isoformat()),
        ("Eggs", "Dairy & Eggs", "dozen", 1, 1, 80, (date.today() + timedelta(days=14)).isoformat()),
        ("Tomatoes", "Fruits & Vegetables", "kg", 0.5, 1, 30, (date.today() + timedelta(days=2)).isoformat()),
        ("Bread", "Bakery & Bread", "pieces", 0, 1, 40, (date.today() + timedelta(days=1)).isoformat()),
        ("Rice", "Grains & Cereals", "kg", 5, 2, 70, ""),
        ("Chicken", "Meat & Seafood", "kg", 0.3, 0.5, 200, (date.today() + timedelta(days=1)).isoformat()),
        ("Olive Oil", "Condiments & Sauces", "bottle", 2, 1, 350, ""),
        ("Orange Juice", "Beverages", "litre", 1, 1, 90, (date.today() - timedelta(days=2)).isoformat()),
        ("Yogurt", "Dairy & Eggs", "pieces", 3, 2, 45, (date.today() + timedelta(days=7)).isoformat()),
        ("Pasta", "Grains & Cereals", "pack", 2, 1, 55, ""),
    ]
    for s in samples:
        item_id = str(data["next_id"])
        data["items"][item_id] = {
            "id": item_id,
            "name": s[0], "category": s[1], "unit": s[2],
            "quantity": s[3], "min_stock": s[4], "price": s[5],
            "expiry": s[6], "added_on": today_str(), "last_updated": today_str(),
        }
        data["next_id"] += 1
    save_data(data)
    print_success(f"Loaded {len(samples)} sample items.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

MENU = {
    "1": ("View All Items", view_items),
    "2": ("Add Item", add_item),
    "3": ("Update Item", update_item),
    "4": ("Remove Item", remove_item),
    "5": ("Smart Alerts", show_alerts),
    "6": ("Shopping List", shopping_list),
    "7": ("Search & Filter", search_items),
    "8": ("Dashboard", dashboard),
    "9": ("Load Sample Data", load_sample_data),
    "0": ("Exit", None),
}


def main_menu(data: dict) -> None:
    if RICH:
        console.print(Panel(
            "[bold green]🛒  Smart Grocery Inventory Manager[/bold green]\n"
            "[dim]Track, alert, and plan your pantry intelligently[/dim]",
            border_style="green",
        ))
    else:
        print("\n" + "=" * 50)
        print("  Smart Grocery Inventory Manager")
        print("=" * 50)

    while True:
        if RICH:
            console.print("\n[bold]Main Menu:[/bold]")
            for k, (label, _) in MENU.items():
                icon = "🚪" if k == "0" else f"[cyan]{k}[/cyan]"
                console.print(f"  {icon}. {label}")
        else:
            print("\nMain Menu:")
            for k, (label, _) in MENU.items():
                print(f"  {k}. {label}")

        # Quick alert summary
        low = sum(1 for it in data["items"].values() if it["quantity"] <= it["min_stock"])
        expired = sum(1 for it in data["items"].values() if (days_until_expiry(it["expiry"]) or 1) < 0)
        if low or expired:
            print_warning(f"Alerts: {low} low-stock | {expired} expired")

        choice = ask("\nEnter choice", "1")
        if choice == "0":
            print_success("Goodbye! Stay stocked. 👋")
            break
        if choice not in MENU:
            print_error("Invalid option. Try again.")
            continue

        label, fn = MENU[choice]
        if fn:
            fn(data)  # type: ignore


if __name__ == "__main__":
    data = load_data()
    try:
        main_menu(data)
    except KeyboardInterrupt:
        print("\n")
        print_info("Interrupted. Bye!")