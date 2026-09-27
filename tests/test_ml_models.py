"""
SmartSpend - Machine Learning Models Unit Tests
Verifies category prediction, anomaly detection accuracy & explanations,
and spending forecaster data sufficiency guardrails.
"""

import unittest
from pathlib import Path
import tempfile
from database.db_manager import DatabaseManager
from database.seed_data import SeedDataManager
from ml.category_classifier import CategoryClassifier
from ml.anomaly_detector import AnomalyDetector
from ml.spending_forecaster import SpendingForecaster


class TestMLModels(unittest.TestCase):
    """Test suite for AI and Machine Learning features."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.db = DatabaseManager(self.temp_path / "test_ml.db")
        self.seed_mgr = SeedDataManager(self.db)
        
        self.cat_model_path = self.temp_path / "test_cat.joblib"
        self.anomaly_model_path = self.temp_path / "test_anomaly.joblib"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_category_classifier_prediction(self):
        """Verify NLP category classifier recognizes common transactions."""
        classifier = CategoryClassifier(model_path=self.cat_model_path)

        # Test Food & Dining predictions
        res_food = classifier.predict("Zomato dinner order with biryani")
        self.assertEqual(res_food["predicted_category"], "Food & Dining")
        self.assertGreater(res_food["confidence"], 30.0)

        # Test Transportation predictions
        res_transport = classifier.predict("Uber cab ride to office")
        self.assertEqual(res_transport["predicted_category"], "Transportation")
        self.assertGreater(res_transport["confidence"], 30.0)

        # Test Entertainment predictions
        res_ent = classifier.predict("Netflix subscription monthly payment")
        self.assertEqual(res_ent["predicted_category"], "Entertainment")

        # Test Groceries
        res_groc = classifier.predict("BigBasket weekly grocery shopping")
        self.assertEqual(res_groc["predicted_category"], "Groceries")

        # Verify top predictions list is populated
        self.assertEqual(len(res_food["top_predictions"]), 3)

    def test_anomaly_detector_logic(self):
        """Verify anomaly detector flags severe spending spikes with rationale."""
        # Load sample data so statistical baselines can be computed
        self.seed_mgr.load_demo_data()

        detector = AnomalyDetector(model_path=self.anomaly_model_path)
        detector.fit_from_database(self.db)

        # Normal meal check (₹400 for Food & Dining)
        normal_eval = detector.evaluate_transaction(400.0, "Food & Dining", "2026-09-25", "₹")
        self.assertFalse(normal_eval["is_anomaly"])
        self.assertEqual(normal_eval["severity"], "Normal")

        # Extreme meal check (₹18,000 for Food & Dining)
        anomaly_eval = detector.evaluate_transaction(18000.0, "Food & Dining", "2026-09-25", "₹")
        self.assertTrue(anomaly_eval["is_anomaly"])
        self.assertIn("Food & Dining", anomaly_eval["reason"])
        self.assertIn("higher than your typical average", anomaly_eval["reason"])
        self.assertIn(anomaly_eval["severity"], ("Medium", "High"))

    def test_spending_forecaster_guardrail(self):
        """
        Verify spending forecaster enforces the historical data sufficiency guardrail
        and does NOT produce misleading projections on insufficient data.
        """
        forecaster = SpendingForecaster()

        # 1. On empty database (0 days)
        res_empty = forecaster.generate_forecast(self.db)
        self.assertFalse(res_empty["is_sufficient"])
        self.assertEqual(res_empty["status"], "insufficient_data")
        self.assertIn("Insufficient Historical Data", res_empty["message"])

        # 2. On sparse data (only 2 days recorded)
        self.db.execute_query("""
            INSERT INTO expenses (title, amount, category, date, payment_method, is_demo)
            VALUES ('Coffee', 150.0, 'Food & Dining', '2026-09-01', 'UPI', 0);
        """)
        self.db.execute_query("""
            INSERT INTO expenses (title, amount, category, date, payment_method, is_demo)
            VALUES ('Lunch', 350.0, 'Food & Dining', '2026-09-02', 'UPI', 0);
        """)
        res_sparse = forecaster.generate_forecast(self.db)
        self.assertFalse(res_sparse["is_sufficient"])
        self.assertEqual(res_sparse["status"], "insufficient_data")

        # 3. On sufficient data (load 180-day demo dataset)
        self.seed_mgr.load_demo_data()
        res_sufficient = forecaster.generate_forecast(self.db)
        self.assertTrue(res_sufficient["is_sufficient"])
        self.assertEqual(res_sufficient["status"], "success")
        self.assertGreater(res_sufficient["projected_month_end"], 0.0)
        self.assertIn("forecast_daily", res_sufficient)
        self.assertIn("budget_risk", res_sufficient)


if __name__ == "__main__":
    unittest.main()
