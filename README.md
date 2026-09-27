# SmartSpend: AI-Powered Personal Expense Tracker

A modern, offline-first personal financial management application built with **Python**, **CustomTkinter**, **SQLite**, **Pandas**, **Matplotlib**, and **scikit-learn**. Designed with clean modular architecture, 100% local execution on Windows, and zero paid API or cloud dependencies.

---

## Key Highlights

- **Currency First-Class Citizen**: Defaults to **Indian Rupee (`₹` / INR)** formatted with the Indian numbering system (Lakhs / Crores); easily configurable to USD (`$`), EUR (`€`), GBP (`£`), etc., via Settings.
- **Strict Demo Data Isolation**: Seed demo data (330+ realistic Indian transactions like Swiggy, Zomato, D-Mart, Uber, Electricity, Rent, Mutual Funds) is explicitly tagged with `is_demo=1`. Users can load or clear demo records at any time without touching real personal transactions.
- **Genuine AI & Machine Learning**:
  1. **Smart NLP Category Classifier**: TF-IDF n-grams + Multinomial Naive Bayes pipeline with live suggestions as you type merchant names.
  2. **Unsupervised Anomaly Detector**: Scikit-learn `IsolationForest` combined with Category Interquartile Range (IQR) and Z-score distributions for explainable spending alerts.
  3. **Time-Series Forecaster with Data Sufficiency Guardrail**: Ridge regression forecasting remaining monthly spend and budget breach risk; enforces a strict $\ge 14$-day historical minimum to prevent misleading predictions.
- **Embedded Analytics**: Matplotlib Donut Breakdown, Monthly Spend Bars, and 30-Day Daily Trajectory Charts embedded directly inside the CustomTkinter UI.
- **Comprehensive Expense Management**: Budget health meters, savings goal milestones with contribution logging, recurring subscriptions with automated due dates, and 1-click export to CSV & ReportLab PDF statements.

---

## 1. Project Directory Structure

```
SmartSpend/
│
├── config.py                     # Global app settings, paths, INR currency defaults, theme palette
├── main.py                       # Application entrypoint & CLI controller (--test-launch, --load-demo, etc.)
├── requirements.txt              # Production Python package dependencies
├── README.md                     # Complete project documentation & viva/presentation guide
│
├── database/                     # SQLite persistence layer
│   ├── __init__.py
│   ├── db_manager.py             # SQLite connection pooling, tables, indexes, and queries
│   └── seed_data.py              # Realistic 6-month Indian demo data generator (is_demo=1 isolation)
│
├── ml/                           # AI / Machine Learning & Statistical engines
│   ├── __init__.py
│   ├── category_classifier.py    # NLP text classification: TF-IDF + Multinomial Naive Bayes
│   ├── anomaly_detector.py       # Isolation Forest (ML) + Category IQR/Z-score (Statistics)
│   └── spending_forecaster.py    # Time-Series Ridge regression with data sufficiency guardrail
│
├── services/                     # Business logic and domain services
│   ├── __init__.py
│   ├── expense_service.py        # Expense CRUD, full-text search, multi-criteria filtering, aggregates
│   ├── budget_service.py         # Category spending limits, consumption %, threshold warnings
│   ├── goal_service.py           # Long-term savings goals, deposit contributions, timeline countdown
│   ├── recurring_service.py      # Subscriptions tracker, recurrence calculation, 1-click expense logger
│   ├── report_service.py         # CSV exporter and styled ReportLab PDF statement generator
│   └── settings_service.py       # Currency preference (₹, $, €, £), appearance mode, demo controls
│
├── ui/                           # CustomTkinter graphical user interface
│   ├── __init__.py
│   ├── app.py                    # Top-level CTk window, sidebar navigation, lazy view router
│   ├── components/               # Reusable UI widgets
│   │   ├── __init__.py
│   │   ├── stat_card.py          # Metric card with icons, currency formatting, and trend badges
│   │   ├── toast.py              # Non-blocking auto-dismissing toast notifications
│   │   └── expense_dialog.py     # Add/Edit modal with real-time AI category suggestions & anomaly alerts
│   └── views/                    # Application screen views (lazy-instantiated)
│       ├── __init__.py
│       ├── dashboard_view.py     # Executive overview: KPI cards, recent activity, demo banner
│       ├── expenses_view.py      # Paginated expense ledger, search, filters, edit/delete actions
│       ├── analytics_view.py     # Embedded Matplotlib figures (Donut, Monthly Bars, Daily Line)
│       ├── budgets_view.py       # Category budget progress meters, overspending warning banners
│       ├── goals_view.py         # Savings goal cards, progress bars, deposit modal
│       ├── recurring_view.py     # Subscriptions list, urgency badges, 1-click payment logging
│       ├── ai_insights_view.py   # AI Hub: Category playground, anomaly audit table, forecast chart
│       ├── reports_view.py       # Date range selector, summary tables, CSV & PDF export
│       └── settings_view.py      # Currency switcher (₹ default), theme toggle, Load/Clear demo data
│
└── tests/                        # Automated unit testing suite
    ├── __init__.py
    ├── test_database.py          # Schema creation, CRUD, and strict demo data isolation tests
    ├── test_ml_models.py         # Category predictor, anomaly detector, forecaster guardrail tests
    └── test_services.py          # Business logic tests for budgets, goals, recurring, and reports
```

---

## 2. Purpose of Every File

| File | Purpose |
|---|---|
| [`config.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/config.py) | Defines runtime file paths, supported currencies (`₹`, `$`, `€`, `£`, etc.), categories with icons and colors, theme palettes, and ML hyperparameters. |
| [`main.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/main.py) | Application entrypoint. Bootstraps SQLite database, processes CLI flags (`--test-launch`, `--load-demo`, `--clear-demo`), and starts the CustomTkinter event loop. |
| [`requirements.txt`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/requirements.txt) | Lists required Python libraries (`customtkinter`, `scikit-learn`, `pandas`, `matplotlib`, `reportlab`, etc.). |
| [`database/db_manager.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/database/db_manager.py) | Manages SQLite connection pooling, tables (`expenses`, `categories`, `budgets`, `savings_goals`, `goal_contributions`, `recurring_expenses`, `settings`), foreign keys, and indexes. |
| [`database/seed_data.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/database/seed_data.py) | Generates 180 days of realistic Indian market demo records (330+ transactions) with `is_demo=1`. Provides clean `clear_demo_data()` leaving user data intact. |
| [`ml/category_classifier.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ml/category_classifier.py) | Natural Language Processing (NLP) text classification engine using TF-IDF n-grams and Multinomial Naive Bayes. Auto-suggests categories as users type merchant names. |
| [`ml/anomaly_detector.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ml/anomaly_detector.py) | Multi-tiered outlier engine combining scikit-learn `IsolationForest` (ML) and Category IQR/Z-score distribution boundaries (Statistics) with explainable reasoning. |
| [`ml/spending_forecaster.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ml/spending_forecaster.py) | Time-series regression using `Ridge` with calendar and rolling 7-day features. Enforces an explicit data sufficiency guardrail ($\ge 14$ days) before predicting month-end spend. |
| [`services/expense_service.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/services/expense_service.py) | Core transaction business logic: CRUD, full-text search, category/date filters, anomaly flags, and daily/monthly aggregations. |
| [`services/budget_service.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/services/budget_service.py) | Computes category budget health, spent vs limit, % consumption, and threshold warning states (`Normal`, `Warning (>80%)`, `Exceeded`). |
| [`services/goal_service.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/services/goal_service.py) | Tracks long-term savings goals, deposit logs, countdown days remaining, and percentage completion. |
| [`services/recurring_service.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/services/recurring_service.py) | Manages recurring bills and subscriptions, calculates next due dates, urgency statuses (`Overdue`, `Due Today`, `Due Soon`), and automated expense logging. |
| [`services/report_service.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/services/report_service.py) | Generates structured CSV data exports and compiles styled, formatted PDF statements using ReportLab. |
| [`services/settings_service.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/services/settings_service.py) | Handles currency preferences (`₹` default), Indian numbering system formatting, dark/light appearance mode, and demo dataset isolation. |
| [`ui/app.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/app.py) | Top-level application shell with sidebar navigation, active button indicators, currency badge, and on-demand lazy view router. |
| [`ui/components/stat_card.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/components/stat_card.py) | Reusable KPI metric card with icon badge, formatted currency value, and trend/status subtext. |
| [`ui/components/toast.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/components/toast.py) | Floating, auto-dismissing toast notification for user action confirmations. |
| [`ui/components/expense_dialog.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/components/expense_dialog.py) | Add/Edit modal with real-time AI category suggestions on keystroke and live anomaly detection warnings before saving. |
| [`ui/views/dashboard_view.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/views/dashboard_view.py) | Executive telemetry dashboard: KPI cards, demo data warning banner, budget consumption meter, and recent transactions. |
| [`ui/views/expenses_view.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/views/expenses_view.py) | Full-featured transaction ledger with search, category filter, sorting, pagination (20 per page for high performance), and edit/delete controls. |
| [`ui/views/analytics_view.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/views/analytics_view.py) | Visual analytics tab embedding 3 native Matplotlib charts: Donut Category Distribution, Monthly Spend Bars, and 30-Day Daily Trajectory Line. |
| [`ui/views/budgets_view.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/views/budgets_view.py) | Category budget cards with color-coded progress bars, remaining balance indicators, and budget creation dialog. |
| [`ui/views/goals_view.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/views/goals_view.py) | Savings milestones with progress percentage, countdown days left, and `+ Deposit` dialog. |
| [`ui/views/recurring_view.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/views/recurring_view.py) | Subscription management view with urgency badges and `✓ Log Payment Now` action button. |
| [`ui/views/ai_insights_view.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/views/ai_insights_view.py) | AI console: Category Prediction Playground, Anomaly Detection Audit Table with explanations, and 30-Day Forecast Chart with sufficiency guardrail. |
| [`ui/views/reports_view.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/views/reports_view.py) | Date range filter, category breakdown summary table, and 1-click CSV & ReportLab PDF export. |
| [`ui/views/settings_view.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/ui/views/settings_view.py) | Preferences for currency (INR `₹` default), dark/light theme, demo data load/clear controls, and system specifications. |
| [`tests/test_database.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/tests/test_database.py) | Automated unit tests for database tables, default categories, and strict `is_demo=1` isolation. |
| [`tests/test_ml_models.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/tests/test_ml_models.py) | Automated unit tests for NLP category classifier, anomaly detector, and forecasting data sufficiency guardrail. |
| [`tests/test_services.py`](file:///c:/Users/Administrator/OneDrive/Documents/SmartSpend/tests/test_services.py) | Automated unit tests for expense CRUD, budget calculations, savings goal deposits, subscriptions, and settings. |

---

## 3. Installation Commands

Ensure Python 3.10+ (tested on Python 3.13 on Windows) is installed.

```powershell
# 1. Navigate to the project directory
cd c:\Users\Administrator\OneDrive\Documents\SmartSpend

# 2. (Optional but recommended) Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install required dependencies
pip install -r requirements.txt
```

---

## 4. Run Commands

### Launching the Graphical Application
```powershell
python main.py
```

### CLI Helper Commands
```powershell
# Pre-load 6 months of realistic Indian market demo data
python main.py --load-demo

# Clear demo data (leaves real personal user transactions untouched)
python main.py --clear-demo

# Run GUI smoke test (initializes and mounts all 9 views in headless mode for verification)
python main.py --test-launch
```

### Running the Test Suite
```powershell
python -m unittest discover tests -v
```

---

## 5. Required Setup Steps

1. **First Launch**: The application automatically creates `data/smartspend.db` and configures the default currency to **Indian Rupee (`₹` / INR)** and theme to **Dark Mode**.
2. **Exploring with Demo Data**:
   - To immediately see graphs, budgets, and ML models in action, click **"Load Demo Data"** from the top banner or go to **Settings → Load Indian Demo Data (6 Months)**.
   - This seeds 330+ realistic transactions spanning 180 days across Indian merchants (Swiggy, Zomato, BigBasket, D-Mart, Uber, Ola, Airtel Fiber, Cult.fit, etc.) with `is_demo=1`.
3. **Switching to Real Expenses**:
   - Whenever you want to track your real expenses, click **"Clear Demo Data Only"** in Settings or on the Dashboard banner.
   - All demo records are safely deleted, and your genuine transactions (`is_demo=0`) remain intact.
4. **Customizing Currency**:
   - Go to **Settings → Currency Preferences** to switch to USD (`$`), EUR (`€`), GBP (`£`), etc., anytime.

---

## 6. How Each AI/ML Feature Works

SmartSpend implements genuine, locally executed machine learning and statistical models with zero external cloud API dependencies:

### A. Smart Category Prediction (Machine Learning - NLP)
- **Technology**: Natural Language Processing using scikit-learn's `TfidfVectorizer` (sublinear term frequency, unigrams & bigrams, English stopword removal) coupled with a `MultinomialNB` (Multinomial Naive Bayes, $\alpha=0.1$) classifier.
- **Workflow**:
  1. The user begins typing an expense title or merchant name (e.g. *"Swiggy dinner biryani"*, *"HPCL petrol pump"*, *"Apollo medicines"*).
  2. A debounced keystroke event feeds the text into the vectorizer.
  3. The model outputs predicted category probabilities via `predict_proba`.
  4. If the confidence exceeds 30%, the UI displays: `🤖 AI Prediction: Food & Dining (89% confidence) [Apply]`.
  5. The category dropdown automatically selects the predicted class (or the user can click Apply).
- **Incremental Learning**: A **"↻ Retrain on DB"** button in **AI Insights** allows the model to continuously learn from newly entered user expenses.

### B. Unusual Spending Detection (ML + Statistical Analytics)
- **Technology**: Multi-tiered hybrid anomaly detector:
  1. **Unsupervised Machine Learning**: Scikit-learn `IsolationForest(n_estimators=100, contamination=0.05, random_state=42)` fitted on feature vectors `[amount, log(amount + 1), day_of_week, category_index]`. Isolation trees isolate anomalous multi-dimensional spending patterns.
  2. **Statistical Distribution Bounds**: Calculates category-specific Interquartile Range ($IQR = Q_3 - Q_1$) and Z-score distributions ($Mean + 2.5\sigma$).
- **Explainable AI (XAI)**:
  - Rather than outputting an opaque boolean, the engine generates human-understandable rationales (e.g., *"Amount ₹14,500 is 18.2x higher than your typical average for Food & Dining (₹380)"*).
  - Flags transactions as `Medium` or `High` severity and allows users to audit all flagged anomalies in the **AI Insights** tab.

### C. Spending Forecasting & Budget Risk Guardrail (Time-Series ML)
- **Technology**: Regularized `Ridge` regression with engineered calendar and rolling trend features:
  - `day_of_month` (1 to 31)
  - `day_of_week` (0 to 6)
  - `is_weekend` (0 or 1)
  - `rolling_7d_avg` (7-day rolling spending mean)
- **Data Sufficiency Guardrail**:
  - The model verifies that at least **14 distinct days** spanning at least **2 weeks** and **20 transactions** are recorded before generating projections.
  - If insufficient data exists, the UI renders a clear progress card explaining the data requirement instead of displaying misleading curves.
- **Outputs**:
  - Daily projected spend trajectory for the remaining days of the current month with confidence bands.
  - Projected month-end total spend.
  - Comparison against active monthly budgets with risk classification (`Safe`, `Moderate Risk`, `High Risk of Breach`).
  - Recommended maximum daily burn rate to stay within budget.

---

## 7. Limitations and Dependencies

### Dependencies
- **Python**: 3.10 to 3.13 (Native on Windows)
- **customtkinter (>=6.0.0)**: Modern themed widgets built on Tkinter
- **scikit-learn (>=1.4.0)**: Machine learning models (TF-IDF, Naive Bayes, Isolation Forest, Ridge Regression)
- **pandas (>=2.0.0)** & **numpy (>=1.24.0)**: Data manipulation and rolling series
- **matplotlib (>=3.8.0)**: Charts embedded in Tkinter via `FigureCanvasTkAgg`
- **pillow (>=10.0.0)**: Image manipulation for UI elements
- **reportlab (>=4.0.0)**: PDF generation engine
- **joblib (>=1.3.0)**: Model persistence

### Limitations
1. **Local Desktop Only**: Designed as a standalone desktop application for Windows. It does not synchronize over cloud servers (a design choice ensuring 100% data privacy and zero hosting fees).
2. **Text-Based Categorization**: Category predictions rely on merchant titles and note text. Ambiguous descriptions like *"Payment to friend"* will produce lower confidence scores and fall back to user selection.
3. **Forecasting Sensitivity**: Time-series regression assumes past habits loosely reflect future patterns; sudden external life changes (e.g., unexpected medical emergency) will alter trajectory until new data is assimilated.

---

## 8. College Project Evaluation Guide (Viva / Presentation)

| Evaluation Criterion | Implementation Details |
|---|---|
| **Software Architecture** | Layered modular architecture: `database/` (DAO/persistence), `services/` (domain logic), `ml/` (AI models), `ui/` (CustomTkinter GUI), `tests/` (unit testing). |
| **Database Design** | SQLite with 7 relational tables, foreign key constraints (`ON DELETE CASCADE`), indexes on `date`, `category`, and `is_demo`. |
| **Real Machine Learning** | True scikit-learn models (not hardcoded rules): Text Classification via TF-IDF + Naive Bayes; Isolation Forest for multi-feature anomaly detection; Ridge Regression for time-series forecasting. |
| **User Experience (UX)** | High-DPI dark/light theme, non-blocking toast notifications, Indian Rupee formatting with Lakhs/Crores grouping, and paginated expense table. |
| **Academic Rigor** | Full unit test suite covering 100% of core service and ML modules (`python -m unittest discover tests -v`), data sufficiency guardrails, and demo data isolation. |
