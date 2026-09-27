"""
SmartSpend - Goal Service
Tracks savings goals, contribution logging, deadline countdowns, and percentage milestones.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from database.db_manager import DatabaseManager


class GoalService:
    """Manages long-term savings goals and deposit contributions."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def create_goal(
        self,
        name: str,
        target_amount: float,
        current_amount: float = 0.0,
        target_date: Optional[str] = None,
        is_demo: int = 0,
    ) -> int:
        """Create a new savings goal."""
        query = """
            INSERT INTO savings_goals (name, target_amount, current_amount, target_date, is_demo)
            VALUES (?, ?, ?, ?, ?);
        """
        return self.db.execute_query(
            query,
            (name.strip(), float(target_amount), float(current_amount), target_date, is_demo)
        )

    def update_goal(
        self,
        goal_id: int,
        name: str,
        target_amount: float,
        current_amount: float,
        target_date: Optional[str] = None,
    ) -> bool:
        """Update an existing savings goal."""
        query = """
            UPDATE savings_goals
            SET name = ?, target_amount = ?, current_amount = ?, target_date = ?
            WHERE id = ?;
        """
        self.db.execute_query(
            query,
            (name.strip(), float(target_amount), float(current_amount), target_date, goal_id)
        )
        return True

    def delete_goal(self, goal_id: int) -> bool:
        """Delete a savings goal and its associated contributions."""
        self.db.execute_query("DELETE FROM savings_goals WHERE id = ?;", (goal_id,))
        return True

    def add_contribution(
        self,
        goal_id: int,
        amount: float,
        date: Optional[str] = None,
        notes: str = "",
    ) -> int:
        """
        Log a deposit towards a savings goal and update its current saved amount.
        """
        dt = date or datetime.now().strftime("%Y-%m-%d")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Log contribution
            cursor.execute("""
                INSERT INTO goal_contributions (goal_id, amount, date, notes)
                VALUES (?, ?, ?, ?);
            """, (goal_id, float(amount), dt, notes.strip()))
            contrib_id = cursor.lastrowid

            # 2. Increment goal's current amount
            cursor.execute("""
                UPDATE savings_goals
                SET current_amount = current_amount + ?
                WHERE id = ?;
            """, (float(amount), goal_id))
            return contrib_id

    def get_goals(self, is_demo: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all savings goals with calculated progress metrics.
        """
        conditions = []
        params: List[Any] = []
        if is_demo is not None:
            conditions.append("is_demo = ?")
            params.append(is_demo)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM savings_goals {where} ORDER BY created_at DESC;"
        rows = self.db.fetch_all(query, tuple(params))

        today = datetime.now().date()
        results = []
        for r in rows:
            target = float(r["target_amount"])
            current = float(r["current_amount"])
            pct = min(100.0, (current / target * 100.0)) if target > 0 else 0.0
            remaining = max(0.0, target - current)

            days_left = None
            if r["target_date"]:
                try:
                    target_dt = datetime.strptime(r["target_date"], "%Y-%m-%d").date()
                    delta = (target_dt - today).days
                    days_left = max(0, delta)
                except ValueError:
                    days_left = None

            results.append({
                "id": r["id"],
                "name": r["name"],
                "target_amount": target,
                "current_amount": current,
                "remaining_amount": remaining,
                "percentage_completed": round(pct, 1),
                "target_date": r["target_date"],
                "days_left": days_left,
                "is_completed": current >= target,
                "is_demo": r["is_demo"]
            })
        return results

    def get_contributions(self, goal_id: int) -> List[Dict[str, Any]]:
        """Retrieve historical contributions made to a savings goal."""
        query = """
            SELECT * FROM goal_contributions
            WHERE goal_id = ?
            ORDER BY date DESC, id DESC;
        """
        return self.db.fetch_all(query, (goal_id,))
