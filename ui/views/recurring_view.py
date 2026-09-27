"""
SmartSpend - View: Recurring Expenses & Subscriptions
Manages recurring bills and subscriptions, tracks upcoming due dates,
and provides 1-click payment logging with automated schedule advancement.
"""

from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
from services.recurring_service import RecurringService
from services.expense_service import ExpenseService
from services.settings_service import SettingsService
from ui.components.toast import show_toast
import config


class RecurringView(ctk.CTkScrollableFrame):
    """Subscription and recurring expense schedule manager."""

    def __init__(
        self,
        master,
        recurring_service: RecurringService,
        expense_service: ExpenseService,
        settings_service: SettingsService,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.recurring_svc = recurring_service
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
            text="Subscriptions & Recurring Expenses",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        self.add_sub_btn = ctk.CTkButton(
            header_f,
            text="+ Add Subscription",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=36,
            corner_radius=8,
            command=self._open_new_sub_dialog
        )
        self.add_sub_btn.pack(side="right")

        # 2. Summary Metric Cards
        self.summary_f = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E293B", border_width=1, border_color="#334155")
        self.summary_f.pack(fill="x", padx=16, pady=(0, 14))
        for c in range(3):
            self.summary_f.grid_columnconfigure(c, weight=1)

        self.lbl_active_count = ctk.CTkLabel(self.summary_f, text="Active: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
        self.lbl_active_count.grid(row=0, column=0, padx=12, pady=14)

        self.lbl_monthly_commit = ctk.CTkLabel(self.summary_f, text="Monthly Commitment: ₹0.00", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
        self.lbl_monthly_commit.grid(row=0, column=1, padx=12, pady=14)

        self.lbl_due_alert = ctk.CTkLabel(self.summary_f, text="Due Soon: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color="#10B981")
        self.lbl_due_alert.grid(row=0, column=2, padx=12, pady=14)

        # 3. Subscriptions List Container
        self.list_container = ctk.CTkFrame(self, fg_color="transparent")
        self.list_container.pack(fill="both", expand=True, padx=16, pady=0)

    def refresh(self):
        """Fetch recurring bills and render cards with action controls."""
        items = self.recurring_svc.get_recurring_expenses(active_only=True)
        summary = self.recurring_svc.get_due_summary()

        self.lbl_active_count.configure(text=f"Active Subscriptions: {summary['total_active']}")
        self.lbl_monthly_commit.configure(
            text=f"Monthly Commitment: {self.settings_svc.format_currency(summary['total_monthly_committed'])}"
        )
        due_str = f"Due Soon / Overdue: {summary['overdue_count'] + summary['due_soon_count']}"
        self.lbl_due_alert.configure(
            text=due_str,
            text_color="#EF4444" if summary["overdue_count"] > 0 else ("#F59E0B" if summary["due_soon_count"] > 0 else "#10B981")
        )

        for widget in self.list_container.winfo_children():
            widget.destroy()

        if not items:
            empty = ctk.CTkLabel(
                self.list_container,
                text="No subscriptions tracked yet. Click '+ Add Subscription' or load demo data in Settings.",
                font=ctk.CTkFont(size=12),
                text_color="#94A3B8"
            )
            empty.pack(pady=40)
            return

        for item in items:
            card = ctk.CTkFrame(
                self.list_container,
                corner_radius=10,
                fg_color="#1E293B",
                border_width=1,
                border_color="#334155"
            )
            card.pack(fill="x", pady=4)
            card.grid_columnconfigure(1, weight=3)

            # Frequency Icon / Urgency indicator
            urg = item["urgency_status"]
            if urg == "Overdue":
                badge_bg, badge_txt, text_col = "#7F1D1D", "OVERDUE", "#FECACA"
            elif urg == "Due Today":
                badge_bg, badge_txt, text_col = "#78350F", "DUE TODAY", "#FDE68A"
            elif urg == "Due Soon":
                badge_bg, badge_txt, text_col = "#78350F", f"DUE IN {item['days_until_due']}d", "#FDE68A"
            else:
                badge_bg, badge_txt, text_col = "#064E3B", f"In {item['days_until_due']}d", "#A7F3D0"

            badge = ctk.CTkLabel(
                card,
                text=f" {badge_txt} ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=badge_bg,
                corner_radius=4,
                text_color=text_col
            )
            badge.grid(row=0, column=0, rowspan=2, padx=12, pady=12)

            # Title & Metadata
            title_text = item["title"]
            if item["is_demo"]:
                title_text += " [Demo]"

            ctk.CTkLabel(
                card,
                text=title_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#F8FAFC"
            ).grid(row=0, column=1, sticky="w", padx=4, pady=(10, 0))

            sub_info = f"Category: {item['category']} • Frequency: {item['frequency']} • Next Due: {item['next_due_date']}"
            if item["last_logged_date"]:
                sub_info += f" • Last Paid: {item['last_logged_date']}"

            ctk.CTkLabel(
                card,
                text=sub_info,
                font=ctk.CTkFont(size=11),
                text_color="#94A3B8"
            ).grid(row=1, column=1, sticky="w", padx=4, pady=(0, 10))

            # Amount
            ctk.CTkLabel(
                card,
                text=self.settings_svc.format_currency(item["amount"]),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#F8FAFC"
            ).grid(row=0, column=2, rowspan=2, padx=14, sticky="e")

            # Actions Box
            act = ctk.CTkFrame(card, fg_color="transparent")
            act.grid(row=0, column=3, rowspan=2, padx=(0, 12), sticky="e")

            ctk.CTkButton(
                act,
                text="✓ Log Payment Now",
                height=28,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#059669",
                hover_color="#047857",
                command=lambda rid=item["id"], rname=item["title"]: self._log_payment(rid, rname)
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                act,
                text="✕",
                width=28,
                height=28,
                font=ctk.CTkFont(size=12),
                fg_color="#334155",
                hover_color="#7F1D1D",
                command=lambda rid=item["id"]: self._delete_recurring(rid)
            ).pack(side="left", padx=2)

    def _open_new_sub_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Recurring Subscription")
        dialog.geometry("420x440")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color="#0F172A")

        ctk.CTkLabel(
            dialog,
            text="Add Subscription or Repeating Bill",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=20, pady=(20, 12), anchor="w")

        ctk.CTkLabel(dialog, text="Title / Service Name *", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        name_entry = ctk.CTkEntry(dialog, placeholder_text="e.g. Netflix, Wi-Fi, Gym, Rent", height=36, fg_color="#1E293B", border_color="#334155")
        name_entry.pack(fill="x", padx=20, pady=(2, 8))

        sym = self.settings_svc.get_currency_symbol()
        ctk.CTkLabel(dialog, text=f"Amount ({sym}) *", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        amt_entry = ctk.CTkEntry(dialog, placeholder_text="0.00", height=36, fg_color="#1E293B", border_color="#334155")
        amt_entry.pack(fill="x", padx=20, pady=(2, 8))

        cats = [c["name"] for c in self.expense_svc.get_categories()]
        ctk.CTkLabel(dialog, text="Category", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        cat_var = ctk.StringVar(value="Entertainment")
        cat_menu = ctk.CTkOptionMenu(dialog, values=cats, variable=cat_var, height=36, fg_color="#1E293B", button_color="#334155")
        cat_menu.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(dialog, text="Frequency", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        freq_var = ctk.StringVar(value="Monthly")
        freq_menu = ctk.CTkOptionMenu(dialog, values=["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"], variable=freq_var, height=36, fg_color="#1E293B", button_color="#334155")
        freq_menu.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(dialog, text="Next Due Date (YYYY-MM-DD) *", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        date_entry = ctk.CTkEntry(dialog, height=36, fg_color="#1E293B", border_color="#334155")
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.pack(fill="x", padx=20, pady=(2, 16))

        def save():
            name = name_entry.get().strip()
            if not name:
                name_entry.configure(border_color="#EF4444")
                return

            try:
                amt = float(amt_entry.get().strip())
                if amt <= 0:
                    raise ValueError
            except ValueError:
                amt_entry.configure(border_color="#EF4444")
                return

            due_dt = date_entry.get().strip()
            try:
                datetime.strptime(due_dt, "%Y-%m-%d")
            except ValueError:
                date_entry.configure(border_color="#EF4444")
                return

            self.recurring_svc.add_recurring_expense(
                title=name,
                amount=amt,
                category=cat_var.get(),
                frequency=freq_var.get(),
                next_due_date=due_dt,
                is_demo=0
            )
            dialog.destroy()
            show_toast(self, f"Added subscription '{name}'!", "success")
            self.refresh()

        ctk.CTkButton(
            dialog,
            text="Save Subscription",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=38,
            command=save
        ).pack(fill="x", padx=20, pady=(0, 20))

    def _log_payment(self, recurring_id: int, title: str):
        self.recurring_svc.log_recurring_expense(recurring_id)
        show_toast(self, f"Payment recorded for '{title}'! Next due date advanced.", "success")
        self.refresh()

    def _delete_recurring(self, recurring_id: int):
        if messagebox.askyesno("Confirm Removal", "Delete this recurring expense schedule?"):
            self.recurring_svc.delete_recurring_expense(recurring_id)
            show_toast(self, "Subscription removed.", "info")
            self.refresh()
