"""
SmartSpend - View: AI Insights & ML Hub
Comprehensive machine learning demonstration and audit console:
1. Smart NLP Category Prediction Playground with live probability distribution.
2. Multi-tiered Anomaly Detection audit table with explainable AI rationale.
3. Time-Series Spending Forecaster with historical data sufficiency guardrails and budget breach risk.
"""

from typing import Optional
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import config
from services.expense_service import ExpenseService
from services.budget_service import BudgetService
from services.settings_service import SettingsService
from ml.category_classifier import CategoryClassifier
from ml.anomaly_detector import AnomalyDetector
from ml.spending_forecaster import SpendingForecaster
from ui.components.toast import show_toast


class AIInsightsView(ctk.CTkScrollableFrame):
    """Dedicated console for inspecting, testing, and visualizing AI/ML models."""

    def __init__(
        self,
        master,
        expense_service: ExpenseService,
        budget_service: BudgetService,
        settings_service: SettingsService,
        classifier: CategoryClassifier,
        detector: AnomalyDetector,
        forecaster: SpendingForecaster,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.expense_svc = expense_service
        self.budget_svc = budget_service
        self.settings_svc = settings_service
        self.classifier = classifier
        self.detector = detector
        self.forecaster = forecaster

        self.grid_columnconfigure(0, weight=1)
        self.forecast_canvas = None

        self.build_ui()
        self.refresh()

    def build_ui(self):
        # Header
        head_f = ctk.CTkFrame(self, fg_color="transparent")
        head_f.pack(fill="x", padx=16, pady=(12, 10))

        ctk.CTkLabel(
            head_f,
            text="AI & Machine Learning Intelligence Hub",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        # -------------------------------------------------------------
        # SECTION 1: Spending Forecasting & Budget Risk Guardrail
        # -------------------------------------------------------------
        self.forecast_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155"
        )
        self.forecast_card.pack(fill="x", padx=16, pady=(0, 14))

        f_header = ctk.CTkFrame(self.forecast_card, fg_color="transparent")
        f_header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            f_header,
            text="📈 Time-Series Spending Forecasting & Budget Risk Analysis",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        ctk.CTkLabel(
            f_header,
            text="Model: Ridge Regression with Calendar & Rolling Features",
            font=ctk.CTkFont(size=11),
            text_color="#60A5FA"
        ).pack(side="right")

        self.forecast_body = ctk.CTkFrame(self.forecast_card, fg_color="transparent")
        self.forecast_body.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        # -------------------------------------------------------------
        # SECTION 2: NLP Category Prediction Playground
        # -------------------------------------------------------------
        nlp_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155"
        )
        nlp_card.pack(fill="x", padx=16, pady=(0, 14))

        nlp_head = ctk.CTkFrame(nlp_card, fg_color="transparent")
        nlp_head.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            nlp_head,
            text="🧠 Smart Category Classifier Playground (NLP)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        ctk.CTkLabel(
            nlp_head,
            text="Algorithm: TF-IDF n-grams + Multinomial Naive Bayes",
            font=ctk.CTkFont(size=11),
            text_color="#60A5FA"
        ).pack(side="right")

        nlp_body = ctk.CTkFrame(nlp_card, fg_color="transparent")
        nlp_body.pack(fill="x", padx=16, pady=(0, 14))

        input_row = ctk.CTkFrame(nlp_body, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 10))

        self.test_text_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Enter any transaction note (e.g. 'Swiggy biryani', 'Shell petrol', 'Apollo medicines')",
            height=38,
            corner_radius=8,
            fg_color="#0F172A",
            border_color="#334155"
        )
        self.test_text_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.test_text_entry.bind("<Return>", lambda e: self._test_category_predict())

        self.test_pred_btn = ctk.CTkButton(
            input_row,
            text="Test ML Prediction",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=38,
            corner_radius=8,
            command=self._test_category_predict
        )
        self.test_pred_btn.pack(side="left", padx=(0, 8))

        self.retrain_btn = ctk.CTkButton(
            input_row,
            text="↻ Retrain on DB",
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            height=38,
            corner_radius=8,
            command=self._retrain_classifier
        )
        self.retrain_btn.pack(side="left")

        # Prediction Results Display Frame
        self.pred_results_frame = ctk.CTkFrame(nlp_body, fg_color="#0F172A", corner_radius=8)
        self.pred_results_frame.pack(fill="x", pady=(0, 4))

        self.pred_result_label = ctk.CTkLabel(
            self.pred_results_frame,
            text="Enter a merchant or expense note above and click 'Test ML Prediction' to test the model.",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.pred_result_label.pack(padx=14, pady=12)

        # -------------------------------------------------------------
        # SECTION 3: Unusual Spending (Anomaly Detection) Audit Table
        # -------------------------------------------------------------
        anom_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155"
        )
        anom_card.pack(fill="x", padx=16, pady=(0, 14))

        anom_head = ctk.CTkFrame(anom_card, fg_color="transparent")
        anom_head.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            anom_head,
            text="🛡️ Unusual Spending Detection (Explainable AI & Statistics)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        self.rescan_btn = ctk.CTkButton(
            anom_head,
            text="↻ Re-Scan Database for Anomalies",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            height=30,
            corner_radius=6,
            command=self._rescan_anomalies
        )
        self.rescan_btn.pack(side="right")

        # Explanatory subtitle
        ctk.CTkLabel(
            anom_card,
            text="Combines Unsupervised Machine Learning (Isolation Forest) with Category Statistical Distributions (IQR & Z-Score).",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(padx=16, pady=(0, 8), anchor="w")

        self.anom_list_frame = ctk.CTkFrame(anom_card, fg_color="transparent")
        self.anom_list_frame.pack(fill="x", padx=16, pady=(0, 14))

    def refresh(self):
        """Re-evaluates all AI modules and updates views."""
        self._refresh_forecasting()
        self._refresh_anomalies()

    def _refresh_forecasting(self):
        for widget in self.forecast_body.winfo_children():
            widget.destroy()

        sym = self.settings_svc.get_currency_symbol()
        res = self.forecaster.generate_forecast(self.expense_svc.db, currency_sym=sym)

        # Guardrail: Check if data is sufficient
        if not res["is_sufficient"]:
            guard_f = ctk.CTkFrame(self.forecast_body, fg_color="#362F1E", corner_radius=8, border_width=1, border_color="#F59E0B")
            guard_f.pack(fill="x", pady=6)

            ctk.CTkLabel(
                guard_f,
                text="⚠️ Historical Data Sufficiency Guardrail Active",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#FDE68A"
            ).pack(anchor="w", padx=14, pady=(12, 6))

            ctk.CTkLabel(
                guard_f,
                text=res["message"],
                font=ctk.CTkFont(size=12),
                text_color="#FEF3C7",
                justify="left"
            ).pack(anchor="w", padx=14, pady=(0, 10))

            btn_box = ctk.CTkFrame(guard_f, fg_color="transparent")
            btn_box.pack(anchor="w", padx=14, pady=(0, 12))

            ctk.CTkButton(
                btn_box,
                text="Load Indian Sample Data to Preview ML Forecast",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#D97706",
                hover_color="#B45309",
                height=30,
                command=self._load_demo_data_action
            ).pack(side="left")
            return

        # If data is sufficient, render ML forecast metrics + chart
        metrics_f = ctk.CTkFrame(self.forecast_body, fg_color="#0F172A", corner_radius=8)
        metrics_f.pack(fill="x", pady=(0, 10))
        for col in range(4):
            metrics_f.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(metrics_f, text=f"Month Spent So Far:\n{self.settings_svc.format_currency(res['spent_so_far'])}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#F8FAFC").grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkLabel(metrics_f, text=f"Daily Burn Rate:\n{self.settings_svc.format_currency(res['daily_burn_rate'])} / day", font=ctk.CTkFont(size=12, weight="bold"), text_color="#60A5FA").grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkLabel(metrics_f, text=f"Projected Month-End:\n{self.settings_svc.format_currency(res['projected_month_end'])}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#F59E0B").grid(row=0, column=2, padx=10, pady=10)
        ctk.CTkLabel(metrics_f, text=f"Budget Risk:\n{res['budget_risk']}", font=ctk.CTkFont(size=12, weight="bold"), text_color=res["risk_color"]).grid(row=0, column=3, padx=10, pady=10)

        # Risk description box
        risk_box = ctk.CTkFrame(self.forecast_body, fg_color="#0F172A", corner_radius=6)
        risk_box.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            risk_box,
            text=f"💡 AI Insight: {res['risk_desc']}",
            font=ctk.CTkFont(size=12),
            text_color="#E2E8F0"
        ).pack(padx=12, pady=8, anchor="w")

        # Embedded Forecast Chart
        if res.get("forecast_daily"):
            chart_f = ctk.CTkFrame(self.forecast_body, fg_color="#0F172A", corner_radius=8)
            chart_f.pack(fill="x")

            forecast_days = [d["day"] for d in res["forecast_daily"]]
            forecast_preds = [d["predicted_amount"] for d in res["forecast_daily"]]
            lower_b = [d["lower_bound"] for d in res["forecast_daily"]]
            upper_b = [d["upper_bound"] for d in res["forecast_daily"]]

            fig = Figure(figsize=(9.2, 2.6), dpi=100, facecolor="#0F172A")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#0F172A")

            ax.plot(forecast_days, forecast_preds, color="#3B82F6", marker="o", markersize=4, linewidth=2, label="Projected Daily Spend (ML)")
            ax.fill_between(forecast_days, lower_b, upper_b, color="#3B82F6", alpha=0.2, label="Confidence Band")

            if res.get("recommended_daily_cap") and res["recommended_daily_cap"] > 0:
                ax.axhline(res["recommended_daily_cap"], color="#10B981", linestyle="--", linewidth=1.5, label=f"Max Daily Cap to Stay on Budget ({sym}{res['recommended_daily_cap']:,.0f})")

            ax.spines['bottom'].set_color('#475569')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#475569')
            ax.tick_params(colors='#94A3B8', labelsize=8)
            ax.set_xlabel("Day of Current Month", color="#94A3B8", fontsize=8)
            ax.set_ylabel(f"Spend ({sym})", color="#94A3B8", fontsize=8)
            ax.grid(True, linestyle="--", alpha=0.15, color="#94A3B8")
            ax.legend(facecolor="#1E293B", edgecolor="#334155", fontsize=8, labelcolor="#F8FAFC")

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=chart_f)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

    def _refresh_anomalies(self):
        for widget in self.anom_list_frame.winfo_children():
            widget.destroy()

        anomalies = self.expense_svc.get_all_anomalies()

        if not anomalies:
            empty = ctk.CTkLabel(
                self.anom_list_frame,
                text="✓ No unusual spending detected. All transactions align with established spending bounds.",
                font=ctk.CTkFont(size=12),
                text_color="#10B981"
            )
            empty.pack(pady=20)
            return

        for a in anomalies:
            row = ctk.CTkFrame(self.anom_list_frame, fg_color="#451A1A", corner_radius=8, border_width=1, border_color="#EF4444")
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(1, weight=1)

            # Severity badge
            ctk.CTkLabel(
                row,
                text=" ⚠️ ANOMALY ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#DC2626",
                text_color="#FFFFFF",
                corner_radius=4
            ).grid(row=0, column=0, rowspan=2, padx=12, pady=10)

            # Title & Date
            title_str = f"{a['title']} • {a['date']} • {a['category']}"
            if a["is_demo"]:
                title_str += " [Demo]"

            ctk.CTkLabel(
                row,
                text=title_str,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#F8FAFC"
            ).grid(row=0, column=1, sticky="w", padx=6, pady=(8, 0))

            # AI Rationale
            reason_str = a["anomaly_reason"] or "Flagged by multi-dimensional Isolation Forest model."
            ctk.CTkLabel(
                row,
                text=f"AI Explanation: {reason_str}",
                font=ctk.CTkFont(size=11),
                text_color="#FECACA"
            ).grid(row=1, column=1, sticky="w", padx=6, pady=(0, 8))

            # Amount
            ctk.CTkLabel(
                row,
                text=self.settings_svc.format_currency(a["amount"]),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#FCA5A5"
            ).grid(row=0, column=2, rowspan=2, padx=16, sticky="e")

    def _test_category_predict(self):
        text = self.test_text_entry.get().strip()
        if not text:
            return

        pred = self.classifier.predict(text)
        top_cat = pred["predicted_category"]
        conf = pred["confidence"]
        top_3 = pred["top_predictions"]

        for widget in self.pred_results_frame.winfo_children():
            widget.destroy()

        res_box = ctk.CTkFrame(self.pred_results_frame, fg_color="transparent")
        res_box.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            res_box,
            text=f"Predicted Category: {top_cat}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#10B981"
        ).pack(anchor="w")

        ctk.CTkLabel(
            res_box,
            text=f"Confidence Score: {conf:.1f}%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#60A5FA"
        ).pack(anchor="w", pady=(2, 6))

        # Top 3 Candidates
        sub_list = ctk.CTkFrame(res_box, fg_color="transparent")
        sub_list.pack(fill="x")

        for item in top_3:
            c_row = ctk.CTkFrame(sub_list, fg_color="transparent")
            c_row.pack(fill="x", pady=1)

            ctk.CTkLabel(
                c_row,
                text=f"• {item['category']}",
                font=ctk.CTkFont(size=11),
                text_color="#E2E8F0",
                width=160,
                anchor="w"
            ).pack(side="left")

            prog = ctk.CTkProgressBar(c_row, width=150, height=8, corner_radius=4, progress_color="#3B82F6")
            prog.pack(side="left", padx=8)
            prog.set(item["confidence"] / 100.0)

            ctk.CTkLabel(
                c_row,
                text=f"{item['confidence']:.1f}%",
                font=ctk.CTkFont(size=10),
                text_color="#94A3B8"
            ).pack(side="left")

    def _retrain_classifier(self):
        stats = self.classifier.train_on_database(self.expense_svc.db)
        show_toast(self, f"Retrained NLP model on {stats['total_samples']} transactions!", "success")
        self._test_category_predict()

    def _rescan_anomalies(self):
        sym = self.settings_svc.get_currency_symbol()
        flagged = self.detector.scan_and_tag_database(self.expense_svc.db, sym)
        show_toast(self, f"Scanned all records: {flagged} unusual transactions flagged.", "warning" if flagged > 0 else "success")
        self.refresh()

    def _load_demo_data_action(self):
        count = self.settings_svc.load_demo_data()
        self.classifier.train_on_database(self.expense_svc.db)
        self.detector.fit_from_database(self.expense_svc.db)
        show_toast(self, f"Loaded {count} demo records. AI models updated!", "success")
        self.refresh()
