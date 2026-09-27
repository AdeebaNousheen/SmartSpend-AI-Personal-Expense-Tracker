"""
SmartSpend - Services Unit Tests
Verifies business logic across expenses, budgets, savings goals, subscriptions, and settings.
"""

import unittest
from pathlib import Path
import tempfile
from database.db_manager import DatabaseManager
from services.expense_service import ExpenseService
from services.budget_service import BudgetService
from services.goal_service import GoalService
from services.recurring_service import RecurringService
from services.settings_service import SettingsService
from services.report_service import ReportService


class TestServices(unittest.TestCase):
    """Test suite for business service logic."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.db = DatabaseManager(self.temp_path / "test_services.db")

        self.expense_svc = ExpenseService(self.db)
        self.budget_svc = BudgetService(self.db)
        self.goal_svc = GoalService(self.db)
        self.recurring_svc = RecurringService(self.db)
        self.settings_svc = SettingsService(self.db)
        self.report_svc = ReportService(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_settings_currency_switching(self):
        """Verify default INR (₹) currency and switching to USD/EUR."""
        # Default should be ₹
        self.assertEqual(self.settings_svc.get_currency_symbol(), "₹")
        self.assertEqual(self.settings_svc.get_currency_code(), "INR")

        formatted = self.settings_svc.format_currency(150000.50)
        self.assertIn("₹", formatted)
        self.assertEqual(formatted, "₹1,50,000.50")

        # Switch to USD
        self.settings_svc.set_currency("USD")
        self.assertEqual(self.settings_svc.get_currency_symbol(), "$")
        self.assertEqual(self.settings_svc.get_currency_code(), "USD")
        formatted_usd = self.settings_svc.format_currency(150000.50)
        self.assertEqual(formatted_usd, "$150,000.50")

    def test_expense_crud_and_metrics(self):
        """Verify expense creation, retrieval, filtering, and total spend."""
        e1 = self.expense_svc.add_expense("Swiggy Biryani", 350.0, "Food & Dining", "2026-09-10", "UPI", "Lunch")
        e2 = self.expense_svc.add_expense("Metro Card", 200.0, "Transportation", "2026-09-11", "UPI", "Commute")

        # Total spend
        total = self.expense_svc.get_total_spent()
        self.assertEqual(total, 550.0)

        # By category
        by_cat = self.expense_svc.get_spending_by_category()
        self.assertEqual(len(by_cat), 2)

        # Delete
        self.expense_svc.delete_expense(e1)
        self.assertEqual(self.expense_svc.get_total_spent(), 200.0)

    def test_budget_status_and_alerts(self):
        """Verify budget limit tracking, percentage calculation, and warning triggers."""
        # Create budget for Food & Dining of ₹1,000 for month 2026-09
        self.budget_svc.set_budget("Food & Dining", "2026-09", 1000.0)

        # 1. Spend ₹500 (50% -> Normal)
        self.expense_svc.add_expense("Meal 1", 500.0, "Food & Dining", "2026-09-05", "UPI")
        status_list = self.budget_svc.get_budget_status("2026-09")
        self.assertEqual(len(status_list), 1)
        self.assertEqual(status_list[0]["status"], "Normal")
        self.assertEqual(status_list[0]["percentage_used"], 50.0)

        # 2. Spend ₹350 more (Total ₹850 = 85% -> Warning)
        self.expense_svc.add_expense("Meal 2", 350.0, "Food & Dining", "2026-09-12", "UPI")
        status_list = self.budget_svc.get_budget_status("2026-09")
        self.assertEqual(status_list[0]["status"], "Warning")

        # 3. Spend ₹200 more (Total ₹1050 = 105% -> Exceeded)
        self.expense_svc.add_expense("Meal 3", 200.0, "Food & Dining", "2026-09-18", "UPI")
        status_list = self.budget_svc.get_budget_status("2026-09")
        self.assertEqual(status_list[0]["status"], "Exceeded")

    def test_goal_contributions(self):
        """Verify savings goal creation and contribution increment."""
        goal_id = self.goal_svc.create_goal("Goa Trip", 20000.0, 5000.0, "2026-11-01")
        goals = self.goal_svc.get_goals()
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0]["percentage_completed"], 25.0)

        # Add contribution of ₹5,000
        self.goal_svc.add_contribution(goal_id, 5000.0, "2026-09-20", "Savings transfer")
        updated_goals = self.goal_svc.get_goals()
        self.assertEqual(updated_goals[0]["current_amount"], 10000.0)
        self.assertEqual(updated_goals[0]["percentage_completed"], 50.0)

    def test_recurring_expense_advancement(self):
        """Verify subscription schedule advancement and automated expense logging."""
        rec_id = self.recurring_svc.add_recurring_expense(
            "Netflix", 649.0, "Entertainment", "Monthly", "2026-09-15"
        )
        # Log the subscription
        expense_id = self.recurring_svc.log_recurring_expense(rec_id)
        self.assertIsNotNone(expense_id)

        # Check expense was recorded
        exp = self.expense_svc.get_expense_by_id(expense_id)
        self.assertIn("Netflix", exp["title"])
        self.assertEqual(exp["amount"], 649.0)

        # Check recurring expense due date moved forward
        rec = self.recurring_svc.get_recurring_expenses()[0]
        self.assertEqual(rec["next_due_date"], "2026-10-15")

    def test_csv_export(self):
        """Verify CSV export writes valid headers and rows."""
        self.expense_svc.add_expense("Test Expense", 100.0, "Shopping", "2026-09-01", "Cash")
        csv_file = self.temp_path / "export_test.csv"
        self.report_svc.export_csv(csv_file)
        self.assertTrue(csv_file.exists())
        self.assertGreater(csv_file.stat().st_size, 50)


if __name__ == "__main__":
    unittest.main()
