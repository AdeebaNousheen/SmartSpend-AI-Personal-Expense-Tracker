"""
SmartSpend - Budget Service
Calculates category spending against set limits, tracks consumption %, and triggers threshold warnings.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from database.db_manager import DatabaseManager


class BudgetService:
    """Manages monthly category spending targets and budget health."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def set_budget(
        self,
        category_name: str,
        month_year: str,
        limit_amount: float,
        is_demo: int = 0,
    ) -> int:
        """
        Creates or updates a budget target for a category in a specific month (YYYY-MM).
        """
        query = """
            INSERT INTO budgets (category_name, month_year, limit_amount, is_demo)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category_name, month_year, is_demo) 
            DO UPDATE SET limit_amount = excluded.limit_amount;
        """
        return self.db.execute_query(query, (category_name.strip(), month_year, float(limit_amount), is_demo))

    def delete_budget(self, budget_id: int) -> bool:
        """Deletes a budget target."""
        self.db.execute_query("DELETE FROM budgets WHERE id = ?;", (budget_id,))
        return True

    def get_budgets(
        self,
        month_year: Optional[str] = None,
        is_demo: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve defined budgets."""
        my = month_year or datetime.now().strftime("%Y-%m")
        conditions = ["month_year = ?"]
        params: List[Any] = [my]

        if is_demo is not None:
            conditions.append("is_demo = ?")
            params.append(is_demo)

        where = f"WHERE {' AND '.join(conditions)}"
        query = f"SELECT * FROM budgets {where} ORDER BY category_name ASC;"
        return self.db.fetch_all(query, tuple(params))

    def get_budget_status(
        self,
        month_year: Optional[str] = None,
        is_demo: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Compares monthly budget limits against actual recorded expenditures.
        Returns:
            category_name, limit_amount, spent_amount, remaining_amount,
            percentage_used, status ('Normal' | 'Warning' | 'Exceeded')
        """
        my = month_year or datetime.now().strftime("%Y-%m")
        budgets = self.get_budgets(month_year=my, is_demo=is_demo)

        # Get actual spending in month per category
        start_date = f"{my}-01"
        end_date = f"{my}-31"

        demo_condition = ""
        params: List[Any] = [start_date, end_date]
        if is_demo is not None:
            demo_condition = "AND is_demo = ?"
            params.append(is_demo)

        query = f"""
            SELECT category, SUM(amount) as spent
            FROM expenses
            WHERE date >= ? AND date <= ? {demo_condition}
            GROUP BY category;
        """
        spending_rows = self.db.fetch_all(query, tuple(params))
        spending_map = {row["category"]: float(row["spent"]) for row in spending_rows}

        results = []
        for b in budgets:
            cat = b["category_name"]
            limit_amt = float(b["limit_amount"])
            spent_amt = spending_map.get(cat, 0.0)
            remaining_amt = max(0.0, limit_amt - spent_amt)
            pct = (spent_amt / limit_amt * 100.0) if limit_amt > 0 else 0.0

            if pct >= 100.0:
                status = "Exceeded"
            elif pct >= 80.0:
                status = "Warning"
            else:
                status = "Normal"

            results.append({
                "id": b["id"],
                "category_name": cat,
                "month_year": my,
                "limit_amount": limit_amt,
                "spent_amount": spent_amt,
                "remaining_amount": remaining_amt,
                "percentage_used": round(pct, 1),
                "status": status,
                "is_demo": b["is_demo"]
            })
        return results

    def get_overall_budget_summary(
        self,
        month_year: Optional[str] = None,
        is_demo: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculates holistic monthly budget summary across all budgeted categories.
        """
        status_list = self.get_budget_status(month_year, is_demo)
        total_budget = sum(item["limit_amount"] for item in status_list)
        total_spent = sum(item["spent_amount"] for item in status_list)
        total_remaining = max(0.0, total_budget - total_spent)
        overall_pct = (total_spent / total_budget * 100.0) if total_budget > 0 else 0.0

        warning_count = sum(1 for item in status_list if item["status"] == "Warning")
        exceeded_count = sum(1 for item in status_list if item["status"] == "Exceeded")

        return {
            "total_budget": total_budget,
            "total_spent": total_spent,
            "total_remaining": total_remaining,
            "overall_pct": round(overall_pct, 1),
            "warning_count": warning_count,
            "exceeded_count": exceeded_count,
            "category_count": len(status_list)
        }
