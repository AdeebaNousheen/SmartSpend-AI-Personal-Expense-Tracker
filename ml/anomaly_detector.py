"""
SmartSpend - Machine Learning & Statistical Anomaly Detector
Detects unusual transactions combining Machine Learning (Isolation Forest)
and Statistical Analytics (Category-specific IQR & Z-score distribution bounds).
Generates human-understandable explanations for flagged anomalies.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import config
from database.db_manager import DatabaseManager


class AnomalyDetector:
    """
    Multi-tiered anomaly detection system combining:
    1. Unsupervised Machine Learning: Isolation Forest for multivariate anomaly scoring.
    2. Statistical Analytics: Category-specific Interquartile Range (IQR) and Z-Score bounds.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or config.ML_CONFIG["anomaly_model_path"]
        self.isolation_forest: Optional[IsolationForest] = None
        self.category_stats: Dict[str, Dict[str, float]] = {}
        self.category_to_idx: Dict[str, int] = {}
        self._load_or_init()

    def _load_or_init(self) -> None:
        """Loads cached model or creates a fresh Isolation Forest instance."""
        if self.model_path.exists():
            try:
                data = joblib.load(self.model_path)
                self.isolation_forest = data.get("model")
                self.category_stats = data.get("stats", {})
                self.category_to_idx = data.get("category_to_idx", {})
                return
            except Exception:
                pass

        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=config.ML_CONFIG["isolation_forest_contamination"],
            random_state=42
        )

    def save_model(self) -> None:
        """Persists trained model and statistical baseline to disk."""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self.isolation_forest,
            "stats": self.category_stats,
            "category_to_idx": self.category_to_idx
        }, self.model_path)

    def fit_from_database(self, db: DatabaseManager) -> Dict[str, Any]:
        """
        Extracts historical transactions to compute category statistical baselines
        and train the Isolation Forest model.
        """
        rows = db.fetch_all("""
            SELECT id, amount, category, date
            FROM expenses
            WHERE category != 'Salary / Income' AND amount > 0
        """)

        if len(rows) < 10:
            return {"status": "insufficient_data", "count": len(rows)}

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["day_of_week"] = df["date"].dt.dayofweek.fillna(0).astype(int)
        df["log_amount"] = np.log1p(df["amount"].values)

        # 1. Compute Statistical Baseline per Category
        stats = {}
        for cat, group in df.groupby("category"):
            amounts = group["amount"].values
            q1 = float(np.percentile(amounts, 25))
            q3 = float(np.percentile(amounts, 75))
            iqr = q3 - q1
            mean = float(np.mean(amounts))
            std = float(np.std(amounts))
            median = float(np.median(amounts))

            stats[cat] = {
                "count": len(amounts),
                "mean": mean,
                "std": std if std > 0 else 1.0,
                "median": median,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "upper_iqr_bound": q3 + (config.ML_CONFIG["iqr_multiplier"] * iqr),
                "z_score_bound": mean + (config.ML_CONFIG["z_score_threshold"] * std)
            }
        self.category_stats = stats

        # 2. Build Category Encoding for ML
        unique_cats = sorted(df["category"].unique())
        self.category_to_idx = {cat: i for i, cat in enumerate(unique_cats)}
        df["cat_idx"] = df["category"].map(self.category_to_idx).fillna(0).astype(int)

        # 3. Train Isolation Forest (Features: amount, log_amount, day_of_week, cat_idx)
        X = df[["amount", "log_amount", "day_of_week", "cat_idx"]].values
        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=config.ML_CONFIG["isolation_forest_contamination"],
            random_state=42
        )
        self.isolation_forest.fit(X)
        self.save_model()

        return {
            "status": "trained",
            "samples": len(df),
            "categories_profiled": len(stats)
        }

    def evaluate_transaction(
        self,
        amount: float,
        category: str,
        date_str: str,
        currency_sym: str = "₹"
    ) -> Dict[str, Any]:
        """
        Evaluates a single transaction for anomalous behavior.
        Combines Statistical Analysis (IQR / Z-Score) with Machine Learning (Isolation Forest).
        
        Returns:
            is_anomaly: bool
            severity: 'Normal' | 'Medium' | 'High'
            reason: str
            method: str
            score: float
        """
        if category == "Salary / Income" or amount <= 0:
            return {
                "is_anomaly": False,
                "severity": "Normal",
                "reason": "Normal transaction",
                "method": "Rule-Based",
                "score": 0.0
            }

        # 1. Statistical Check
        stats = self.category_stats.get(category)
        is_stat_outlier = False
        stat_reason = ""
        severity = "Normal"

        if stats and stats["count"] >= 3:
            mean = stats["mean"]
            upper_iqr = stats["upper_iqr_bound"]
            z_bound = stats["z_score_bound"]

            if amount > upper_iqr or amount > z_bound:
                is_stat_outlier = True
                ratio = amount / mean if mean > 0 else 1.0
                if ratio >= 4.0:
                    severity = "High"
                else:
                    severity = "Medium"
                stat_reason = (
                    f"Amount {currency_sym}{amount:,.2f} is {ratio:.1f}x higher than your "
                    f"typical average ({currency_sym}{mean:,.2f}) for '{category}'."
                )

        # 2. Machine Learning Check (Isolation Forest)
        is_ml_outlier = False
        ml_score = 0.0
        if self.isolation_forest is not None:
            try:
                dt = pd.to_datetime(date_str, errors="coerce")
                dow = dt.dayofweek if pd.notnull(dt) else 0
                cat_idx = self.category_to_idx.get(category, 0)
                log_amt = np.log1p(amount)

                sample = np.array([[amount, log_amt, dow, cat_idx]])
                pred = self.isolation_forest.predict(sample)[0]  # -1 for anomaly, 1 for normal
                ml_score = float(self.isolation_forest.decision_function(sample)[0])

                if pred == -1:
                    is_ml_outlier = True
            except Exception:
                pass

        # 3. Decision Fusion
        is_anomaly = is_stat_outlier or is_ml_outlier

        if is_stat_outlier and is_ml_outlier:
            method = "Combined (ML & Statistical Outlier)"
            final_reason = stat_reason or "Multi-dimensional anomaly identified by Isolation Forest."
            severity = "High"
        elif is_stat_outlier:
            method = "Statistical Analytics (Category IQR/Z-Score)"
            final_reason = stat_reason
        elif is_ml_outlier:
            method = "Machine Learning (Isolation Forest)"
            final_reason = f"Unusual multivariate spending pattern detected (ML Score: {ml_score:.3f})."
            severity = "Medium"
        else:
            method = "Normal"
            final_reason = "Within standard spending bounds."
            severity = "Normal"

        return {
            "is_anomaly": is_anomaly,
            "severity": severity,
            "reason": final_reason,
            "method": method,
            "score": round(ml_score, 4)
        }

    def scan_and_tag_database(self, db: DatabaseManager, currency_sym: str = "₹") -> int:
        """
        Runs anomaly detection across all database records and updates flags.
        """
        self.fit_from_database(db)

        rows = db.fetch_all("SELECT id, amount, category, date FROM expenses;")
        flagged_count = 0

        for r in rows:
            res = self.evaluate_transaction(r["amount"], r["category"], r["date"], currency_sym)
            if res["is_anomaly"]:
                flagged_count += 1
                db.execute_query(
                    "UPDATE expenses SET is_anomaly = 1, anomaly_reason = ? WHERE id = ?;",
                    (res["reason"], r["id"])
                )
            else:
                db.execute_query(
                    "UPDATE expenses SET is_anomaly = 0, anomaly_reason = NULL WHERE id = ?;",
                    (r["id"],)
                )

        return flagged_count
