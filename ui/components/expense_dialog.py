"""
SmartSpend - Component: ExpenseDialog
Interactive modal dialog for Adding / Editing transactions.
Integrates live AI Category Prediction and real-time Anomaly Detection warnings.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import customtkinter as ctk
import config
from ml.category_classifier import CategoryClassifier
from ml.anomaly_detector import AnomalyDetector


class ExpenseDialog(ctk.CTkToplevel):
    """
    Modal dialog for creating or updating an expense.
    Demonstrates real-time AI assistance:
    - Smart Category suggestion as merchant title is typed
    - Anomaly detection warning if spending amount is unusual for the category
    """

    def __init__(
        self,
        master,
        title: str = "Add Expense",
        expense_data: Optional[Dict[str, Any]] = None,
        categories: Optional[List[str]] = None,
        currency_sym: str = "₹",
        classifier: Optional[CategoryClassifier] = None,
        detector: Optional[AnomalyDetector] = None,
        on_save_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self.title(title)
        self.geometry("520x680")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.currency_sym = currency_sym
        self.classifier = classifier or CategoryClassifier()
        self.detector = detector or AnomalyDetector()
        self.on_save = on_save_callback
        self.expense_data = expense_data

        self.cat_list = categories or [c["name"] for c in config.DEFAULT_CATEGORIES if c["is_income"] == 0]
        self.user_manually_selected_cat = False
        self._typing_timer = None

        self._build_ui()
        self._populate_if_edit()

    def _build_ui(self):
        self.configure(fg_color="#0F172A")
        self.grid_columnconfigure(0, weight=1)

        # Header Title
        self.header_label = ctk.CTkLabel(
            self,
            text=self.title(),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F8FAFC"
        )
        self.header_label.pack(padx=24, pady=(20, 10), anchor="w")

        # Scrollable form container
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24, pady=0)

        # 1. Title / Merchant Entry
        ctk.CTkLabel(form, text="Title / Merchant Name *", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8").pack(anchor="w", pady=(8, 2))
        self.title_entry = ctk.CTkEntry(
            form,
            placeholder_text="e.g. Swiggy biryani, Uber to airport, D-Mart",
            height=38,
            corner_radius=8,
            fg_color="#1E293B",
            border_color="#334155"
        )
        self.title_entry.pack(fill="x", pady=(0, 4))
        self.title_entry.bind("<KeyRelease>", self._on_title_key_release)

        # Live AI Category Recommendation Box
        self.ai_suggest_frame = ctk.CTkFrame(form, fg_color="#1E293B", corner_radius=6, border_width=1, border_color="#3B82F6")
        self.ai_suggest_frame.pack(fill="x", pady=(2, 8))
        self.ai_suggest_frame.pack_forget()  # Hidden until typing triggers

        self.ai_label = ctk.CTkLabel(
            self.ai_suggest_frame,
            text="🤖 AI Suggestion: ...",
            font=ctk.CTkFont(size=11),
            text_color="#60A5FA"
        )
        self.ai_label.pack(side="left", padx=10, pady=4)

        self.apply_ai_btn = ctk.CTkButton(
            self.ai_suggest_frame,
            text="Apply",
            width=55,
            height=24,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self._apply_ai_suggestion
        )
        self.apply_ai_btn.pack(side="right", padx=8, pady=4)

        # 2. Amount Entry
        ctk.CTkLabel(form, text=f"Amount ({self.currency_sym}) *", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8").pack(anchor="w", pady=(8, 2))
        self.amount_entry = ctk.CTkEntry(
            form,
            placeholder_text=f"0.00",
            height=38,
            corner_radius=8,
            fg_color="#1E293B",
            border_color="#334155"
        )
        self.amount_entry.pack(fill="x", pady=(0, 4))
        self.amount_entry.bind("<KeyRelease>", self._check_anomaly_live)

        # 3. Category Dropdown
        ctk.CTkLabel(form, text="Category *", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8").pack(anchor="w", pady=(8, 2))
        self.category_var = ctk.StringVar(value=self.cat_list[0] if self.cat_list else "Other Expense")
        self.category_menu = ctk.CTkOptionMenu(
            form,
            values=self.cat_list,
            variable=self.category_var,
            height=38,
            corner_radius=8,
            fg_color="#1E293B",
            button_color="#334155",
            command=self._on_category_manual_select
        )
        self.category_menu.pack(fill="x", pady=(0, 4))

        # 4. Date Entry
        ctk.CTkLabel(form, text="Date (YYYY-MM-DD) *", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8").pack(anchor="w", pady=(8, 2))
        self.date_entry = ctk.CTkEntry(
            form,
            height=38,
            corner_radius=8,
            fg_color="#1E293B",
            border_color="#334155"
        )
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(fill="x", pady=(0, 4))

        # 5. Payment Method
        ctk.CTkLabel(form, text="Payment Method", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8").pack(anchor="w", pady=(8, 2))
        self.payment_var = ctk.StringVar(value="UPI")
        self.payment_menu = ctk.CTkOptionMenu(
            form,
            values=config.PAYMENT_METHODS,
            variable=self.payment_var,
            height=38,
            corner_radius=8,
            fg_color="#1E293B",
            button_color="#334155"
        )
        self.payment_menu.pack(fill="x", pady=(0, 4))

        # 6. Notes (Optional)
        ctk.CTkLabel(form, text="Notes (Optional)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94A3B8").pack(anchor="w", pady=(8, 2))
        self.notes_entry = ctk.CTkEntry(
            form,
            placeholder_text="Additional details or tags",
            height=38,
            corner_radius=8,
            fg_color="#1E293B",
            border_color="#334155"
        )
        self.notes_entry.pack(fill="x", pady=(0, 8))

        # Real-time Anomaly Warning Box
        self.anomaly_box = ctk.CTkFrame(form, fg_color="#451A1A", corner_radius=6, border_width=1, border_color="#EF4444")
        self.anomaly_box.pack(fill="x", pady=(4, 8))
        self.anomaly_box.pack_forget()  # Hidden by default

        self.anomaly_label = ctk.CTkLabel(
            self.anomaly_box,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#FCA5A5",
            wraplength=440,
            justify="left"
        )
        self.anomaly_label.pack(padx=10, pady=8, fill="x")

        # Action Buttons Row
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(10, 20), side="bottom")

        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#334155",
            hover_color="#475569",
            height=40,
            corner_radius=8,
            command=self.destroy
        )
        self.cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Expense",
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=40,
            corner_radius=8,
            command=self._on_submit
        )
        self.save_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _populate_if_edit(self):
        """Pre-fill fields if editing an existing expense."""
        if not self.expense_data:
            return

        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, self.expense_data.get("title", ""))

        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, str(self.expense_data.get("amount", "")))

        cat = self.expense_data.get("category", "")
        if cat in self.cat_list:
            self.category_var.set(cat)
            self.user_manually_selected_cat = True

        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, self.expense_data.get("date", ""))

        pay = self.expense_data.get("payment_method", "UPI")
        if pay in config.PAYMENT_METHODS:
            self.payment_var.set(pay)

        self.notes_entry.delete(0, "end")
        self.notes_entry.insert(0, self.expense_data.get("notes") or "")

    def _on_title_key_release(self, event=None):
        """Debounced live category prediction on keystroke."""
        if self._typing_timer:
            self.after_cancel(self._typing_timer)
        self._typing_timer = self.after(250, self._perform_category_prediction)

    def _perform_category_prediction(self):
        text = self.title_entry.get().strip()
        if len(text) < 3:
            self.ai_suggest_frame.pack_forget()
            return

        pred = self.classifier.predict(text)
        predicted_cat = pred["predicted_category"]
        conf = pred["confidence"]

        if conf >= 30.0 and predicted_cat in self.cat_list:
            self.current_ai_cat = predicted_cat
            self.ai_label.configure(text=f"🤖 AI Prediction: {predicted_cat} ({conf}% confidence)")
            self.ai_suggest_frame.pack(fill="x", pady=(2, 8))

            # Auto-select if the user hasn't actively chosen a category yet
            if not self.user_manually_selected_cat:
                self.category_var.set(predicted_cat)
                self._check_anomaly_live()
        else:
            self.ai_suggest_frame.pack_forget()

    def _apply_ai_suggestion(self):
        if hasattr(self, "current_ai_cat") and self.current_ai_cat in self.cat_list:
            self.category_var.set(self.current_ai_cat)
            self.user_manually_selected_cat = True
            self.ai_suggest_frame.pack_forget()
            self._check_anomaly_live()

    def _on_category_manual_select(self, selected_choice):
        self.user_manually_selected_cat = True
        self._check_anomaly_live()

    def _check_anomaly_live(self, event=None):
        """Evaluates live whether the typed amount is an anomaly for the category."""
        amt_str = self.amount_entry.get().strip()
        category = self.category_var.get()
        date_str = self.date_entry.get().strip()

        try:
            amount = float(amt_str)
        except ValueError:
            self.anomaly_box.pack_forget()
            return

        eval_res = self.detector.evaluate_transaction(amount, category, date_str, self.currency_sym)
        if eval_res["is_anomaly"]:
            self.anomaly_label.configure(
                text=f"⚠️ Unusual Spending Flagged ({eval_res['severity']} Severity):\n{eval_res['reason']}"
            )
            self.anomaly_box.pack(fill="x", pady=(4, 8))
            self.current_anomaly_reason = eval_res["reason"]
        else:
            self.anomaly_box.pack_forget()
            self.current_anomaly_reason = None

    def _on_submit(self):
        title = self.title_entry.get().strip()
        amt_str = self.amount_entry.get().strip()
        category = self.category_var.get()
        date_str = self.date_entry.get().strip()
        payment = self.payment_var.get()
        notes = self.notes_entry.get().strip()

        if not title:
            self.title_entry.configure(border_color="#EF4444")
            return

        try:
            amount = float(amt_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.amount_entry.configure(border_color="#EF4444")
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.date_entry.configure(border_color="#EF4444")
            return

        # Check anomaly on submission
        eval_res = self.detector.evaluate_transaction(amount, category, date_str, self.currency_sym)
        is_anomaly = 1 if eval_res["is_anomaly"] else 0
        anomaly_reason = eval_res["reason"] if is_anomaly else None

        result_data = {
            "title": title,
            "amount": amount,
            "category": category,
            "date": date_str,
            "payment_method": payment,
            "notes": notes,
            "is_anomaly": is_anomaly,
            "anomaly_reason": anomaly_reason
        }

        if self.on_save:
            self.on_save(result_data)

        self.destroy()
