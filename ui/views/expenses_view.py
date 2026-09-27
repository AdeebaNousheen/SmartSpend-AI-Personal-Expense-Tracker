"""
SmartSpend - View: Expenses Management
Complete expense ledger with full-text search, multi-criteria filtering,
sorting, pagination/scrolling, edit/delete actions, and CSV export.
"""

from typing import Optional
from tkinter import ttk, messagebox
import customtkinter as ctk
from services.expense_service import ExpenseService
from services.settings_service import SettingsService
from services.report_service import ReportService
from ml.category_classifier import CategoryClassifier
from ml.anomaly_detector import AnomalyDetector
from ui.components.expense_dialog import ExpenseDialog
from ui.components.toast import show_toast
import config


class ExpensesView(ctk.CTkFrame):
    """Transaction ledger and management table."""

    def __init__(
        self,
        master,
        expense_service: ExpenseService,
        settings_service: SettingsService,
        report_service: ReportService,
        classifier: CategoryClassifier,
        detector: AnomalyDetector,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.expense_svc = expense_service
        self.settings_svc = settings_service
        self.report_svc = report_service
        self.classifier = classifier
        self.detector = detector

        self.current_page = 1
        self.page_size = 20
        self.total_pages = 1

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.build_ui()
        self.refresh()

    def build_ui(self):
        # 1. Header Row
        header_f = ctk.CTkFrame(self, fg_color="transparent")
        header_f.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 10))
        header_f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_f,
            text="Expense Ledger",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(header_f, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        self.export_csv_btn = ctk.CTkButton(
            btn_box,
            text="📥 Export CSV",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            height=36,
            corner_radius=8,
            command=self._export_csv
        )
        self.export_csv_btn.pack(side="left", padx=(0, 8))

        self.add_btn = ctk.CTkButton(
            btn_box,
            text="+ Add Expense",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=36,
            corner_radius=8,
            command=self._open_add_dialog
        )
        self.add_btn.pack(side="left")

        # 2. Filter & Search Control Bar
        filter_bar = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155"
        )
        filter_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Search Entry
        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Search merchant, notes...",
            width=220,
            height=34,
            corner_radius=6,
            fg_color="#0F172A",
            border_color="#334155"
        )
        self.search_entry.pack(side="left", padx=10, pady=8)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        # Category Filter
        cats = ["All Categories"] + [c["name"] for c in self.expense_svc.get_categories()]
        self.cat_filter_var = ctk.StringVar(value="All Categories")
        self.cat_filter = ctk.CTkOptionMenu(
            filter_bar,
            values=cats,
            variable=self.cat_filter_var,
            width=160,
            height=34,
            corner_radius=6,
            fg_color="#0F172A",
            button_color="#334155",
            command=lambda v: self.refresh()
        )
        self.cat_filter.pack(side="left", padx=(0, 8), pady=8)

        # Sort By Filter
        self.sort_var = ctk.StringVar(value="Date (Newest)")
        self.sort_menu = ctk.CTkOptionMenu(
            filter_bar,
            values=["Date (Newest)", "Date (Oldest)", "Amount (Highest)", "Amount (Lowest)"],
            variable=self.sort_var,
            width=140,
            height=34,
            corner_radius=6,
            fg_color="#0F172A",
            button_color="#334155",
            command=lambda v: self.refresh()
        )
        self.sort_menu.pack(side="left", padx=(0, 8), pady=8)

        # Anomaly Toggle Filter
        self.anomaly_only_var = ctk.BooleanVar(value=False)
        self.anomaly_checkbox = ctk.CTkCheckBox(
            filter_bar,
            text="⚠️ Anomalies Only",
            variable=self.anomaly_only_var,
            font=ctk.CTkFont(size=12),
            command=self.refresh
        )
        self.anomaly_checkbox.pack(side="left", padx=8, pady=8)

        # Record count summary
        self.count_label = ctk.CTkLabel(
            filter_bar,
            text="Showing 0 expenses",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.count_label.pack(side="right", padx=12, pady=8)

        # 3. Table Frame with Scrollable Rows
        table_container = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155"
        )
        table_container.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Table Header
        th = ctk.CTkFrame(table_container, fg_color="#0F172A", height=36, corner_radius=6)
        th.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 2))
        th.grid_columnconfigure(1, weight=3)  # Title
        th.grid_columnconfigure(2, weight=2)  # Category
        th.grid_columnconfigure(3, weight=2)  # Amount
        th.grid_columnconfigure(4, weight=2)  # Payment
        th.grid_columnconfigure(5, weight=2)  # Status/Notes
        th.grid_columnconfigure(6, weight=1)  # Actions

        cols = [
            ("Date", 0, 90),
            ("Merchant / Title", 1, 0),
            ("Category", 2, 0),
            ("Amount", 3, 0),
            ("Payment", 4, 0),
            ("Flag / Notes", 5, 0),
            ("Action", 6, 90)
        ]
        for name, col_idx, width in cols:
            lbl = ctk.CTkLabel(
                th,
                text=name,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#94A3B8"
            )
            lbl.grid(row=0, column=col_idx, padx=8, pady=6, sticky="w" if col_idx < 3 else ("e" if col_idx == 3 else "w"))

        # Scrollable Rows
        self.rows_frame = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.rows_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 4))
        self.rows_frame.grid_columnconfigure(1, weight=3)
        self.rows_frame.grid_columnconfigure(2, weight=2)
        self.rows_frame.grid_columnconfigure(3, weight=2)
        self.rows_frame.grid_columnconfigure(4, weight=2)
        self.rows_frame.grid_columnconfigure(5, weight=2)
        self.rows_frame.grid_columnconfigure(6, weight=1)

        # Pagination Control Bar
        self.pagination_frame = ctk.CTkFrame(table_container, fg_color="#0F172A", height=38, corner_radius=6)
        self.pagination_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))

        self.prev_btn = ctk.CTkButton(
            self.pagination_frame,
            text="◀ Previous",
            width=80,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=self._prev_page
        )
        self.prev_btn.pack(side="left", padx=10, pady=5)

        self.page_lbl = ctk.CTkLabel(
            self.pagination_frame,
            text="Page 1 of 1",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8"
        )
        self.page_lbl.pack(side="left", padx=10)

        self.next_btn = ctk.CTkButton(
            self.pagination_frame,
            text="Next ▶",
            width=80,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=self._next_page
        )
        self.next_btn.pack(side="left", padx=4, pady=5)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh(reset_page=False)

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh(reset_page=False)

    def refresh(self, reset_page: bool = True):
        """Fetch and render filtered list of expenses with pagination."""
        if reset_page:
            self.current_page = 1

        search_query = self.search_entry.get().strip() or None
        cat = self.cat_filter_var.get()
        category = None if cat == "All Categories" else cat

        sort_choice = self.sort_var.get()
        if "Highest" in sort_choice:
            sort_by, sort_order = "amount", "DESC"
        elif "Lowest" in sort_choice:
            sort_by, sort_order = "amount", "ASC"
        elif "Oldest" in sort_choice:
            sort_by, sort_order = "date", "ASC"
        else:
            sort_by, sort_order = "date", "DESC"

        is_anomaly = 1 if self.anomaly_only_var.get() else None

        expenses = self.expense_svc.get_expenses(
            category=category,
            search=search_query,
            is_anomaly=is_anomaly,
            sort_by=sort_by,
            sort_order=sort_order
        )

        total_count = len(expenses)
        total_amount = sum(e["amount"] for e in expenses)

        import math
        self.total_pages = max(1, math.ceil(total_count / self.page_size))
        self.current_page = max(1, min(self.current_page, self.total_pages))

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_count)
        paged_expenses = expenses[start_idx:end_idx]

        self.count_label.configure(
            text=f"Showing {start_idx + 1 if total_count > 0 else 0}-{end_idx} of {total_count} expenses ({self.settings_svc.format_currency(total_amount)})"
        )
        self.page_lbl.configure(text=f"Page {self.current_page} of {self.total_pages}")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < self.total_pages else "disabled")

        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        if not paged_expenses:
            empty = ctk.CTkLabel(
                self.rows_frame,
                text="No expenses matching current filter criteria.",
                font=ctk.CTkFont(size=12),
                text_color="#94A3B8"
            )
            empty.pack(pady=40)
            return

        for idx, exp in enumerate(paged_expenses):
            row_bg = "#182234" if idx % 2 == 0 else "#1E293B"
            row = ctk.CTkFrame(self.rows_frame, fg_color=row_bg, height=36, corner_radius=4)
            row.pack(fill="x", pady=1)
            row.grid_columnconfigure(1, weight=3)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=2)
            row.grid_columnconfigure(5, weight=2)
            row.grid_columnconfigure(6, weight=1)

            # Date
            ctk.CTkLabel(
                row,
                text=exp["date"],
                font=ctk.CTkFont(size=11),
                text_color="#94A3B8"
            ).grid(row=0, column=0, padx=8, pady=4, sticky="w")

            # Title
            title_text = exp["title"]
            if exp["is_demo"]:
                title_text += " [Demo]"
            ctk.CTkLabel(
                row,
                text=title_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#F8FAFC"
            ).grid(row=0, column=1, padx=8, pady=4, sticky="w")

            # Category
            cat_badge = ctk.CTkLabel(
                row,
                text=exp["category"],
                font=ctk.CTkFont(size=11),
                text_color="#60A5FA"
            )
            cat_badge.grid(row=0, column=2, padx=8, pady=4, sticky="w")

            # Amount
            amt_color = "#F87171" if exp["is_anomaly"] else "#F8FAFC"
            ctk.CTkLabel(
                row,
                text=self.settings_svc.format_currency(exp["amount"]),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=amt_color
            ).grid(row=0, column=3, padx=8, pady=4, sticky="e")

            # Payment
            ctk.CTkLabel(
                row,
                text=exp["payment_method"],
                font=ctk.CTkFont(size=11),
                text_color="#94A3B8"
            ).grid(row=0, column=4, padx=8, pady=4, sticky="w")

            # Notes / Anomaly Indicator
            if exp["is_anomaly"]:
                note_text = "⚠️ " + (exp["anomaly_reason"] or "Outlier flagged")
                note_col = "#FCA5A5"
            else:
                note_text = exp["notes"] or "—"
                note_col = "#64748B"

            ctk.CTkLabel(
                row,
                text=note_text[:28] + ("..." if len(note_text) > 28 else ""),
                font=ctk.CTkFont(size=10),
                text_color=note_col
            ).grid(row=0, column=5, padx=8, pady=4, sticky="w")

            # Action Buttons (Edit & Delete)
            act_box = ctk.CTkFrame(row, fg_color="transparent")
            act_box.grid(row=0, column=6, padx=4, pady=2, sticky="e")

            ctk.CTkButton(
                act_box,
                text="✎",
                width=24,
                height=24,
                font=ctk.CTkFont(size=12),
                fg_color="#334155",
                hover_color="#475569",
                command=lambda e_data=exp: self._open_edit_dialog(e_data)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act_box,
                text="✕",
                width=24,
                height=24,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#7F1D1D",
                hover_color="#991B1B",
                command=lambda eid=exp["id"], title=exp["title"]: self._delete_expense(eid, title)
            ).pack(side="left", padx=2)

    def _open_add_dialog(self):
        cats = [c["name"] for c in self.expense_svc.get_categories()]
        ExpenseDialog(
            self,
            title="Add Expense",
            categories=cats,
            currency_sym=self.settings_svc.get_currency_symbol(),
            classifier=self.classifier,
            detector=self.detector,
            on_save_callback=self._handle_add_save
        )

    def _handle_add_save(self, data: dict):
        self.expense_svc.add_expense(
            title=data["title"],
            amount=data["amount"],
            category=data["category"],
            date=data["date"],
            payment_method=data["payment_method"],
            notes=data["notes"],
            is_anomaly=data["is_anomaly"],
            anomaly_reason=data["anomaly_reason"],
            is_demo=0
        )
        show_toast(self, "Expense added successfully!", "success")
        self.refresh()

    def _open_edit_dialog(self, expense_data: dict):
        cats = [c["name"] for c in self.expense_svc.get_categories()]
        ExpenseDialog(
            self,
            title=f"Edit Expense #{expense_data['id']}",
            expense_data=expense_data,
            categories=cats,
            currency_sym=self.settings_svc.get_currency_symbol(),
            classifier=self.classifier,
            detector=self.detector,
            on_save_callback=lambda data: self._handle_edit_save(expense_data["id"], data)
        )

    def _handle_edit_save(self, expense_id: int, data: dict):
        self.expense_svc.update_expense(
            expense_id=expense_id,
            title=data["title"],
            amount=data["amount"],
            category=data["category"],
            date=data["date"],
            payment_method=data["payment_method"],
            notes=data["notes"],
            is_anomaly=data["is_anomaly"],
            anomaly_reason=data["anomaly_reason"]
        )
        show_toast(self, "Expense updated successfully!", "info")
        self.refresh()

    def _delete_expense(self, expense_id: int, title: str):
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete expense:\n'{title}'?"):
            self.expense_svc.delete_expense(expense_id)
            show_toast(self, "Expense deleted.", "warning")
            self.refresh()

    def _export_csv(self):
        csv_path = config.REPORTS_DIR / "SmartSpend_Expenses_Export.csv"
        self.report_svc.export_csv(csv_path)
        show_toast(self, f"Exported CSV to {csv_path.name}", "success")
