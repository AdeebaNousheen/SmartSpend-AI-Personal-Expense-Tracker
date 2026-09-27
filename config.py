"""
SmartSpend - Configuration Module
Defines global application settings, paths, categories, and styling constants.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Database
DB_PATH = DATA_DIR / "smartspend.db"

# Currency Settings
DEFAULT_CURRENCY_SYMBOL = "₹"
DEFAULT_CURRENCY_CODE = "INR"
SUPPORTED_CURRENCIES = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CAD": "CA$",
    "AUD": "AU$",
}

# Application Metadata
APP_NAME = "SmartSpend"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "AI-Powered Personal Expense Tracker"

# Default Categories with distinct UI color representations
DEFAULT_CATEGORIES = [
    {"name": "Food & Dining", "icon": "🍔", "color": "#FF7043", "is_income": 0},
    {"name": "Groceries", "icon": "🛒", "color": "#42A5F5", "is_income": 0},
    {"name": "Transportation", "icon": "🚗", "color": "#FFA726", "is_income": 0},
    {"name": "Housing & Rent", "icon": "🏠", "color": "#AB47BC", "is_income": 0},
    {"name": "Utilities & Bills", "icon": "💡", "color": "#26A69A", "is_income": 0},
    {"name": "Entertainment", "icon": "🎬", "color": "#EC407A", "is_income": 0},
    {"name": "Shopping", "icon": "🛍️", "color": "#7E57C2", "is_income": 0},
    {"name": "Healthcare", "icon": "💊", "color": "#EF5350", "is_income": 0},
    {"name": "Personal Care", "icon": "✂️", "color": "#26C6DA", "is_income": 0},
    {"name": "Education", "icon": "📚", "color": "#8D6E63", "is_income": 0},
    {"name": "Investments", "icon": "📈", "color": "#66BB6A", "is_income": 0},
    {"name": "Other Expense", "icon": "📦", "color": "#78909C", "is_income": 0},
    {"name": "Salary / Income", "icon": "💰", "color": "#4CAF50", "is_income": 1},
]

# Payment Methods
PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Cash", "Net Banking", "Other"]

# Machine Learning & Analytics Parameters
ML_CONFIG = {
    # Category Prediction
    "category_model_path": MODELS_DIR / "category_classifier.joblib",
    "min_category_training_samples": 10,
    
    # Anomaly Detection
    "anomaly_model_path": MODELS_DIR / "anomaly_detector.joblib",
    "isolation_forest_contamination": 0.05,
    "z_score_threshold": 2.5,
    "iqr_multiplier": 1.75,
    
    # Spending Forecasting
    "forecasting_model_path": MODELS_DIR / "spending_forecaster.joblib",
    "min_forecast_days_required": 14,
    "min_forecast_span_weeks": 2,
    "min_forecast_transactions": 20,
    "forecast_horizon_days": 30,
}

# UI Theme & Colors
THEME_CONFIG = {
    "appearance_mode": "dark",  # "dark" or "light"
    "color_theme": "blue",
    "colors": {
        "primary": "#3B82F6",
        "primary_hover": "#2563EB",
        "secondary": "#64748B",
        "accent": "#10B981",
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "success": "#10B981",
        "info": "#06B6D4",
        "card_bg_dark": "#1E293B",
        "card_bg_light": "#FFFFFF",
        "sidebar_dark": "#0F172A",
        "sidebar_light": "#F8FAFC",
        "text_dark": "#F8FAFC",
        "text_muted": "#94A3B8",
        "border_dark": "#334155",
        "demo_banner_bg": "#D97706",
    }
}
