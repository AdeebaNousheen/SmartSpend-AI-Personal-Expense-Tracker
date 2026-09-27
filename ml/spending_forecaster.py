"""
SmartSpend - Machine Learning: Spending Forecaster
Applies time-series regression (Ridge Regression with calendar & rolling features)
to project day-by-day trajectory and month-end expenditure against active budgets.
Enforces a strict historical data sufficiency guardrail (minimum 14 distinct days across >= 2 weeks).
"""

from datetime import datetime, timedelta
import calendar
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
import config
from database.db_manager import DatabaseManager


class SpendingForecaster:
    """
    Time-Series ML Forecaster for upcoming daily spending and month-end budget risk.
    Guarded by a strict minimum historical data requirement.
    """

    def __init__(self):
        self.min_days = config.ML_CONFIG["min_forecast_days_required"]
        self.min_weeks = config.ML_CONFIG["min_forecast_span_weeks"]
        self.min_transactions = config.ML_CONFIG["min_forecast_transactions"]

    def check_data_sufficiency(self, db: DatabaseManager, is_demo: Optional[int] = None) -> Dict[str, Any]:
        """
        Validates whether sufficient historical expense data exists to generate
        reliable forecasting without producing misleading predictions.
        """
        demo_cond = ""
        params: List[Any] = []
        if is_demo is not None:
            demo_cond = "AND is_demo = ?"
            params.append(is_demo)

        query = f"""
            SELECT date, amount
            FROM expenses
            WHERE category != 'Salary / Income' {demo_cond}
            ORDER BY date ASC;
        """
        rows = db.fetch_all(query, tuple(params))

        if not rows:
            return {
                "is_sufficient": False,
                "transaction_count": 0,
                "distinct_days": 0,
                "span_days": 0,
                "span_weeks": 0.0,
                "message": (
                    f"Insufficient Historical Data: Spending forecasting requires at least "
                    f"{self.min_days} days of recorded expenses spanning {self.min_weeks} weeks. "
                    f"Currently 0 transactions recorded. Continue logging expenses or load demo data to preview forecasting."
                )
            }

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        distinct_days = int(df["date"].dt.date.nunique())
        total_tx = len(df)
        min_date = df["date"].min()
        max_date = df["date"].max()
        span_days = int((max_date - min_date).days) + 1
        span_weeks = round(span_days / 7.0, 1)

        is_sufficient = (
            distinct_days >= self.min_days and
            span_weeks >= self.min_weeks and
            total_tx >= self.min_transactions
        )

        message = ""
        if not is_sufficient:
            message = (
                f"Insufficient Historical Data for Reliable Machine Learning Forecast:\n"
                f"• Recorded Distinct Days: {distinct_days} / {self.min_days} required\n"
                f"• Time Span: {span_weeks} weeks / {self.min_weeks} weeks required\n"
                f"• Transactions: {total_tx} / {self.min_transactions} required\n\n"
                f"To protect against inaccurate predictions, please record more daily expenses "
                f"or load Indian sample data to explore ML forecasting."
            )
        else:
            message = f"Sufficient data available ({distinct_days} days, {total_tx} transactions over {span_weeks} weeks)."

        return {
            "is_sufficient": is_sufficient,
            "transaction_count": total_tx,
            "distinct_days": distinct_days,
            "span_days": span_days,
            "span_weeks": span_weeks,
            "message": message,
            "df": df
        }

    def generate_forecast(
        self,
        db: DatabaseManager,
        currency_sym: str = "₹",
        is_demo: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes ML forecasting if guardrail passes; otherwise returns informative status.
        """
        sufficiency = self.check_data_sufficiency(db, is_demo=is_demo)
        if not sufficiency["is_sufficient"]:
            return {
                "status": "insufficient_data",
                "is_sufficient": False,
                "message": sufficiency["message"],
                "metrics": sufficiency
            }

        df = sufficiency["df"]

        # Aggregate daily total spending
        daily_series = df.groupby(df["date"].dt.date)["amount"].sum().reset_index()
        daily_series.columns = ["date", "amount"]
        daily_series["date"] = pd.to_datetime(daily_series["date"])
        daily_series = daily_series.sort_values("date").reset_index(drop=True)

        # Feature Engineering for Time-Series Regression
        daily_series["day_of_week"] = daily_series["date"].dt.dayofweek
        daily_series["day_of_month"] = daily_series["date"].dt.day
        daily_series["is_weekend"] = daily_series["day_of_week"].apply(lambda x: 1 if x in (4, 5, 6) else 0)
        daily_series["rolling_7d"] = daily_series["amount"].rolling(window=7, min_periods=1).mean()

        # Target variable: daily amount
        features = ["day_of_week", "day_of_month", "is_weekend", "rolling_7d"]
        X = daily_series[features].values
        y = daily_series["amount"].values

        # Fit regularized Ridge regression
        model = Ridge(alpha=1.0, positive=True)
        model.fit(X, y)

        # Current Month Time Calculations
        today = datetime.now().date()
        current_year = today.year
        current_month = today.month
        current_day = today.day
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        remaining_days = max(0, days_in_month - current_day)

        # Spending in current month so far
        current_month_str = today.strftime("%Y-%m")
        month_expenses = df[df["date"].dt.strftime("%Y-%m") == current_month_str]
        spent_so_far = float(month_expenses["amount"].sum())

        daily_burn_rate = (spent_so_far / current_day) if current_day > 0 else 0.0

        # Forecast remaining days of the month
        recent_rolling = float(daily_series["rolling_7d"].iloc[-1])
        predicted_remaining_daily = []
        cumulative_predicted = 0.0

        for day in range(current_day + 1, days_in_month + 1):
            future_date = datetime(current_year, current_month, day).date()
            dow = future_date.weekday()
            is_wknd = 1 if dow in (4, 5, 6) else 0
            # Blend rolling average with day model prediction
            x_future = np.array([[dow, day, is_wknd, recent_rolling]])
            pred_val = max(50.0, float(model.predict(x_future)[0]))
            
            # Update rolling average estimate
            recent_rolling = (recent_rolling * 6 + pred_val) / 7.0

            std_err = float(np.std(y)) if len(y) > 1 else 100.0
            lower_b = max(0.0, pred_val - (0.5 * std_err))
            upper_b = pred_val + (0.5 * std_err)

            cumulative_predicted += pred_val
            predicted_remaining_daily.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "day": day,
                "predicted_amount": round(pred_val, 2),
                "lower_bound": round(lower_b, 2),
                "upper_bound": round(upper_b, 2),
            })

        projected_month_end = round(spent_so_far + cumulative_predicted, 2)

        # Budget Risk Evaluation
        budget_row = db.fetch_one(
            "SELECT COALESCE(SUM(limit_amount), 0.0) as total_budget FROM budgets WHERE month_year = ?;",
            (current_month_str,)
        )
        total_budget = float(budget_row["total_budget"]) if budget_row else 0.0

        if total_budget <= 0.0:
            budget_risk = "No Budget Set"
            risk_color = "#64748B"
            risk_desc = "No monthly budget defined for current month."
            recommended_cap = None
        else:
            diff = projected_month_end - total_budget
            if projected_month_end > total_budget:
                budget_risk = "High Risk of Breach"
                risk_color = "#EF4444"
                pct_over = ((projected_month_end - total_budget) / total_budget) * 100.0
                risk_desc = (
                    f"Warning: At current trajectory, projected spend ({currency_sym}{projected_month_end:,.2f}) "
                    f"will exceed your budget ({currency_sym}{total_budget:,.2f}) by {pct_over:.1f}% ({currency_sym}{diff:,.2f})."
                )
            elif projected_month_end >= (0.85 * total_budget):
                budget_risk = "Moderate Risk"
                risk_color = "#F59E0B"
                risk_desc = (
                    f"Caution: Projected spend is {((projected_month_end / total_budget) * 100.0):.1f}% "
                    f"of your total monthly budget limit."
                )
            else:
                budget_risk = "Safe / Within Budget"
                risk_color = "#10B981"
                surplus = total_budget - projected_month_end
                risk_desc = (
                    f"Good financial health: Projected spend is comfortably within budget "
                    f"(estimated surplus of {currency_sym}{surplus:,.2f})."
                )

            # Recommended daily cap to finish month exactly on budget
            remaining_budget = max(0.0, total_budget - spent_so_far)
            recommended_cap = (remaining_budget / remaining_days) if remaining_days > 0 else 0.0

        return {
            "status": "success",
            "is_sufficient": True,
            "current_month": current_month_str,
            "days_elapsed": current_day,
            "days_remaining": remaining_days,
            "spent_so_far": spent_so_far,
            "daily_burn_rate": round(daily_burn_rate, 2),
            "predicted_remaining_spend": round(cumulative_predicted, 2),
            "projected_month_end": projected_month_end,
            "total_budget": total_budget,
            "budget_risk": budget_risk,
            "risk_color": risk_color,
            "risk_desc": risk_desc,
            "recommended_daily_cap": round(recommended_cap, 2) if recommended_cap is not None else None,
            "forecast_daily": predicted_remaining_daily,
            "recent_history": daily_series.tail(15)[["date", "amount"]].to_dict(orient="records")
        }
