# Smart-Grocery-Management-System-
People forget what groceries they have, waste food, and don’t track expenses. Build a system that:  Tracks grocery items Alerts expiry dates Suggests shopping list Tracks spending



Here’s a **clear, real-world way to split 4 people in GitHub** so your team works smoothly (like in a software company).

---

# 🚀 1. Create the Repository

One person (Team Lead) creates a repo on GitHub

### Steps:

* Go to GitHub → New Repository
* Name: `grocery-system` (or your project)
* Click **Settings → Collaborators → Add people**
* Add all 3 teammates

---

# 👥 2. Assign Roles (Very Important)

Don’t let everyone do everything → it creates confusion.

### Suggested split for 4 people:

| Person   | Role                   | Work                    |
| -------- | ---------------------- | ----------------------- |
| Person 1 | Inventory              | Add/remove/update items |
| Person 2 | Expiry                 | Handle expiry logic     |
| Person 3 | Shopping               | Generate shopping list  |
| Person 4 | Expenses + Integration | Cost + main.py          |

---

# 🌿 3. Use Branches (Core Concept)

Each person MUST work in their own branch (never directly in `main`).

### Branch structure:

```
main
 ├── inventory-feature
 ├── expiry-feature
 ├── shopping-feature
 └── expense-feature
```

---

# 💻 4. Each Person Workflow

## 🔹 Step 1: Clone Repo

```bash
git clone https://github.com/your-repo.git
cd grocery-system
```

## 🔹 Step 2: Create Your Branch

Example (Person 1):

```bash
git checkout -b inventory-feature
```

---

## 🔹 Step 3: Do Your Work

* Create your file (example: `inventory.py`)
* Write your code

---

## 🔹 Step 4: Commit & Push

```bash
git add .
git commit -m "Added inventory module"
git push origin inventory-feature
```

---

# 🔄 5. Create Pull Request (PR)

* Go to GitHub
* Click **Compare & Pull Request**
* Add description
* Click **Create PR**

---

# ✅ 6. Review & Merge

👉 Person 4 (or Team Lead):

* Reviews code
* Fix conflicts if needed
* Click **Merge**

---

# 🔁 7. Sync with Main (VERY IMPORTANT)

After merge, everyone must update:

```bash
git checkout main
git pull origin main
```

---

# ⚠️ Common Mistakes (Avoid This)

❌ Working directly in `main`
❌ Overwriting others’ code
❌ Not pulling latest changes
❌ No clear role division

---

# 🧠 Pro Team Setup (Like Real Companies)

## Use Issues

* Go to **Issues tab**
* Create tasks like:

  * “Build inventory module”
  * “Add expiry checker”

## Use Labels

* `bug`
* `feature`
* `enhancement`

---

# 🏆 Simple Flow Summary

1. Create repo
2. Add 4 members
3. Each creates own branch
4. Push code
5. Create PR
6. Merge to main

---


Just tell 👍
