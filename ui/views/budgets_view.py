"""
SmartSpend - View: Budgets Management
Interactive category budget tracking with visual progress gauges,
remaining balance calculations, and automatic threshold warning badges.
"""

from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
from services.budget_service import BudgetService
from services.expense_service import ExpenseService
from services.settings_service import SettingsService
from ui.components.toast import show_toast


class BudgetsView(ctk.CTkScrollableFrame):
    """Monthly budget planning and consumption monitor."""

    def __init__(
        self,
        master,
        budget_service: BudgetService,
        expense_service: ExpenseService,
        settings_service: SettingsService,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.budget_svc = budget_service
        self.expense_svc = expense_service
        self.settings_svc = settings_service

        self.grid_columnconfigure(0, weight=1)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        # 1. Header Row
        header_f = ctk.CTkFrame(self, fg_color="transparent")
        header_f.pack(fill="x", padx=16, pady=(12, 10))

        ctk.CTkLabel(
            header_f,
            text="Monthly Budget Planner",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        self.add_budget_btn = ctk.CTkButton(
            header_f,
            text="+ Set Category Budget",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=36,
            corner_radius=8,
            command=self._open_budget_dialog
        )
        self.add_budget_btn.pack(side="right")

        # 2. Executive Summary Banner
        self.summary_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155"
        )
        self.summary_card.pack(fill="x", padx=16, pady=(0, 14))
        for c in range(4):
            self.summary_card.grid_columnconfigure(c, weight=1)

        self.lbl_total_budget = ctk.CTkLabel(self.summary_card, text="Budgeted: ₹0.00", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
        self.lbl_total_budget.grid(row=0, column=0, padx=12, pady=14)

        self.lbl_total_spent = ctk.CTkLabel(self.summary_card, text="Spent: ₹0.00", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
        self.lbl_total_spent.grid(row=0, column=1, padx=12, pady=14)

        self.lbl_remaining = ctk.CTkLabel(self.summary_card, text="Remaining: ₹0.00", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10B981")
        self.lbl_remaining.grid(row=0, column=2, padx=12, pady=14)

        self.lbl_alerts = ctk.CTkLabel(self.summary_card, text="Alerts: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F59E0B")
        self.lbl_alerts.grid(row=0, column=3, padx=12, pady=14)

        # 3. Category Budgets Grid Container
        self.budgets_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.budgets_grid.pack(fill="both", expand=True, padx=16, pady=0)
        self.budgets_grid.grid_columnconfigure(0, weight=1)
        self.budgets_grid.grid_columnconfigure(1, weight=1)

    def refresh(self):
        """Fetch current month budgets and render progress cards."""
        today = datetime.now().date()
        current_month = today.strftime("%Y-%m")

        status_list = self.budget_svc.get_budget_status(current_month)
        summary = self.budget_svc.get_overall_budget_summary(current_month)

        # Update Summary Banner
        self.lbl_total_budget.configure(text=f"Budgeted: {self.settings_svc.format_currency(summary['total_budget'])}")
        self.lbl_total_spent.configure(text=f"Spent: {self.settings_svc.format_currency(summary['total_spent'])}")
        self.lbl_remaining.configure(
            text=f"Remaining: {self.settings_svc.format_currency(summary['total_remaining'])}",
            text_color="#10B981" if summary["total_remaining"] > 0 else "#EF4444"
        )
        total_alerts = summary["warning_count"] + summary["exceeded_count"]
        self.lbl_alerts.configure(
            text=f"Alerts: {total_alerts} ({summary['exceeded_count']} Overbudget)",
            text_color="#EF4444" if summary["exceeded_count"] > 0 else ("#F59E0B" if summary["warning_count"] > 0 else "#10B981")
        )

        for widget in self.budgets_grid.winfo_children():
            widget.destroy()

        if not status_list:
            empty = ctk.CTkLabel(
                self.budgets_grid,
                text="No budgets defined for this month. Click '+ Set Category Budget' or load demo data in Settings.",
                font=ctk.CTkFont(size=12),
                text_color="#94A3B8"
            )
            empty.pack(pady=40)
            return

        for idx, b in enumerate(status_list):
            row_idx = idx // 2
            col_idx = idx % 2

            card = ctk.CTkFrame(
                self.budgets_grid,
                corner_radius=12,
                fg_color="#1E293B",
                border_width=1,
                border_color="#334155"
            )
            card.grid(row=row_idx, column=col_idx, padx=6, pady=6, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            # Top Card Row: Category Title + Status Badge
            top_box = ctk.CTkFrame(card, fg_color="transparent")
            top_box.pack(fill="x", padx=14, pady=(12, 6))

            cat_title = b["category_name"]
            if b["is_demo"]:
                cat_title += " [Demo]"

            ctk.CTkLabel(
                top_box,
                text=cat_title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#F8FAFC"
            ).pack(side="left")

            # Status Badge
            if b["status"] == "Exceeded":
                badge_bg, badge_txt = "#7F1D1D", "OVERBUDGET"
                bar_color = "#EF4444"
            elif b["status"] == "Warning":
                badge_bg, badge_txt = "#78350F", "WARNING (>80%)"
                bar_color = "#F59E0B"
            else:
                badge_bg, badge_txt = "#064E3B", "NORMAL"
                bar_color = "#10B981"

            badge = ctk.CTkLabel(
                top_box,
                text=f" {badge_txt} ",
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=badge_bg,
                corner_radius=4,
                text_color="#FFFFFF"
            )
            badge.pack(side="right")

            # Middle: Limit vs Spent Details
            mid_box = ctk.CTkFrame(card, fg_color="transparent")
            mid_box.pack(fill="x", padx=14, pady=(0, 6))

            ctk.CTkLabel(
                mid_box,
                text=f"Spent: {self.settings_svc.format_currency(b['spent_amount'])}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#F8FAFC"
            ).pack(side="left")

            ctk.CTkLabel(
                mid_box,
                text=f"Limit: {self.settings_svc.format_currency(b['limit_amount'])}",
                font=ctk.CTkFont(size=12),
                text_color="#94A3B8"
            ).pack(side="right")

            # Progress Bar
            prog = ctk.CTkProgressBar(card, height=10, corner_radius=5, progress_color=bar_color)
            prog.pack(fill="x", padx=14, pady=(0, 6))
            pct_val = min(1.0, b["percentage_used"] / 100.0)
            prog.set(pct_val)

            # Footer: Remaining amount + Action buttons
            foot_box = ctk.CTkFrame(card, fg_color="transparent")
            foot_box.pack(fill="x", padx=14, pady=(0, 10))

            ctk.CTkLabel(
                foot_box,
                text=f"{b['percentage_used']:.1f}% used • {self.settings_svc.format_currency(b['remaining_amount'])} remaining",
                font=ctk.CTkFont(size=11),
                text_color="#94A3B8"
            ).pack(side="left")

            del_btn = ctk.CTkButton(
                foot_box,
                text="✕ Remove",
                width=65,
                height=22,
                font=ctk.CTkFont(size=10),
                fg_color="#334155",
                hover_color="#7F1D1D",
                command=lambda bid=b["id"]: self._delete_budget(bid)
            )
            del_btn.pack(side="right")

    def _open_budget_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Set Category Budget")
        dialog.geometry("400x320")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color="#0F172A")

        ctk.CTkLabel(
            dialog,
            text="Set Monthly Budget Limit",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=20, pady=(20, 12), anchor="w")

        cats = [c["name"] for c in self.expense_svc.get_categories()]
        ctk.CTkLabel(dialog, text="Category", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        cat_var = ctk.StringVar(value=cats[0] if cats else "Food & Dining")
        cat_menu = ctk.CTkOptionMenu(dialog, values=cats, variable=cat_var, height=36, fg_color="#1E293B", button_color="#334155")
        cat_menu.pack(fill="x", padx=20, pady=(2, 10))

        sym = self.settings_svc.get_currency_symbol()
        ctk.CTkLabel(dialog, text=f"Monthly Limit ({sym})", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        amt_entry = ctk.CTkEntry(dialog, placeholder_text="e.g. 10000", height=36, fg_color="#1E293B", border_color="#334155")
        amt_entry.pack(fill="x", padx=20, pady=(2, 16))

        def save():
            try:
                amt = float(amt_entry.get().strip())
                if amt <= 0:
                    raise ValueError
            except ValueError:
                amt_entry.configure(border_color="#EF4444")
                return

            current_month = datetime.now().strftime("%Y-%m")
            self.budget_svc.set_budget(
                category_name=cat_var.get(),
                month_year=current_month,
                limit_amount=amt,
                is_demo=0
            )
            dialog.destroy()
            show_toast(self, f"Budget set for {cat_var.get()}!", "success")
            self.refresh()

        ctk.CTkButton(
            dialog,
            text="Save Budget",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=38,
            command=save
        ).pack(fill="x", padx=20, pady=(0, 20))

    def _delete_budget(self, budget_id: int):
        if messagebox.askyesno("Confirm Removal", "Remove this category budget?"):
            self.budget_svc.delete_budget(budget_id)
            show_toast(self, "Budget removed.", "info")
            self.refresh()
