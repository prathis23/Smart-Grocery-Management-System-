from datetime import datetime
import json, os

EXPIRY_LOG_FILE = "expiry_log.json"


# ─────────────────────────────────────────
# SAFE FILE HELPERS
# ─────────────────────────────────────────

def load_inventory():
    """Safely load inventory from file."""
    if os.path.exists("inventory.json"):
        try:
            with open("inventory.json", "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("⚠️  Inventory file corrupted. Returning empty.")
    return {}


def save_inventory(inventory):
    """Safely save inventory to file."""
    try:
        with open("inventory.json", "w") as f:
            json.dump(inventory, f, indent=4)
    except IOError as e:
        print(f"❌ Failed to save inventory: {e}")


def load_expiry_log():
    """Safely load expiry action log."""
    if os.path.exists(EXPIRY_LOG_FILE):
        try:
            with open(EXPIRY_LOG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("⚠️  Expiry log corrupted. Starting fresh.")
    return []


def save_expiry_log(log):
    """Safely save expiry action log."""
    try:
        with open(EXPIRY_LOG_FILE, "w") as f:
            json.dump(log, f, indent=4)
    except IOError as e:
        print(f"❌ Failed to save expiry log: {e}")


# ─────────────────────────────────────────
# CORE EXPIRY LOGIC
# ─────────────────────────────────────────

def parse_expiry(date_str):
    """Safely parse expiry date string. Returns None if invalid."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def check_expiry(alert_days=3):
    """
    Check all items for expiry status.
    Returns (expired_list, expiring_soon_list)
    """
    inventory = load_inventory()

    if not inventory:
        print("📦 Inventory is empty. Nothing to check.")
        return [], []

    today         = datetime.today().date()
    expired       = []
    expiring_soon = []
    invalid_dates = []

    for name, details in inventory.items():
        expiry_str = details.get("expiry_date", "")
        expiry     = parse_expiry(expiry_str)        # Fix: safe date parse

        if expiry is None:
            invalid_dates.append(name)
            continue

        days_left = (expiry - today).days

        if days_left < 0:
            expired.append((name, abs(days_left), expiry_str))
        elif days_left <= alert_days:
            expiring_soon.append((name, days_left, expiry_str))

    # ── Print Results ──
    print("\n🔴 Expired Items:")
    if expired:
        print(f"  {'Item':<20} {'Expired':<20} {'Since'}")
        print("  " + "-" * 48)
        for name, days, date in expired:
            print(f"  ❌ {name:<20} {date:<20} {days} day(s) ago")
    else:
        print("  None — all good!")

    print(f"\n🟡 Expiring Within {alert_days} Day(s):")
    if expiring_soon:
        print(f"  {'Item':<20} {'Expiry Date':<20} {'Days Left'}")
        print("  " + "-" * 48)
        for name, days, date in expiring_soon:
            print(f"  ⚠️  {name:<20} {date:<20} {days} day(s)")
    else:
        print("  None — all good!")

    # Fix: warn about invalid date formats
    if invalid_dates:
        print(f"\n⚠️  Invalid/missing expiry dates for: {', '.join(invalid_dates)}")
        print("   Please update them using format YYYY-MM-DD.")

    return expired, expiring_soon


def remove_expired_items():
    """Remove all expired items from inventory and log the action."""
    inventory = load_inventory()
    today     = datetime.today().date()
    removed   = []

    for name in list(inventory.keys()):
        expiry_str = inventory[name].get("expiry_date", "")
        expiry     = parse_expiry(expiry_str)        # Fix: safe date parse

        if expiry is None:
            print(f"⚠️  Skipping '{name}' — invalid expiry date.")
            continue

        if expiry < today:
            removed.append({
                "item"        : name,
                "expiry_date" : expiry_str,
                "removed_on"  : str(today)
            })
            del inventory[name]

    if removed:
        save_inventory(inventory)

        # Fix: log removed items for audit trail
        log = load_expiry_log()
        log.extend(removed)
        save_expiry_log(log)

        print(f"\n🗑️  Removed {len(removed)} expired item(s):")
        for entry in removed:
            print(f"   ❌ {entry['item']} (expired: {entry['expiry_date']})")
    else:
        print("✅ No expired items to remove.")

    return removed


def update_expiry_date(name, new_date):
    """Update the expiry date of an existing inventory item."""
    inventory = load_inventory()

    # Fix: validate item exists
    if name not in inventory:
        print(f"❌ '{name}' not found in inventory.")
        return

    # Fix: validate new date format
    if parse_expiry(new_date) is None:
        print("❌ Invalid date format. Use YYYY-MM-DD (e.g. 2025-12-31).")
        return

    inventory[name]["expiry_date"] = new_date
    save_inventory(inventory)
    print(f"✅ Expiry date for '{name}' updated to {new_date}.")


def view_expiry_log():
    """Display the full log of removed expired items."""
    log = load_expiry_log()

    if not log:
        print("📋 No expiry removal history found.")
        return

    print("\n📋 Expiry Removal Log:")
    print(f"  {'Item':<20} {'Expiry Date':<16} {'Removed On'}")
    print("  " + "-" * 50)
    for entry in log:
        print(f"  🗑️  {entry['item']:<20} "
              f"{entry['expiry_date']:<16} "
              f"{entry['removed_on']}")


def expiry_summary():
    """Print a full summary: expired, expiring soon, healthy items."""
    inventory = load_inventory()
    today     = datetime.today().date()

    expired_count  = 0
    soon_count     = 0
    healthy_count  = 0
    invalid_count  = 0

    for name, details in inventory.items():
        expiry = parse_expiry(details.get("expiry_date", ""))

        if expiry is None:
            invalid_count += 1
        elif expiry < today:
            expired_count += 1
        elif (expiry - today).days <= 3:
            soon_count += 1
        else:
            healthy_count += 1

    total = len(inventory)
    print("\n📊 Expiry Summary:")
    print(f"  {'Total Items':<25} {total}")
    print(f"  {'🔴 Expired':<25} {expired_count}")
    print(f"  {'🟡 Expiring Soon (≤3d)':<25} {soon_count}")
    print(f"  {'🟢 Healthy':<25} {healthy_count}")
    print(f"  {'⚠️  Invalid Date':<25} {invalid_count}")