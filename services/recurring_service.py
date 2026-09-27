"""
SmartSpend - Recurring Expense Service
Tracks repeating bills & subscriptions, detects due payments, and enables automated expense logging.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from database.db_manager import DatabaseManager


class RecurringService:
    """Manages subscription lifecycles, schedule recalculations, and automated expense logging."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def add_recurring_expense(
        self,
        title: str,
        amount: float,
        category: str,
        frequency: str = "Monthly",
        next_due_date: Optional[str] = None,
        is_demo: int = 0,
    ) -> int:
        """Register a new recurring expense/subscription."""
        dt = next_due_date or datetime.now().strftime("%Y-%m-%d")
        query = """
            INSERT INTO recurring_expenses (
                title, amount, category, frequency, next_due_date, is_active, is_demo
            ) VALUES (?, ?, ?, ?, ?, 1, ?);
        """
        return self.db.execute_query(
            query,
            (title.strip(), float(amount), category.strip(), frequency, dt, is_demo)
        )

    def update_recurring_expense(
        self,
        recurring_id: int,
        title: str,
        amount: float,
        category: str,
        frequency: str,
        next_due_date: str,
        is_active: int = 1,
    ) -> bool:
        """Update subscription parameters."""
        query = """
            UPDATE recurring_expenses
            SET title = ?, amount = ?, category = ?, frequency = ?, next_due_date = ?, is_active = ?
            WHERE id = ?;
        """
        self.db.execute_query(
            query,
            (title.strip(), float(amount), category.strip(), frequency, next_due_date, is_active, recurring_id)
        )
        return True

    def delete_recurring_expense(self, recurring_id: int) -> bool:
        """Delete a recurring subscription."""
        self.db.execute_query("DELETE FROM recurring_expenses WHERE id = ?;", (recurring_id,))
        return True

    def get_recurring_expenses(
        self,
        is_demo: Optional[int] = None,
        active_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Fetch recurring expenses with due date urgency calculations."""
        conditions = []
        params: List[Any] = []

        if active_only:
            conditions.append("is_active = 1")
        if is_demo is not None:
            conditions.append("is_demo = ?")
            params.append(is_demo)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM recurring_expenses {where} ORDER BY next_due_date ASC;"
        rows = self.db.fetch_all(query, tuple(params))

        today = datetime.now().date()
        results = []
        for r in rows:
            try:
                due_dt = datetime.strptime(r["next_due_date"], "%Y-%m-%d").date()
                days_diff = (due_dt - today).days
                if days_diff < 0:
                    status = "Overdue"
                elif days_diff == 0:
                    status = "Due Today"
                elif days_diff <= 7:
                    status = "Due Soon"
                else:
                    status = "Upcoming"
            except ValueError:
                days_diff = 999
                status = "Unknown"

            results.append({
                **r,
                "days_until_due": days_diff,
                "urgency_status": status
            })
        return results

    def calculate_next_date(self, current_due_date_str: str, frequency: str) -> str:
        """Computes next due date based on recurrence interval."""
        try:
            curr_dt = datetime.strptime(current_due_date_str, "%Y-%m-%d").date()
        except ValueError:
            curr_dt = datetime.now().date()

        freq = frequency.capitalize()
        if freq == "Daily":
            next_dt = curr_dt + timedelta(days=1)
        elif freq == "Weekly":
            next_dt = curr_dt + timedelta(days=7)
        elif freq == "Quarterly":
            next_dt = curr_dt + timedelta(days=90)
        elif freq == "Yearly":
            next_dt = curr_dt.replace(year=curr_dt.year + 1)
        else:  # Monthly default
            # Add ~30 days safely handling month wrapping
            month = curr_dt.month + 1
            year = curr_dt.year
            if month > 12:
                month = 1
                year += 1
            day = min(curr_dt.day, 28)
            next_dt = curr_dt.replace(year=year, month=month, day=day)

        return next_dt.strftime("%Y-%m-%d")

    def log_recurring_expense(self, recurring_id: int) -> int:
        """
        Records the recurring bill as an actual expense today and automatically
        advances its next_due_date.
        """
        rec = self.db.fetch_one("SELECT * FROM recurring_expenses WHERE id = ?;", (recurring_id,))
        if not rec:
            raise ValueError(f"Recurring expense {recurring_id} not found.")

        today_str = datetime.now().strftime("%Y-%m-%d")
        next_due = self.calculate_next_date(rec["next_due_date"], rec["frequency"])

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Insert into expenses
            cursor.execute("""
                INSERT INTO expenses (
                    title, amount, category, date, payment_method, notes,
                    is_anomaly, is_demo
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?);
            """, (
                f"{rec['title']} (Subscription)",
                rec["amount"],
                rec["category"],
                today_str,
                "UPI",
                f"Automated recurring log for frequency: {rec['frequency']}",
                rec["is_demo"]
            ))
            expense_id = cursor.lastrowid

            # 2. Advance recurring schedule
            cursor.execute("""
                UPDATE recurring_expenses
                SET last_logged_date = ?, next_due_date = ?
                WHERE id = ?;
            """, (today_str, next_due, recurring_id))

            return expense_id

    def get_due_summary(self, is_demo: Optional[int] = None) -> Dict[str, Any]:
        """Summarizes subscriptions due soon or overdue."""
        items = self.get_recurring_expenses(is_demo=is_demo, active_only=True)
        overdue = [i for i in items if i["urgency_status"] == "Overdue"]
        due_soon = [i for i in items if i["urgency_status"] in ("Due Today", "Due Soon")]

        return {
            "total_active": len(items),
            "total_monthly_committed": sum(i["amount"] for i in items if i["frequency"] == "Monthly"),
            "overdue_count": len(overdue),
            "overdue_amount": sum(i["amount"] for i in overdue),
            "due_soon_count": len(due_soon),
            "due_soon_amount": sum(i["amount"] for i in due_soon),
        }
