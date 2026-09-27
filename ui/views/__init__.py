"""Views package initialization."""
from ui.views.dashboard_view import DashboardView
from ui.views.expenses_view import ExpensesView
from ui.views.analytics_view import AnalyticsView
from ui.views.budgets_view import BudgetsView
from ui.views.goals_view import GoalsView
from ui.views.recurring_view import RecurringView
from ui.views.ai_insights_view import AIInsightsView
from ui.views.reports_view import ReportsView
from ui.views.settings_view import SettingsView

__all__ = [
    "DashboardView",
    "ExpensesView",
    "AnalyticsView",
    "BudgetsView",
    "GoalsView",
    "RecurringView",
    "AIInsightsView",
    "ReportsView",
    "SettingsView",
]
