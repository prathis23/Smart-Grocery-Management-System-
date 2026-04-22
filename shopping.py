from inventory import load_inventory, save_inventory
import json, os

SHOPPING_FILE  = "shopping_list.json"
THRESHOLD_QTY  = 2          # suggest restock if qty falls below this

def generate_shopping_list():
    inventory = load_inventory()
    shopping_list = {}

    for name, details in inventory.items():
        if details["quantity"] <= THRESHOLD_QTY:
            needed = 5 - details["quantity"]   # restock up to 5
            shopping_list[name] = {
                "current_qty": details["quantity"],
                "unit": details["unit"],
                "suggested_buy": needed,
                "est_cost": round(needed * details["price"], 2)
            }

    with open(SHOPPING_FILE, "w") as f:
        json.dump(shopping_list, f, indent=4)

    print("\n🛒 Suggested Shopping List:")
    if shopping_list:
        total = 0
        print(f"{'Item':<20} {'Have':<8} {'Buy':<8} {'Est. Cost'}")
        print("-" * 50)
        for name, info in shopping_list.items():
            print(f"{name:<20} {info['current_qty']:<8} "
                  f"{info['suggested_buy']:<8} ₹{info['est_cost']}")
            total += info["est_cost"]
        print(f"\n💰 Total Estimated Cost: ₹{round(total, 2)}")
    else:
        print("  ✅ Stock is sufficient. Nothing to buy!")

    return shopping_list

def add_manual_item(name, quantity, unit, est_price):
    shopping_list = {}
    if os.path.exists(SHOPPING_FILE):
        with open(SHOPPING_FILE, "r") as f:
            shopping_list = json.load(f)

    shopping_list[name] = {
        "current_qty": 0,
        "unit": unit,
        "suggested_buy": quantity,
        "est_cost": round(quantity * est_price, 2)
    }
    with open(SHOPPING_FILE, "w") as f:
        json.dump(shopping_list, f, indent=4)
    print(f"✅ '{name}' added to shopping list manually.")