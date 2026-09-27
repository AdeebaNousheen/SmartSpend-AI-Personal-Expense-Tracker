"""
SmartSpend - Main Application Window
Coordinates CustomTkinter application shell, sidebar navigation,
theme synchronization, and dynamic view transitions.
"""

from typing import Dict, Optional
import customtkinter as ctk
import config
from database.db_manager import DatabaseManager
from services.expense_service import ExpenseService
from services.budget_service import BudgetService
from services.goal_service import GoalService
from services.recurring_service import RecurringService
from services.settings_service import SettingsService
from services.report_service import ReportService
from ml.category_classifier import CategoryClassifier
from ml.anomaly_detector import AnomalyDetector
from ml.spending_forecaster import SpendingForecaster
from ui.views.dashboard_view import DashboardView
from ui.views.expenses_view import ExpensesView
from ui.views.analytics_view import AnalyticsView
from ui.views.budgets_view import BudgetsView
from ui.views.goals_view import GoalsView
from ui.views.recurring_view import RecurringView
from ui.views.ai_insights_view import AIInsightsView
from ui.views.reports_view import ReportsView
from ui.views.settings_view import SettingsView


class SmartSpendApp(ctk.CTk):
    """Primary application controller and top-level CustomTkinter window."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        super().__init__()

        # Database and Services Initialization
        self.db = db or DatabaseManager()
        self.settings_svc = SettingsService(self.db)
        self.expense_svc = ExpenseService(self.db)
        self.budget_svc = BudgetService(self.db)
        self.goal_svc = GoalService(self.db)
        self.recurring_svc = RecurringService(self.db)
        self.report_svc = ReportService(self.db)

        # Machine Learning Modules Initialization
        self.classifier = CategoryClassifier()
        self.detector = AnomalyDetector()
        self.forecaster = SpendingForecaster()

        # Window Appearance & Geometry
        mode = self.settings_svc.get_appearance_mode()
        ctk.set_appearance_mode(mode)
        ctk.set_default_color_theme("blue")

        self.title(f"{config.APP_NAME} - {config.APP_SUBTITLE}")
        self.geometry("1180x760")
        self.minsize(1024, 640)

        # Layout: Sidebar (col 0) + Main Content (col 1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.views: Dict[str, ctk.CTkFrame] = {}
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.current_view_name = "Dashboard"

        self._build_sidebar()
        self._build_views()
        self.navigate_to("Dashboard")

    def _build_sidebar(self):
        """Constructs the left navigation panel."""
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0,
            fg_color="#0F172A",
            border_width=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Brand Header
        brand_f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_f.pack(fill="x", padx=16, pady=(20, 24))

        ctk.CTkLabel(
            brand_f,
            text="💳 SmartSpend",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_f,
            text="AI-Powered Finance",
            font=ctk.CTkFont(size=11),
            text_color="#60A5FA"
        ).pack(anchor="w", pady=(2, 0))

        # Navigation Links
        nav_items = [
            ("Dashboard", "📊 Dashboard"),
            ("Expenses", "📝 Expenses"),
            ("Analytics", "📈 Analytics"),
            ("Budgets", "🎯 Budgets"),
            ("Goals", "💰 Savings Goals"),
            ("Recurring", "🔄 Subscriptions"),
            ("AI Insights", "🧠 AI Insights"),
            ("Reports", "📄 Reports"),
            ("Settings", "⚙️ Settings"),
        ]

        self.nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_container.pack(fill="x", padx=10, pady=0)

        for name, label in nav_items:
            btn = ctk.CTkButton(
                self.nav_container,
                text=label,
                anchor="w",
                font=ctk.CTkFont(size=13, weight="normal"),
                fg_color="transparent",
                text_color="#94A3B8",
                hover_color="#1E293B",
                height=38,
                corner_radius=8,
                command=lambda view_name=name: self.navigate_to(view_name)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[name] = btn

        # Sidebar Footer: Currency Badge
        footer_f = ctk.CTkFrame(self.sidebar, fg_color="#1E293B", corner_radius=8)
        footer_f.pack(fill="x", side="bottom", padx=12, pady=16)

        self.sidebar_curr_lbl = ctk.CTkLabel(
            footer_f,
            text=f"Currency: {self.settings_svc.get_currency_code()} ({self.settings_svc.get_currency_symbol()})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#10B981"
        )
        self.sidebar_curr_lbl.pack(padx=8, pady=8)

    def _build_views(self):
        """Registers view constructors for on-demand lazy instantiation."""
        self.content_container = ctk.CTkFrame(self, fg_color="#090D16", corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        self.view_factories = {
            "Dashboard": lambda: DashboardView(
                self.content_container,
                expense_service=self.expense_svc,
                budget_service=self.budget_svc,
                recurring_service=self.recurring_svc,
                settings_service=self.settings_svc,
                classifier=self.classifier,
                detector=self.detector,
                on_navigate=self.navigate_to
            ),
            "Expenses": lambda: ExpensesView(
                self.content_container,
                expense_service=self.expense_svc,
                settings_service=self.settings_svc,
                report_service=self.report_svc,
                classifier=self.classifier,
                detector=self.detector
            ),
            "Analytics": lambda: AnalyticsView(
                self.content_container,
                expense_service=self.expense_svc,
                settings_service=self.settings_svc
            ),
            "Budgets": lambda: BudgetsView(
                self.content_container,
                budget_service=self.budget_svc,
                expense_service=self.expense_svc,
                settings_service=self.settings_svc
            ),
            "Goals": lambda: GoalsView(
                self.content_container,
                goal_service=self.goal_svc,
                settings_service=self.settings_svc
            ),
            "Recurring": lambda: RecurringView(
                self.content_container,
                recurring_service=self.recurring_svc,
                expense_service=self.expense_svc,
                settings_service=self.settings_svc
            ),
            "AI Insights": lambda: AIInsightsView(
                self.content_container,
                expense_service=self.expense_svc,
                budget_service=self.budget_svc,
                settings_service=self.settings_svc,
                classifier=self.classifier,
                detector=self.detector,
                forecaster=self.forecaster
            ),
            "Reports": lambda: ReportsView(
                self.content_container,
                expense_service=self.expense_svc,
                settings_service=self.settings_svc,
                report_service=self.report_svc
            ),
            "Settings": lambda: SettingsView(
                self.content_container,
                settings_service=self.settings_svc,
                classifier=self.classifier,
                detector=self.detector,
                on_settings_changed=self._on_settings_updated
            )
        }

    def navigate_to(self, view_name: str):
        """Swaps active view with lazy instantiation and button styling."""
        if view_name not in self.view_factories:
            return

        # Lazy instantiate view on first access
        if view_name not in self.views:
            self.views[view_name] = self.view_factories[view_name]()

        # Hide other active views
        for name, v in self.views.items():
            if name != view_name:
                v.grid_forget()

        # Update sidebar button visual states
        for name, btn in self.nav_buttons.items():
            if name == view_name:
                btn.configure(
                    fg_color="#2563EB",
                    text_color="#FFFFFF",
                    font=ctk.CTkFont(size=13, weight="bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="#94A3B8",
                    font=ctk.CTkFont(size=13, weight="normal")
                )

        # Show target view and refresh it
        active_view = self.views[view_name]
        active_view.grid(row=0, column=0, sticky="nsew")
        if hasattr(active_view, "refresh"):
            active_view.refresh()

        self.current_view_name = view_name

    def _on_settings_updated(self):
        """Refreshes all views and updates the currency label across the application."""
        curr_code = self.settings_svc.get_currency_code()
        curr_sym = self.settings_svc.get_currency_symbol()
        self.sidebar_curr_lbl.configure(text=f"Currency: {curr_code} ({curr_sym})")

        # Refresh all loaded views
        for v in self.views.values():
            if hasattr(v, "refresh"):
                v.refresh()
