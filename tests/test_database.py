"""
SmartSpend - Database Unit Tests
Verifies schema integrity, CRUD operations, and strict demo data isolation.
"""

import unittest
from pathlib import Path
import tempfile
from database.db_manager import DatabaseManager
from database.seed_data import SeedDataManager


class TestDatabaseManager(unittest.TestCase):
    """Test suite for SQLite database management and demo data isolation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_smartspend.db"
        self.db = DatabaseManager(self.db_path)
        self.seed_mgr = SeedDataManager(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tables_created(self):
        """Verify that all core tables exist in the database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {
            "settings", "categories", "expenses", "budgets",
            "savings_goals", "goal_contributions", "recurring_expenses"
        }
        for table in expected_tables:
            self.assertIn(table, tables, f"Expected table '{table}' missing from database schema.")

    def test_default_categories_seeded(self):
        """Verify default categories are populated on database initialization."""
        cats = self.db.fetch_all("SELECT * FROM categories;")
        self.assertGreaterEqual(len(cats), 10)
        cat_names = [c["name"] for c in cats]
        self.assertIn("Food & Dining", cat_names)
        self.assertIn("Transportation", cat_names)
        self.assertIn("Groceries", cat_names)

    def test_demo_data_isolation(self):
        """
        Verify that demo data is tagged with is_demo=1 and clearing demo data
        does NOT delete real user records (is_demo=0).
        """
        # 1. Insert a genuine user expense (is_demo = 0)
        user_expense_id = self.db.execute_query("""
            INSERT INTO expenses (
                title, amount, category, date, payment_method, notes, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, 0);
        """, ("My Real Grocery Run", 1250.0, "Groceries", "2026-09-20", "UPI", "Organic vegetables"))

        # 2. Insert a real user savings goal
        user_goal_id = self.db.execute_query("""
            INSERT INTO savings_goals (name, target_amount, current_amount, is_demo)
            VALUES (?, ?, ?, 0);
        """, ("Real Emergency Fund", 50000.0, 10000.0))

        # 3. Load demo dataset
        demo_count = self.seed_mgr.load_demo_data()
        self.assertGreater(demo_count, 50, "Expected demo data to populate over 50 records.")
        self.assertTrue(self.seed_mgr.has_demo_data())

        # Verify both exist together
        total_expenses = self.db.fetch_one("SELECT COUNT(*) as count FROM expenses;")["count"]
        self.assertEqual(total_expenses, demo_count + 1)

        # 4. Clear demo data only
        cleared_count = self.seed_mgr.clear_demo_data()
        self.assertEqual(cleared_count, demo_count)
        self.assertFalse(self.seed_mgr.has_demo_data())

        # 5. Verify user records are untouched
        remaining_user_expense = self.db.fetch_one("SELECT * FROM expenses WHERE id = ?;", (user_expense_id,))
        self.assertIsNotNone(remaining_user_expense)
        self.assertEqual(remaining_user_expense["title"], "My Real Grocery Run")
        self.assertEqual(remaining_user_expense["is_demo"], 0)

        remaining_user_goal = self.db.fetch_one("SELECT * FROM savings_goals WHERE id = ?;", (user_goal_id,))
        self.assertIsNotNone(remaining_user_goal)
        self.assertEqual(remaining_user_goal["name"], "Real Emergency Fund")
        self.assertEqual(remaining_user_goal["is_demo"], 0)


if __name__ == "__main__":
    unittest.main()
