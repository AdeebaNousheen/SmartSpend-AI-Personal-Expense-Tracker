"""
SmartSpend - View: Dashboard
Executive financial dashboard featuring KPI stat cards, budget health meter,
recent transactions, subscription alerts, and demo data isolation banner.
"""

from datetime import datetime
from typing import Callable, Optional
import customtkinter as ctk
import config
from services.expense_service import ExpenseService
from services.budget_service import BudgetService
from services.recurring_service import RecurringService
from services.settings_service import SettingsService
from ml.category_classifier import CategoryClassifier
from ml.anomaly_detector import AnomalyDetector
from ui.components.stat_card import StatCard
from ui.components.expense_dialog import ExpenseDialog
from ui.components.toast import show_toast


class DashboardView(ctk.CTkScrollableFrame):
    """Main dashboard displaying financial telemetry, quick actions, and recent activity."""

    def __init__(
        self,
        master,
        expense_service: ExpenseService,
        budget_service: BudgetService,
        recurring_service: RecurringService,
        settings_service: SettingsService,
        classifier: CategoryClassifier,
        detector: AnomalyDetector,
        on_navigate: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.expense_svc = expense_service
        self.budget_svc = budget_service
        self.recurring_svc = recurring_service
        self.settings_svc = settings_service
        self.classifier = classifier
        self.detector = detector
        self.on_navigate = on_navigate

        self.grid_columnconfigure(0, weight=1)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        # 1. Demo Mode Notification Banner (Visible only if demo data exists)
        self.demo_banner = ctk.CTkFrame(
            self,
            fg_color="#78350F",
            corner_radius=8,
            border_width=1,
            border_color="#F59E0B"
        )
        self.demo_banner.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 6))

        self.demo_banner_label = ctk.CTkLabel(
            self.demo_banner,
            text="⚠️ Demo Mode Active: Displaying synthetic Indian financial records for demonstration. Real user data is kept isolated.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FEF3C7"
        )
        self.demo_banner_label.pack(side="left", padx=14, pady=8)

        self.clear_demo_btn = ctk.CTkButton(
            self.demo_banner,
            text="Clear Demo Data",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#B45309",
            hover_color="#92400E",
            height=26,
            command=self._clear_demo_data
        )
        self.clear_demo_btn.pack(side="right", padx=12, pady=6)

        # 2. Header & Action Row
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 14))
        header_frame.grid_columnconfigure(0, weight=1)

        greeting = self._get_time_greeting()
        self.welcome_label = ctk.CTkLabel(
            header_frame,
            text=f"{greeting}! Here is your financial overview.",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        )
        self.welcome_label.grid(row=0, column=0, sticky="w")

        self.quick_add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add Expense",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=36,
            corner_radius=8,
            command=self._open_add_dialog
        )
        self.quick_add_btn.grid(row=0, column=1, sticky="e")

        # 3. KPI Cards Grid (4 Columns)
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))
        for col in range(4):
            self.cards_frame.grid_columnconfigure(col, weight=1)

        sym = self.settings_svc.get_currency_symbol()
        self.card_spent = StatCard(self.cards_frame, title="Spent This Month", value=f"{sym}0.00", icon="💸")
        self.card_spent.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.card_daily = StatCard(self.cards_frame, title="Daily Average", value=f"{sym}0.00", icon="📊")
        self.card_daily.grid(row=0, column=1, padx=4, sticky="ew")

        self.card_budget = StatCard(self.cards_frame, title="Budget Remaining", value=f"{sym}0.00", icon="🎯")
        self.card_budget.grid(row=0, column=2, padx=4, sticky="ew")

        self.card_subs = StatCard(self.cards_frame, title="Active Subscriptions", value="0", icon="🔄")
        self.card_subs.grid(row=0, column=3, padx=(8, 0), sticky="ew")

        # 4. Budget Meter Section
        self.budget_meter_frame = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155"
        )
        self.budget_meter_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))
        self.budget_meter_frame.grid_columnconfigure(1, weight=1)

        self.budget_header_label = ctk.CTkLabel(
            self.budget_meter_frame,
            text="Monthly Budget Consumption",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        self.budget_header_label.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.budget_pct_label = ctk.CTkLabel(
            self.budget_meter_frame,
            text="0%",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#10B981"
        )
        self.budget_pct_label.grid(row=0, column=2, padx=16, pady=(12, 4), sticky="e")

        self.budget_progress = ctk.CTkProgressBar(
            self.budget_meter_frame,
            height=12,
            corner_radius=6,
            progress_color="#10B981"
        )
        self.budget_progress.grid(row=1, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="ew")
        self.budget_progress.set(0.0)

        self.budget_detail_label = ctk.CTkLabel(
            self.budget_meter_frame,
            text="₹0 spent of ₹0 budgeted",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.budget_detail_label.grid(row=2, column=0, columnspan=3, padx=16, pady=(0, 12), sticky="w")

        # 5. Split Section: Left = Recent Transactions, Right = AI Alerts & Shortcuts
        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.grid(row=4, column=0, sticky="nsew", padx=16, pady=0)
        split_frame.grid_columnconfigure(0, weight=6)
        split_frame.grid_columnconfigure(1, weight=4)

        # Left: Recent Transactions
        self.tx_container = ctk.CTkFrame(
            split_frame,
            corner_radius=12,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155"
        )
        self.tx_container.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        self.tx_container.grid_columnconfigure(0, weight=1)

        tx_header = ctk.CTkFrame(self.tx_container, fg_color="transparent")
        tx_header.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            tx_header,
            text="Recent Transactions",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        view_all_btn = ctk.CTkButton(
            tx_header,
            text="View All →",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color="#334155",
            width=70,
            command=lambda: self.on_navigate("Expenses") if self.on_navigate else None
        )
        view_all_btn.pack(side="right")

        self.tx_list_frame = ctk.CTkFrame(self.tx_container, fg_color="transparent")
        self.tx_list_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        # Right: AI Alerts & Recurring Due
        right_container = ctk.CTkFrame(
            split_frame,
            corner_radius=12,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155"
        )
        right_container.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        right_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right_container,
            text="AI Insights & Bill Alerts",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=16, pady=(12, 8), anchor="w")

        self.alerts_frame = ctk.CTkFrame(right_container, fg_color="transparent")
        self.alerts_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    def _get_time_greeting(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            return "Good morning"
        elif hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"

    def refresh(self):
        """Re-queries data and refreshes all UI widgets."""
        today = datetime.now().date()
        current_month = today.strftime("%Y-%m")
        start_month = f"{current_month}-01"
        end_month = f"{current_month}-31"

        # 1. Check Demo Data State
        has_demo = self.settings_svc.has_demo_data()
        if has_demo:
            demo_count = self.settings_svc.get_demo_count()
            self.demo_banner_label.configure(
                text=f"⚠️ Demo Mode Active: Displaying {demo_count} sample Indian financial records. Real user data is isolated."
            )
            self.demo_banner.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 6))
        else:
            self.demo_banner.grid_forget()

        # 2. Refresh KPI Cards
        total_month_spent = self.expense_svc.get_total_spent(start_date=start_month, end_date=end_month)
        days_passed = max(1, today.day)
        daily_avg = total_month_spent / days_passed

        budget_summary = self.budget_svc.get_overall_budget_summary(current_month)
        total_budget = budget_summary["total_budget"]
        remaining_budget = max(0.0, total_budget - total_month_spent)

        recurring_summary = self.recurring_svc.get_due_summary()

        self.card_spent.update_value(
            self.settings_svc.format_currency(total_month_spent),
            f"Month: {today.strftime('%B %Y')}",
            "#94A3B8"
        )
        self.card_daily.update_value(
            self.settings_svc.format_currency(daily_avg),
            f"Over {days_passed} days",
            "#94A3B8"
        )
        self.card_budget.update_value(
            self.settings_svc.format_currency(remaining_budget),
            f"{budget_summary['overall_pct']}% of limit used",
            "#EF4444" if budget_summary["overall_pct"] >= 100 else ("#F59E0B" if budget_summary["overall_pct"] >= 80 else "#10B981")
        )
        self.card_subs.update_value(
            str(recurring_summary["total_active"]),
            f"{recurring_summary['due_soon_count']} due soon" if recurring_summary["due_soon_count"] > 0 else "All bills up to date",
            "#F59E0B" if recurring_summary["due_soon_count"] > 0 else "#10B981"
        )

        # 3. Budget Meter Update
        if total_budget > 0:
            pct = min(100.0, (total_month_spent / total_budget) * 100.0)
            self.budget_progress.set(pct / 100.0)
            self.budget_pct_label.configure(text=f"{pct:.1f}%")

            if pct >= 100:
                prog_color = "#EF4444"
                self.budget_pct_label.configure(text_color="#EF4444")
            elif pct >= 80:
                prog_color = "#F59E0B"
                self.budget_pct_label.configure(text_color="#F59E0B")
            else:
                prog_color = "#10B981"
                self.budget_pct_label.configure(text_color="#10B981")

            self.budget_progress.configure(progress_color=prog_color)
            self.budget_detail_label.configure(
                text=f"{self.settings_svc.format_currency(total_month_spent)} spent of {self.settings_svc.format_currency(total_budget)} budgeted"
            )
        else:
            self.budget_progress.set(0.0)
            self.budget_pct_label.configure(text="No Budget Set", text_color="#64748B")
            self.budget_detail_label.configure(
                text="Click Budgets in the sidebar to set monthly spending targets."
            )

        # 4. Recent Transactions List
        for widget in self.tx_list_frame.winfo_children():
            widget.destroy()

        recent_txs = self.expense_svc.get_expenses(limit=6, sort_by="date", sort_order="DESC")
        if not recent_txs:
            empty_lbl = ctk.CTkLabel(
                self.tx_list_frame,
                text="No expenses recorded yet. Click '+ Add Expense' or load demo data in Settings!",
                font=ctk.CTkFont(size=12),
                text_color="#94A3B8"
            )
            empty_lbl.pack(pady=20)
        else:
            for tx in recent_txs:
                row_f = ctk.CTkFrame(self.tx_list_frame, fg_color="#0F172A", corner_radius=8)
                row_f.pack(fill="x", pady=3, padx=2)
                row_f.grid_columnconfigure(1, weight=1)

                # Anomaly warning icon if flagged
                anom_badge = "⚠️ " if tx["is_anomaly"] else "• "
                dot_color = "#EF4444" if tx["is_anomaly"] else "#3B82F6"

                icon_lbl = ctk.CTkLabel(row_f, text=anom_badge, font=ctk.CTkFont(size=14), text_color=dot_color)
                icon_lbl.grid(row=0, column=0, rowspan=2, padx=(10, 4), pady=6)

                title_lbl = ctk.CTkLabel(
                    row_f,
                    text=tx["title"],
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#F8FAFC"
                )
                title_lbl.grid(row=0, column=1, sticky="w", padx=(0, 6), pady=(4, 0))

                sub_text = f"{tx['date']} • {tx['category']} • {tx['payment_method']}"
                if tx["is_demo"]:
                    sub_text += " • [Demo]"
                sub_lbl = ctk.CTkLabel(
                    row_f,
                    text=sub_text,
                    font=ctk.CTkFont(size=10),
                    text_color="#94A3B8"
                )
                sub_lbl.grid(row=1, column=1, sticky="w", padx=(0, 6), pady=(0, 4))

                amt_lbl = ctk.CTkLabel(
                    row_f,
                    text=self.settings_svc.format_currency(tx["amount"]),
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#FCA5A5" if tx["is_anomaly"] else "#F8FAFC"
                )
                amt_lbl.grid(row=0, column=2, rowspan=2, padx=12, pady=6, sticky="e")

        # 5. Right Alerts Section
        for widget in self.alerts_frame.winfo_children():
            widget.destroy()

        # Alert A: Anomalies
        anomalies = self.expense_svc.get_all_anomalies()
        if anomalies:
            anom_box = ctk.CTkFrame(self.alerts_frame, fg_color="#451A1A", corner_radius=8, border_width=1, border_color="#EF4444")
            anom_box.pack(fill="x", pady=(0, 8))

            ctk.CTkLabel(
                anom_box,
                text=f"⚠️ {len(anomalies)} Unusual Transactions Flagged",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#FCA5A5"
            ).pack(anchor="w", padx=10, pady=(8, 2))

            latest_anom = anomalies[0]
            ctk.CTkLabel(
                anom_box,
                text=f"Latest: {latest_anom['title']} ({self.settings_svc.format_currency(latest_anom['amount'])})",
                font=ctk.CTkFont(size=11),
                text_color="#FECACA"
            ).pack(anchor="w", padx=10, pady=(0, 4))

            ctk.CTkButton(
                anom_box,
                text="Review in AI Insights →",
                height=24,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#DC2626",
                hover_color="#B91C1C",
                command=lambda: self.on_navigate("AI Insights") if self.on_navigate else None
            ).pack(anchor="e", padx=10, pady=(0, 8))

        # Alert B: Subscriptions due
        due_items = self.recurring_svc.get_recurring_expenses(active_only=True)
        imminent = [i for i in due_items if i["urgency_status"] in ("Overdue", "Due Today", "Due Soon")]
        if imminent:
            due_box = ctk.CTkFrame(self.alerts_frame, fg_color="#362F1E", corner_radius=8, border_width=1, border_color="#F59E0B")
            due_box.pack(fill="x", pady=(0, 8))

            ctk.CTkLabel(
                due_box,
                text=f"🔔 {len(imminent)} Bills Due Soon",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#FDE68A"
            ).pack(anchor="w", padx=10, pady=(8, 2))

            for item in imminent[:2]:
                ctk.CTkLabel(
                    due_box,
                    text=f"• {item['title']}: {self.settings_svc.format_currency(item['amount'])} ({item['urgency_status']})",
                    font=ctk.CTkFont(size=11),
                    text_color="#FEF3C7"
                ).pack(anchor="w", padx=10, pady=1)

            ctk.CTkButton(
                due_box,
                text="Manage Subscriptions →",
                height=24,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#D97706",
                hover_color="#B45309",
                command=lambda: self.on_navigate("Recurring") if self.on_navigate else None
            ).pack(anchor="e", padx=10, pady=(4, 8))
        else:
            good_box = ctk.CTkFrame(self.alerts_frame, fg_color="#064E3B", corner_radius=8, border_width=1, border_color="#10B981")
            good_box.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(
                good_box,
                text="✓ No Overdue Bills",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#A7F3D0"
            ).pack(padx=10, pady=8)

    def _open_add_dialog(self):
        cats = [c["name"] for c in self.expense_svc.get_categories()]
        ExpenseDialog(
            self,
            title="Add New Expense",
            categories=cats,
            currency_sym=self.settings_svc.get_currency_symbol(),
            classifier=self.classifier,
            detector=self.detector,
            on_save_callback=self._handle_save_expense
        )

    def _handle_save_expense(self, data: dict):
        self.expense_svc.add_expense(
            title=data["title"],
            amount=data["amount"],
            category=data["category"],
            date=data["date"],
            payment_method=data["payment_method"],
            notes=data["notes"],
            is_anomaly=data["is_anomaly"],
            anomaly_reason=data["anomaly_reason"],
            is_demo=0  # Genuine user expense
        )
        show_toast(self, "Expense recorded successfully!", "success")
        self.refresh()

    def _clear_demo_data(self):
        count = self.settings_svc.clear_demo_data()
        show_toast(self, f"Removed {count} demo expense records. Real data kept safe.", "info")
        self.refresh()
