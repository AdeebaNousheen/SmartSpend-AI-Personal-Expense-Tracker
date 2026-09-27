"""
SmartSpend - Seed Data Manager
Generates realistic Indian demo financial data spanning 6 months with is_demo=1.
Provides clean isolation, loading, and deletion of demo data without affecting real user records.
"""

from datetime import datetime, timedelta
import random
from typing import Optional
from database.db_manager import DatabaseManager


class SeedDataManager:
    """Manages synthetic demo dataset for evaluation, testing, and initial demonstration."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def has_demo_data(self) -> bool:
        """Check if any demo records exist in the database."""
        row = self.db.fetch_one("SELECT COUNT(*) as count FROM expenses WHERE is_demo = 1;")
        return bool(row and row["count"] > 0)

    def count_demo_data(self) -> int:
        """Return the total number of demo expense records."""
        row = self.db.fetch_one("SELECT COUNT(*) as count FROM expenses WHERE is_demo = 1;")
        return row["count"] if row else 0

    def clear_demo_data(self) -> int:
        """
        Safely wipe all demo records. Real user expenses (is_demo=0) are completely preserved.
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE is_demo = 1;")
            expenses_deleted = cursor.rowcount
            cursor.execute("DELETE FROM budgets WHERE is_demo = 1;")
            cursor.execute("""
                DELETE FROM goal_contributions 
                WHERE goal_id IN (SELECT id FROM savings_goals WHERE is_demo = 1);
            """)
            cursor.execute("DELETE FROM savings_goals WHERE is_demo = 1;")
            cursor.execute("DELETE FROM recurring_expenses WHERE is_demo = 1;")
            return expenses_deleted

    def clear_all_data(self) -> None:
        """Resets all tables to empty state while preserving categories and configuration."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses;")
            cursor.execute("DELETE FROM budgets;")
            cursor.execute("DELETE FROM goal_contributions;")
            cursor.execute("DELETE FROM savings_goals;")
            cursor.execute("DELETE FROM recurring_expenses;")

    def load_demo_data(self) -> int:
        """
        Generates and inserts realistic Indian market demo financial records.
        Spans 180 days (6 months) up to today.
        Includes deliberate anomalies for AI detection demonstration.
        """
        # First ensure no duplicate demo data exists
        self.clear_demo_data()

        today = datetime.now().date()
        random.seed(42)  # Deterministic generation for consistency

        # Merchant & category templates typical for an Indian young professional/student
        expense_templates = [
            # Food & Dining (Frequent, moderate)
            ("Swiggy food delivery", 250, 650, "Food & Dining", "UPI", "Biryani & snacks"),
            ("Zomato dinner order", 300, 850, "Food & Dining", "UPI", "Dinner with friends"),
            ("Chai Point tea & snacks", 60, 180, "Food & Dining", "Cash", "Evening tea"),
            ("Starbucks coffee", 280, 480, "Food & Dining", "Credit Card", "Cold brew & pastry"),
            ("McDonald's meal", 220, 520, "Food & Dining", "UPI", "Burger & fries"),
            ("Local Darshini breakfast", 70, 160, "Food & Dining", "Cash", "Dosa & filter coffee"),

            # Groceries (Weekly, higher amount)
            ("BigBasket weekly vegetables", 600, 1400, "Groceries", "UPI", "Fresh veggies & fruits"),
            ("D-Mart monthly supermarket haul", 2500, 4800, "Groceries", "Debit Card", "Provisions & cleaning"),
            ("Zepto quick grocery delivery", 180, 450, "Groceries", "UPI", "Milk, bread, eggs"),
            ("Blinkit household essentials", 220, 580, "Groceries", "UPI", "Cooking oil & spices"),

            # Transportation (Regular commutes)
            ("Uber cab ride to office", 180, 420, "Transportation", "UPI", "Peak hour cab"),
            ("Ola auto rickshaw", 70, 150, "Transportation", "UPI", "Metro to office"),
            ("Namma Metro card recharge", 200, 500, "Transportation", "UPI", "Smart card top-up"),
            ("Indian Oil petrol refill", 800, 1800, "Transportation", "Debit Card", "Full tank petrol"),

            # Utilities & Bills (Monthly)
            ("Electricity bill (BESCOM)", 1100, 1900, "Utilities & Bills", "Net Banking", "Monthly power bill"),
            ("Airtel Broadband Wi-Fi", 999, 999, "Utilities & Bills", "Net Banking", "100 Mbps fiber"),
            ("Jio mobile prepaid recharge", 349, 749, "Utilities & Bills", "UPI", "3-month data pack"),
            ("Water utility bill", 250, 450, "Utilities & Bills", "UPI", "Apartment water charges"),

            # Entertainment & Subscriptions
            ("Netflix Premium subscription", 649, 649, "Entertainment", "Credit Card", "Family plan 4K"),
            ("Spotify Premium family", 179, 179, "Entertainment", "Credit Card", "Music subscription"),
            ("PVR Cinemas movie tickets", 450, 1100, "Entertainment", "Credit Card", "Weekend movie & popcorn"),
            ("Steam gaming store purchase", 800, 2200, "Entertainment", "Credit Card", "Game on discount"),

            # Shopping
            ("Amazon India electronics & cables", 400, 1500, "Shopping", "Credit Card", "USB-C hub & phone case"),
            ("Myntra clothing & shoes", 1200, 3200, "Shopping", "Credit Card", "Casual wear"),
            ("Decathlon fitness gear", 600, 1800, "Shopping", "UPI", "Running socks & water bottle"),

            # Healthcare
            ("Apollo Pharmacy medicines", 150, 750, "Healthcare", "UPI", "Vitamins & first-aid"),
            ("Doctor consultation fee", 600, 1000, "Healthcare", "UPI", "General checkup"),

            # Personal Care
            ("Salon haircut & grooming", 250, 600, "Personal Care", "UPI", "Monthly haircut"),
        ]

        demo_expenses = []

        # Generate realistic distribution over past 180 days
        for days_ago in range(180, -1, -1):
            current_date = today - timedelta(days=days_ago)
            day_of_week = current_date.weekday()

            # Base number of transactions for the day
            # Weekends have more social/food/shopping spending
            if day_of_week in (4, 5, 6):  # Fri, Sat, Sun
                num_tx = random.choices([1, 2, 3, 4], weights=[0.2, 0.4, 0.3, 0.1])[0]
            else:
                num_tx = random.choices([0, 1, 2, 3], weights=[0.15, 0.5, 0.3, 0.05])[0]

            for _ in range(num_tx):
                template = random.choice(expense_templates)
                title, min_amt, max_amt, category, payment_method, notes = template
                amount = round(random.uniform(min_amt, max_amt), 2)

                demo_expenses.append((
                    title,
                    amount,
                    category,
                    current_date.strftime("%Y-%m-%d"),
                    payment_method,
                    notes,
                    0,     # is_anomaly initially 0
                    None,  # anomaly_reason
                    1      # is_demo = 1
                ))

            # Add monthly recurring items on specific days
            if current_date.day == 1:
                # Rent payment
                demo_expenses.append((
                    "Monthly House Rent",
                    16500.0,
                    "Housing & Rent",
                    current_date.strftime("%Y-%m-%d"),
                    "Net Banking",
                    "Apartment monthly rent transfer",
                    0,
                    None,
                    1
                ))
            elif current_date.day == 5:
                # Mutual Fund SIP Investment
                demo_expenses.append((
                    "Mutual Fund SIP - Index Fund",
                    5000.0,
                    "Investments",
                    current_date.strftime("%Y-%m-%d"),
                    "Net Banking",
                    "Automated SIP deduction",
                    0,
                    None,
                    1
                ))

        # Add deliberate anomalies for demonstration of AI detection
        # Anomaly 1: A huge restaurant bill
        anomaly_date_1 = today - timedelta(days=12)
        demo_expenses.append((
            "Five Star Luxury Dinner & Drinks",
            14500.0,
            "Food & Dining",
            anomaly_date_1.strftime("%Y-%m-%d"),
            "Credit Card",
            "Fine dining celebration with large group",
            1,
            "Amount ₹14,500 is 24x higher than typical Food & Dining average (₹350-₹800)",
            1
        ))

        # Anomaly 2: Extreme shopping purchase
        anomaly_date_2 = today - timedelta(days=45)
        demo_expenses.append((
            "Apple Store - iPhone Purchase",
            79900.0,
            "Shopping",
            anomaly_date_2.strftime("%Y-%m-%d"),
            "Credit Card",
            "Annual smartphone upgrade",
            1,
            "Amount ₹79,900 is an extreme 28x outlier compared to standard shopping transactions",
            1
        ))

        # Insert all demo expenses
        self.db.execute_many("""
            INSERT INTO expenses (
                title, amount, category, date, payment_method, notes,
                is_anomaly, anomaly_reason, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, demo_expenses)

        # Seed Demo Budgets for current month (YYYY-MM)
        current_month_str = today.strftime("%Y-%m")
        demo_budgets = [
            ("Food & Dining", current_month_str, 12000.0, 1),
            ("Groceries", current_month_str, 9000.0, 1),
            ("Transportation", current_month_str, 4500.0, 1),
            ("Housing & Rent", current_month_str, 18000.0, 1),
            ("Utilities & Bills", current_month_str, 4000.0, 1),
            ("Entertainment", current_month_str, 3000.0, 1),
            ("Shopping", current_month_str, 8000.0, 1),
            ("Healthcare", current_month_str, 3000.0, 1),
        ]
        self.db.execute_many("""
            INSERT OR REPLACE INTO budgets (category_name, month_year, limit_amount, is_demo)
            VALUES (?, ?, ?, ?);
        """, demo_budgets)

        # Seed Demo Savings Goals
        demo_goals = [
            ("Emergency Fund (6 Months)", 150000.0, 95000.0, (today + timedelta(days=120)).strftime("%Y-%m-%d"), 1),
            ("Goa Trip with College Friends", 25000.0, 18500.0, (today + timedelta(days=45)).strftime("%Y-%m-%d"), 1),
            ("New Coding Laptop (M-Series)", 120000.0, 45000.0, (today + timedelta(days=180)).strftime("%Y-%m-%d"), 1),
        ]
        for name, target, current, target_dt, is_demo in demo_goals:
            goal_id = self.db.execute_query("""
                INSERT INTO savings_goals (name, target_amount, current_amount, target_date, is_demo)
                VALUES (?, ?, ?, ?, ?);
            """, (name, target, current, target_dt, is_demo))

            # Add demo contributions history
            self.db.execute_query("""
                INSERT INTO goal_contributions (goal_id, amount, date, notes)
                VALUES (?, ?, ?, ?);
            """, (goal_id, current * 0.4, (today - timedelta(days=60)).strftime("%Y-%m-%d"), "Monthly savings allocation"))
            self.db.execute_query("""
                INSERT INTO goal_contributions (goal_id, amount, date, notes)
                VALUES (?, ?, ?, ?);
            """, (goal_id, current * 0.6, (today - timedelta(days=20)).strftime("%Y-%m-%d"), "Bonus contribution"))

        # Seed Demo Recurring Subscriptions
        demo_recurring = [
            ("House Rent", 16500.0, "Housing & Rent", "Monthly", (today + timedelta(days=4)).strftime("%Y-%m-%d"), (today - timedelta(days=26)).strftime("%Y-%m-%d"), 1, 1),
            ("Airtel Fiber Broadband", 999.0, "Utilities & Bills", "Monthly", (today + timedelta(days=11)).strftime("%Y-%m-%d"), (today - timedelta(days=19)).strftime("%Y-%m-%d"), 1, 1),
            ("Netflix 4K Ultra", 649.0, "Entertainment", "Monthly", (today + timedelta(days=7)).strftime("%Y-%m-%d"), (today - timedelta(days=23)).strftime("%Y-%m-%d"), 1, 1),
            ("Spotify Family", 179.0, "Entertainment", "Monthly", (today + timedelta(days=15)).strftime("%Y-%m-%d"), (today - timedelta(days=15)).strftime("%Y-%m-%d"), 1, 1),
            ("Cult.fit Gym Membership", 1500.0, "Personal Care", "Monthly", (today + timedelta(days=2)).strftime("%Y-%m-%d"), (today - timedelta(days=28)).strftime("%Y-%m-%d"), 1, 1),
        ]
        self.db.execute_many("""
            INSERT INTO recurring_expenses (
                title, amount, category, frequency, next_due_date, last_logged_date, is_active, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, demo_recurring)

        return len(demo_expenses)
