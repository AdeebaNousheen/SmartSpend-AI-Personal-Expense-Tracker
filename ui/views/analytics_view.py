"""
SmartSpend - View: Analytics & Charts
Embeds Matplotlib charts directly in CustomTkinter via FigureCanvasTkAgg.
Displays: Category Donut Distribution, Monthly Trend Bars, and Daily Trajectory Line.
"""

from datetime import datetime, timedelta
from typing import Optional
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import config
from services.expense_service import ExpenseService
from services.settings_service import SettingsService


class AnalyticsView(ctk.CTkScrollableFrame):
    """Visual financial intelligence hub with embedded Matplotlib visualizations."""

    def __init__(
        self,
        master,
        expense_service: ExpenseService,
        settings_service: SettingsService,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.expense_svc = expense_service
        self.settings_svc = settings_service

        self.grid_columnconfigure(0, weight=1)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        # 1. Header & Range Filter
        top_f = ctk.CTkFrame(self, fg_color="transparent")
        top_f.pack(fill="x", padx=16, pady=(12, 10))

        ctk.CTkLabel(
            top_f,
            text="Financial Analytics & Visualizations",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        self.range_var = ctk.StringVar(value="Last 90 Days")
        self.range_menu = ctk.CTkOptionMenu(
            top_f,
            values=["Last 30 Days", "Last 90 Days", "Last 180 Days", "All Time"],
            variable=self.range_var,
            width=150,
            height=32,
            fg_color="#1E293B",
            button_color="#334155",
            command=lambda v: self.refresh()
        )
        self.range_menu.pack(side="right")

        # 2. Executive Stat Strip
        self.stat_strip = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.stat_strip.pack(fill="x", padx=16, pady=(0, 14))
        for c in range(3):
            self.stat_strip.grid_columnconfigure(c, weight=1)

        self.strip_total = ctk.CTkLabel(self.stat_strip, text="Total: ₹0.00", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
        self.strip_total.grid(row=0, column=0, padx=12, pady=12)

        self.strip_top_cat = ctk.CTkLabel(self.stat_strip, text="Top Category: —", font=ctk.CTkFont(size=13), text_color="#60A5FA")
        self.strip_top_cat.grid(row=0, column=1, padx=12, pady=12)

        self.strip_tx_count = ctk.CTkLabel(self.stat_strip, text="Transactions: 0", font=ctk.CTkFont(size=13), text_color="#94A3B8")
        self.strip_tx_count.grid(row=0, column=2, padx=12, pady=12)

        # 3. Canvas Container Frames
        self.charts_container = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_container.pack(fill="both", expand=True, padx=16, pady=0)
        self.charts_container.grid_columnconfigure(0, weight=1)
        self.charts_container.grid_columnconfigure(1, weight=1)

        # Left: Donut Chart Frame
        self.donut_frame = ctk.CTkFrame(self.charts_container, fg_color="#1E293B", corner_radius=12, border_width=1, border_color="#334155")
        self.donut_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 14))

        # Right: Monthly Trend Bar Chart Frame
        self.bar_frame = ctk.CTkFrame(self.charts_container, fg_color="#1E293B", corner_radius=12, border_width=1, border_color="#334155")
        self.bar_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 14))

        # Bottom: Daily Trajectory Line Chart Frame
        self.line_frame = ctk.CTkFrame(self.charts_container, fg_color="#1E293B", corner_radius=12, border_width=1, border_color="#334155")
        self.line_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 14))

        self.donut_canvas = None
        self.bar_canvas = None
        self.line_canvas = None

    def _get_date_bounds(self) -> tuple:
        today = datetime.now().date()
        choice = self.range_var.get()
        if choice == "Last 30 Days":
            start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        elif choice == "Last 90 Days":
            start = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        elif choice == "Last 180 Days":
            start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
        else:
            start = None
        end = today.strftime("%Y-%m-%d")
        return start, end

    def refresh(self):
        """Re-fetches analytical data and redraws Matplotlib figures."""
        start_date, end_date = self._get_date_bounds()
        total_spent = self.expense_svc.get_total_spent(start_date, end_date)
        by_category = self.expense_svc.get_spending_by_category(start_date, end_date)
        tx_count = sum(c["tx_count"] for c in by_category)

        # Update Stat Strip
        sym = self.settings_svc.get_currency_symbol()
        self.strip_total.configure(text=f"Total Expenditure: {self.settings_svc.format_currency(total_spent)}")
        self.strip_tx_count.configure(text=f"Total Transactions: {tx_count}")
        if by_category:
            top_c = by_category[0]
            pct = (top_c["total_amount"] / total_spent * 100.0) if total_spent > 0 else 0
            self.strip_top_cat.configure(
                text=f"Top Category: {top_c['category']} ({self.settings_svc.format_currency(top_c['total_amount'])} • {pct:.0f}%)"
            )
        else:
            self.strip_top_cat.configure(text="Top Category: None")

        # 1. Render Donut Chart
        self._render_donut_chart(by_category, total_spent)

        # 2. Render Monthly Bar Chart
        self._render_monthly_bar_chart()

        # 3. Render Daily Trajectory Line Chart
        self._render_daily_line_chart()

    def _render_donut_chart(self, by_category, total_spent):
        for widget in self.donut_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.donut_frame,
            text="Category Spending Share",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=14, pady=(12, 4), anchor="w")

        if not by_category or total_spent <= 0:
            ctk.CTkLabel(self.donut_frame, text="No expense data to display.", text_color="#94A3B8").pack(pady=50)
            return

        # Prepare top 6 categories + others
        labels = []
        sizes = []
        palette = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#64748B"]

        top_cats = by_category[:6]
        other_sum = sum(c["total_amount"] for c in by_category[6:])

        for item in top_cats:
            labels.append(item["category"])
            sizes.append(item["total_amount"])

        if other_sum > 0:
            labels.append("Other Categories")
            sizes.append(other_sum)

        fig = Figure(figsize=(4.5, 3.2), dpi=100, facecolor="#1E293B")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1E293B")

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.0f%%",
            pctdistance=0.75,
            startangle=140,
            colors=palette[:len(sizes)],
            textprops=dict(color="#F8FAFC", fontsize=8)
        )
        for autotext in autotexts:
            autotext.set_color("#FFFFFF")
            autotext.set_weight("bold")

        # Create Donut Hole
        centre_circle = matplotlib.patches.Circle((0, 0), 0.55, fc="#1E293B")
        ax.add_artist(centre_circle)
        ax.axis("equal")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.donut_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _render_monthly_bar_chart(self):
        for widget in self.bar_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.bar_frame,
            text="Monthly Spending Trend (Last 6 Months)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=14, pady=(12, 4), anchor="w")

        monthly_data = self.expense_svc.get_monthly_spending(num_months=6)
        if not monthly_data:
            ctk.CTkLabel(self.bar_frame, text="No monthly data recorded.", text_color="#94A3B8").pack(pady=50)
            return

        months = [m["month_year"] for m in monthly_data]
        amounts = [m["total_amount"] for m in monthly_data]

        fig = Figure(figsize=(4.5, 3.2), dpi=100, facecolor="#1E293B")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1E293B")

        bars = ax.bar(months, amounts, color="#3B82F6", width=0.55, edgecolor="#60A5FA", linewidth=0.8)

        # Style axes
        ax.spines['bottom'].set_color('#475569')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#475569')
        ax.tick_params(colors='#94A3B8', labelsize=8)
        ax.grid(axis='y', linestyle='--', alpha=0.2, color='#94A3B8')

        sym = self.settings_svc.get_currency_symbol()
        # Bar annotations
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(
                    f"{sym}{height:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=7, color="#E2E8F0", weight='bold'
                )

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.bar_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _render_daily_line_chart(self):
        for widget in self.line_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.line_frame,
            text="Daily Spending Trajectory (Last 30 Days)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=14, pady=(12, 4), anchor="w")

        daily_data = self.expense_svc.get_daily_spending(days=30)
        if not daily_data:
            ctk.CTkLabel(self.line_frame, text="No daily data recorded.", text_color="#94A3B8").pack(pady=40)
            return

        days = [d["date"][-5:] for d in daily_data]  # MM-DD
        amounts = [d["total_amount"] for d in daily_data]

        fig = Figure(figsize=(9.2, 2.8), dpi=100, facecolor="#1E293B")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1E293B")

        # Line + points
        ax.plot(days, amounts, color="#10B981", marker='o', markersize=3.5, linewidth=1.8, label="Daily Spend")
        
        # Mean reference line
        avg_spend = sum(amounts) / max(1, len(amounts))
        ax.axhline(avg_spend, color="#F59E0B", linestyle=":", linewidth=1.2, label=f"Average ({self.settings_svc.get_currency_symbol()}{avg_spend:,.0f})")

        ax.fill_between(range(len(days)), amounts, color="#10B981", alpha=0.15)

        ax.spines['bottom'].set_color('#475569')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#475569')
        ax.tick_params(colors='#94A3B8', labelsize=8)
        ax.set_xticks(range(0, len(days), 3))  # Display every 3rd day to avoid clutter
        ax.grid(True, linestyle='--', alpha=0.15, color='#94A3B8')
        ax.legend(facecolor="#0F172A", edgecolor="#334155", fontsize=8, labelcolor="#F8FAFC")

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.line_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))
