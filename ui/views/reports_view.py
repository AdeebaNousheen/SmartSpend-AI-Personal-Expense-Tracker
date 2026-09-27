"""
SmartSpend - View: Reports & Export
Financial report compiler with custom date range analysis, category distribution breakdown,
and 1-click export to CSV and ReportLab-styled PDF statements.
"""

from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
import config
from services.expense_service import ExpenseService
from services.settings_service import SettingsService
from services.report_service import ReportService
from ui.components.toast import show_toast


class ReportsView(ctk.CTkScrollableFrame):
    """Financial statement generator and exporter."""

    def __init__(
        self,
        master,
        expense_service: ExpenseService,
        settings_service: SettingsService,
        report_service: ReportService,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.expense_svc = expense_service
        self.settings_svc = settings_service
        self.report_svc = report_service

        self.grid_columnconfigure(0, weight=1)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        # 1. Header
        head_f = ctk.CTkFrame(self, fg_color="transparent")
        head_f.pack(fill="x", padx=16, pady=(12, 10))

        ctk.CTkLabel(
            head_f,
            text="Financial Reports & Statements",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        # 2. Filter & Date Range Bar
        filter_card = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E293B", border_width=1, border_color="#334155")
        filter_card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(filter_card, text="Select Period:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8").pack(side="left", padx=(14, 8), pady=10)

        self.period_var = ctk.StringVar(value="Last 30 Days")
        self.period_menu = ctk.CTkOptionMenu(
            filter_card,
            values=["This Month", "Last 30 Days", "Last 90 Days", "Last 180 Days", "All Time"],
            variable=self.period_var,
            width=140,
            height=32,
            fg_color="#0F172A",
            button_color="#334155",
            command=lambda v: self.refresh()
        )
        self.period_menu.pack(side="left", padx=4, pady=10)

        # Export Buttons
        self.export_pdf_btn = ctk.CTkButton(
            filter_card,
            text="📄 Generate PDF Report",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            height=32,
            command=self._generate_pdf
        )
        self.export_pdf_btn.pack(side="right", padx=(4, 14), pady=10)

        self.export_csv_btn = ctk.CTkButton(
            filter_card,
            text="📥 Export CSV",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=32,
            command=self._export_csv
        )
        self.export_csv_btn.pack(side="right", padx=4, pady=10)

        # 3. Summary KPI Row
        self.summary_f = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E293B", border_width=1, border_color="#334155")
        self.summary_f.pack(fill="x", padx=16, pady=(0, 14))
        for col in range(4):
            self.summary_f.grid_columnconfigure(col, weight=1)

        self.lbl_total = ctk.CTkLabel(self.summary_f, text="Total Spent:\n₹0.00", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F8FAFC")
        self.lbl_total.grid(row=0, column=0, padx=10, pady=12)

        self.lbl_tx_count = ctk.CTkLabel(self.summary_f, text="Transactions:\n0", font=ctk.CTkFont(size=13, weight="bold"), text_color="#60A5FA")
        self.lbl_tx_count.grid(row=0, column=1, padx=10, pady=12)

        self.lbl_avg_tx = ctk.CTkLabel(self.summary_f, text="Avg / Expense:\n₹0.00", font=ctk.CTkFont(size=13, weight="bold"), text_color="#10B981")
        self.lbl_avg_tx.grid(row=0, column=2, padx=10, pady=12)

        self.lbl_anom_count = ctk.CTkLabel(self.summary_f, text="Anomalies:\n0", font=ctk.CTkFont(size=13, weight="bold"), text_color="#F59E0B")
        self.lbl_anom_count.grid(row=0, column=3, padx=10, pady=12)

        # 4. Breakdown Table Container
        self.table_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E293B", border_width=1, border_color="#334155")
        self.table_card.pack(fill="both", expand=True, padx=16, pady=0)

        ctk.CTkLabel(
            self.table_card,
            text="Category Spending Distribution",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=16, pady=(14, 8), anchor="w")

        self.table_body = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.table_body.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    def _get_dates(self) -> tuple:
        today = datetime.now().date()
        p = self.period_var.get()
        if p == "This Month":
            start = today.replace(day=1).strftime("%Y-%m-%d")
        elif p == "Last 30 Days":
            start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        elif p == "Last 90 Days":
            start = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        elif p == "Last 180 Days":
            start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
        else:
            start = None
        end = today.strftime("%Y-%m-%d")
        return start, end

    def refresh(self):
        """Re-computes statement metrics for the selected time window."""
        start_date, end_date = self._get_dates()
        total = self.expense_svc.get_total_spent(start_date, end_date)
        by_cat = self.expense_svc.get_spending_by_category(start_date, end_date)
        tx_count = sum(c["tx_count"] for c in by_cat)
        avg_tx = (total / tx_count) if tx_count > 0 else 0.0

        anomalies = self.expense_svc.get_expenses(start_date=start_date, end_date=end_date, is_anomaly=1)

        self.lbl_total.configure(text=f"Total Spent:\n{self.settings_svc.format_currency(total)}")
        self.lbl_tx_count.configure(text=f"Transactions:\n{tx_count}")
        self.lbl_avg_tx.configure(text=f"Avg / Expense:\n{self.settings_svc.format_currency(avg_tx)}")
        self.lbl_anom_count.configure(text=f"Anomalies:\n{len(anomalies)}")

        for widget in self.table_body.winfo_children():
            widget.destroy()

        if not by_cat:
            empty = ctk.CTkLabel(self.table_body, text="No expenses found for the selected period.", text_color="#94A3B8")
            empty.pack(pady=30)
            return

        for c in by_cat:
            row = ctk.CTkFrame(self.table_body, fg_color="#0F172A", corner_radius=6, height=36)
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(0, weight=3)
            row.grid_columnconfigure(1, weight=3)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)

            pct = (c["total_amount"] / total * 100.0) if total > 0 else 0.0

            # Category
            ctk.CTkLabel(
                row,
                text=c["category"],
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#F8FAFC"
            ).grid(row=0, column=0, padx=12, pady=6, sticky="w")

            # Progress Bar for Visual Weight
            prog = ctk.CTkProgressBar(row, height=8, corner_radius=4, progress_color="#3B82F6")
            prog.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
            prog.set(pct / 100.0)

            # Amount
            ctk.CTkLabel(
                row,
                text=self.settings_svc.format_currency(c["total_amount"]),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#60A5FA"
            ).grid(row=0, column=2, padx=8, pady=6, sticky="e")

            # Percentage & Count
            ctk.CTkLabel(
                row,
                text=f"{pct:.1f}% ({c['tx_count']} txs)",
                font=ctk.CTkFont(size=11),
                text_color="#94A3B8"
            ).grid(row=0, column=3, padx=12, pady=6, sticky="e")

    def _export_csv(self):
        start_date, end_date = self._get_dates()
        out_file = config.REPORTS_DIR / f"SmartSpend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.report_svc.export_csv(out_file, start_date=start_date, end_date=end_date)
        show_toast(self, f"Exported CSV to {out_file.name}!", "success")

    def _generate_pdf(self):
        start_date, end_date = self._get_dates()
        out_file = config.REPORTS_DIR / f"SmartSpend_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        try:
            self.report_svc.export_pdf(out_file, start_date=start_date, end_date=end_date)
            show_toast(self, f"Generated PDF statement: {out_file.name}!", "success")
            messagebox.showinfo("PDF Generated", f"Financial statement PDF generated successfully at:\n{out_file.resolve()}")
        except Exception as e:
            show_toast(self, f"PDF generation error: {str(e)}", "error")
