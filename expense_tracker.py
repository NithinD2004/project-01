import sqlite3
import sys
from datetime import datetime

# FIX 1: Windows consoles often can't print the ₹ symbol (UnicodeEncodeError)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    date TEXT NOT NULL
)
""")
conn.commit()


# ---------- Helpers (shared validation for add AND edit) ----------
def read_amount(prompt):
    amount = float(input(prompt))
    if amount <= 0:                       # FIX 2: edit used to allow <= 0
        raise ValueError("Amount must be greater than zero!")
    return amount


def read_category(prompt):
    category = input(prompt).strip()
    if not category:                      # FIX 3: empty category was allowed
        raise ValueError("Category cannot be empty!")
    return category.title()               # "food" and "Food" now group together


def read_date(prompt):
    parsed = datetime.strptime(input(prompt).strip(), "%Y-%m-%d")
    # FIX 4: "2026-1-5" passes strptime but breaks the monthly LIKE search,
    # so always store the zero-padded form "2026-01-05"
    return parsed.strftime("%Y-%m-%d")


# ---------- Features ----------
def add_expense():
    try:
        amount = read_amount("Enter amount: ₹")
        category = read_category("Enter category: ")
        description = input("Enter description: ").strip()
        date = read_date("Enter date (YYYY-MM-DD): ")

        cursor.execute(
            "INSERT INTO expenses (amount, category, description, date) "
            "VALUES (?, ?, ?, ?)",
            (amount, category, description, date),
        )
        conn.commit()
        print("\nExpense added successfully!")
    except ValueError as e:
        print(f"\nInvalid input: {e}")


def view_expenses():
    cursor.execute("SELECT * FROM expenses ORDER BY date")
    records = cursor.fetchall()

    if not records:
        print("\nNo expenses found!")
        return False

    print("\n--- ALL EXPENSES ---")
    print(f"{'ID':<4}{'Amount':>10}  {'Category':<14}{'Date':<12}Description")
    print("-" * 60)
    for id_, amount, category, description, date in records:   # FIX 5: readable table
        print(f"{id_:<4}{amount:>10.2f}  {category:<14}{date:<12}{description}")
    return True


def edit_expense():
    if not view_expenses():               # FIX 6: don't ask for an ID when list is empty
        return
    try:
        expense_id = int(input("\nEnter expense ID to edit: "))
        amount = read_amount("Enter new amount: ₹")
        category = read_category("Enter new category: ")
        description = input("Enter new description: ").strip()
        date = read_date("Enter new date (YYYY-MM-DD): ")

        cursor.execute(
            "UPDATE expenses SET amount=?, category=?, description=?, date=? "
            "WHERE id=?",
            (amount, category, description, date, expense_id),
        )
        conn.commit()

        if cursor.rowcount:
            print("Expense updated successfully!")
        else:
            print("Expense ID not found!")
    except ValueError as e:
        print(f"\nInvalid input: {e}")


def delete_expense():
    if not view_expenses():
        return
    try:
        expense_id = int(input("\nEnter expense ID to delete: "))
        cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()

        if cursor.rowcount:
            print("Expense deleted successfully!")
        else:
            print("Expense ID not found!")
    except ValueError:
        print("Invalid ID!")


def monthly_summary():
    month = input("Enter month (YYYY-MM): ").strip()
    try:
        datetime.strptime(month, "%Y-%m")

        cursor.execute(
            "SELECT category, SUM(amount) FROM expenses "
            "WHERE date LIKE ? GROUP BY category ORDER BY SUM(amount) DESC",
            (month + "-%",),              # FIX 7: "2026-01-%" is stricter than "2026-01%"
        )
        records = cursor.fetchall()

        if not records:
            print("No expenses found for this month!")
            return

        total = sum(row[1] for row in records)

        print("\n--- MONTHLY SUMMARY ---")
        for category, amount in records:
            pct = (amount / total) * 100 if total else 0   # FIX 8: no ZeroDivisionError
            print(f"{category}: ₹{amount:.2f} ({pct:.1f}%)")
        print(f"\nTotal Expenses: ₹{total:.2f}")
    except ValueError:
        print("Invalid month format!")


# ---------- Main ----------
def main():
    actions = {
        "1": add_expense,
        "2": view_expenses,
        "3": edit_expense,
        "4": delete_expense,
        "5": monthly_summary,
    }
    try:
        while True:
            print("\n==============================")
            print("       EXPENSE TRACKER")
            print("==============================")
            print("1. Add Expense")
            print("2. View Expenses")
            print("3. Edit Expense")
            print("4. Delete Expense")
            print("5. Monthly Summary")
            print("6. Exit")

            choice = input("\nEnter your choice: ").strip()

            if choice == "6":
                print("Thank you for using Expense Tracker!")
                break
            action = actions.get(choice)
            if action:
                action()
            else:
                print("Invalid choice! Try again.")
    except (KeyboardInterrupt, EOFError):   # FIX 9: Ctrl+C exits cleanly
        print("\nExiting...")
    finally:
        conn.close()


if __name__ == "__main__":
    main()