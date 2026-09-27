"""
SmartSpend - Expense Service
Core business logic for expense tracking, search, filtering, and statistical aggregations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from database.db_manager import DatabaseManager


class ExpenseService:
    """Manages transaction records, filtering, and aggregated metrics."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def add_expense(
        self,
        title: str,
        amount: float,
        category: str,
        date: str,
        payment_method: str = "UPI",
        notes: str = "",
        is_anomaly: int = 0,
        anomaly_reason: Optional[str] = None,
        is_demo: int = 0,
    ) -> int:
        """Insert a new expense transaction."""
        query = """
            INSERT INTO expenses (
                title, amount, category, date, payment_method, notes,
                is_anomaly, anomaly_reason, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        return self.db.execute_query(
            query,
            (title.strip(), float(amount), category.strip(), date, payment_method, notes.strip(), is_anomaly, anomaly_reason, is_demo)
        )

    def update_expense(
        self,
        expense_id: int,
        title: str,
        amount: float,
        category: str,
        date: str,
        payment_method: str,
        notes: str = "",
        is_anomaly: Optional[int] = None,
        anomaly_reason: Optional[str] = None,
    ) -> bool:
        """Update an existing expense transaction."""
        if is_anomaly is not None:
            query = """
                UPDATE expenses
                SET title = ?, amount = ?, category = ?, date = ?,
                    payment_method = ?, notes = ?, is_anomaly = ?, anomaly_reason = ?
                WHERE id = ?;
            """
            self.db.execute_query(
                query,
                (title.strip(), float(amount), category.strip(), date, payment_method, notes.strip(), is_anomaly, anomaly_reason, expense_id)
            )
        else:
            query = """
                UPDATE expenses
                SET title = ?, amount = ?, category = ?, date = ?,
                    payment_method = ?, notes = ?
                WHERE id = ?;
            """
            self.db.execute_query(
                query,
                (title.strip(), float(amount), category.strip(), date, payment_method, notes.strip(), expense_id)
            )
        return True

    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense record by ID."""
        self.db.execute_query("DELETE FROM expenses WHERE id = ?;", (expense_id,))
        return True

    def get_expense_by_id(self, expense_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve single expense details."""
        return self.db.fetch_one("SELECT * FROM expenses WHERE id = ?;", (expense_id,))

    def get_expenses(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        is_anomaly: Optional[int] = None,
        is_demo: Optional[int] = None,
        sort_by: str = "date",
        sort_order: str = "DESC",
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Query expenses with flexible search, filtering, and sorting criteria.
        """
        conditions = []
        params: List[Any] = []

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if category and category != "All":
            conditions.append("category = ?")
            params.append(category)
        if search:
            conditions.append("(title LIKE ? OR notes LIKE ? OR payment_method LIKE ?)")
            term = f"%{search.strip()}%"
            params.extend([term, term, term])
        if is_anomaly is not None:
            conditions.append("is_anomaly = ?")
            params.append(is_anomaly)
        if is_demo is not None:
            conditions.append("is_demo = ?")
            params.append(is_demo)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Validate sorting column
        allowed_sort_cols = {"date", "amount", "title", "category", "created_at"}
        safe_sort = sort_by if sort_by in allowed_sort_cols else "date"
        safe_order = "ASC" if sort_order.upper() == "ASC" else "DESC"

        limit_clause = f"LIMIT {int(limit)} OFFSET {int(offset)}" if limit is not None else ""

        query = f"""
            SELECT * FROM expenses
            {where_clause}
            ORDER BY {safe_sort} {safe_order}, id DESC
            {limit_clause};
        """
        return self.db.fetch_all(query, tuple(params))

    def get_categories(self, include_income: bool = False) -> List[Dict[str, Any]]:
        """Fetch categories registered in system."""
        if include_income:
            return self.db.fetch_all("SELECT * FROM categories ORDER BY name ASC;")
        return self.db.fetch_all("SELECT * FROM categories WHERE is_income = 0 ORDER BY name ASC;")

    def get_total_spent(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_demo: Optional[int] = None,
    ) -> float:
        """Calculate total expenditure within a date interval (excluding income)."""
        conditions = ["category != 'Salary / Income'"]
        params: List[Any] = []

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if is_demo is not None:
            conditions.append("is_demo = ?")
            params.append(is_demo)

        where_clause = f"WHERE {' AND '.join(conditions)}"
        row = self.db.fetch_one(f"SELECT COALESCE(SUM(amount), 0.0) as total FROM expenses {where_clause};", tuple(params))
        return float(row["total"]) if row else 0.0

    def get_spending_by_category(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_demo: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Aggregate total expenditure by category for visualization (pie/donut charts).
        """
        conditions = ["category != 'Salary / Income'"]
        params: List[Any] = []

        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if is_demo is not None:
            conditions.append("is_demo = ?")
            params.append(is_demo)

        where_clause = f"WHERE {' AND '.join(conditions)}"
        query = f"""
            SELECT category, SUM(amount) as total_amount, COUNT(*) as tx_count
            FROM expenses
            {where_clause}
            GROUP BY category
            ORDER BY total_amount DESC;
        """
        return self.db.fetch_all(query, tuple(params))

    def get_monthly_spending(self, num_months: int = 6, is_demo: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Calculates monthly spending totals for the past N months.
        """
        conditions = ["category != 'Salary / Income'"]
        params: List[Any] = []

        if is_demo is not None:
            conditions.append("is_demo = ?")
            params.append(is_demo)

        where_clause = f"WHERE {' AND '.join(conditions)}"
        query = f"""
            SELECT strftime('%Y-%m', date) as month_year, SUM(amount) as total_amount, COUNT(*) as tx_count
            FROM expenses
            {where_clause}
            GROUP BY month_year
            ORDER BY month_year DESC
            LIMIT {int(num_months)};
        """
        rows = self.db.fetch_all(query, tuple(params))
        return list(reversed(rows))

    def get_daily_spending(self, days: int = 30, is_demo: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Calculates daily spending totals for the last N calendar days.
        """
        today = datetime.now().date()
        start_date = (today - timedelta(days=days - 1)).strftime("%Y-%m-%d")

        conditions = ["category != 'Salary / Income'", "date >= ?"]
        params: List[Any] = [start_date]

        if is_demo is not None:
            conditions.append("is_demo = ?")
            params.append(is_demo)

        where_clause = f"WHERE {' AND '.join(conditions)}"
        query = f"""
            SELECT date, SUM(amount) as total_amount
            FROM expenses
            {where_clause}
            GROUP BY date
            ORDER BY date ASC;
        """
        rows = self.db.fetch_all(query, tuple(params))

        # Fill missing days with zero spend for continuous trend lines
        daily_map = {row["date"]: row["total_amount"] for row in rows}
        continuous_data = []
        for i in range(days):
            d_str = (today - timedelta(days=(days - 1 - i))).strftime("%Y-%m-%d")
            continuous_data.append({
                "date": d_str,
                "total_amount": daily_map.get(d_str, 0.0)
            })
        return continuous_data

    def get_all_anomalies(self, is_demo: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve all transactions flagged as anomalies."""
        return self.get_expenses(is_anomaly=1, is_demo=is_demo, sort_by="date", sort_order="DESC")

    def update_anomaly_status(self, expense_id: int, is_anomaly: int, reason: Optional[str] = None) -> None:
        """Mark or unmark an expense as an anomaly with rationale."""
        self.db.execute_query(
            "UPDATE expenses SET is_anomaly = ?, anomaly_reason = ? WHERE id = ?;",
            (is_anomaly, reason, expense_id)
        )
