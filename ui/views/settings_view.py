"""
SmartSpend - View: Settings
Configuration hub for currency preference (INR ₹ default), theme modes,
strict demo data management (load/clear), and system information.
"""

from tkinter import messagebox
from typing import Callable, Optional
import customtkinter as ctk
import config
from services.settings_service import SettingsService
from ml.category_classifier import CategoryClassifier
from ml.anomaly_detector import AnomalyDetector
from ui.components.toast import show_toast


class SettingsView(ctk.CTkScrollableFrame):
    """Application preferences and dataset isolation manager."""

    def __init__(
        self,
        master,
        settings_service: SettingsService,
        classifier: CategoryClassifier,
        detector: AnomalyDetector,
        on_settings_changed: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.settings_svc = settings_service
        self.classifier = classifier
        self.detector = detector
        self.on_settings_changed = on_settings_changed

        self.grid_columnconfigure(0, weight=1)
        self.build_ui()
        self.refresh()

    def build_ui(self):
        # Header
        head_f = ctk.CTkFrame(self, fg_color="transparent")
        head_f.pack(fill="x", padx=16, pady=(12, 10))

        ctk.CTkLabel(
            head_f,
            text="Preferences & Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        # -------------------------------------------------------------
        # CARD 1: Currency & Regional Configuration
        # -------------------------------------------------------------
        curr_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E293B", border_width=1, border_color="#334155")
        curr_card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            curr_card,
            text="💱 Currency Preferences",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=16, pady=(14, 4), anchor="w")

        ctk.CTkLabel(
            curr_card,
            text="Default is Indian Rupee (₹). All monetary totals, formatting, and charts update dynamically.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(padx=16, pady=(0, 10), anchor="w")

        row1 = ctk.CTkFrame(curr_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 14))

        curr_options = [f"{code} ({sym})" for code, sym in config.SUPPORTED_CURRENCIES.items()]
        curr_code = self.settings_svc.get_currency_code()
        curr_sym = self.settings_svc.get_currency_symbol()
        default_val = f"{curr_code} ({curr_sym})"

        self.currency_var = ctk.StringVar(value=default_val if default_val in curr_options else curr_options[0])
        self.curr_menu = ctk.CTkOptionMenu(
            row1,
            values=curr_options,
            variable=self.currency_var,
            width=180,
            height=36,
            fg_color="#0F172A",
            button_color="#334155",
            command=self._on_currency_change
        )
        self.curr_menu.pack(side="left")

        self.curr_preview_lbl = ctk.CTkLabel(
            row1,
            text=f"Sample Preview: {self.settings_svc.format_currency(125400.50)}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10B981"
        )
        self.curr_preview_lbl.pack(side="left", padx=16)

        # -------------------------------------------------------------
        # CARD 2: Theme & Appearance
        # -------------------------------------------------------------
        theme_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E293B", border_width=1, border_color="#334155")
        theme_card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            theme_card,
            text="🎨 Appearance Mode",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=16, pady=(14, 4), anchor="w")

        row2 = ctk.CTkFrame(theme_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 14))

        self.theme_var = ctk.StringVar(value=self.settings_svc.get_appearance_mode().capitalize())
        self.theme_menu = ctk.CTkOptionMenu(
            row2,
            values=["Dark", "Light"],
            variable=self.theme_var,
            width=180,
            height=36,
            fg_color="#0F172A",
            button_color="#334155",
            command=self._on_theme_change
        )
        self.theme_menu.pack(side="left")

        # -------------------------------------------------------------
        # CARD 3: Demo Data Isolation & Controls
        # -------------------------------------------------------------
        demo_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E293B", border_width=1, border_color="#334155")
        demo_card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            demo_card,
            text="🧪 Demo Dataset Isolation & Controls",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=16, pady=(14, 4), anchor="w")

        ctk.CTkLabel(
            demo_card,
            text="Synthetic Indian market demo data is tagged with is_demo=1 and never mixed with genuine user records.\n"
                 "You can load or clear demo data anytime with 1 click without affecting real transactions.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            justify="left"
        ).pack(padx=16, pady=(0, 10), anchor="w")

        self.demo_status_lbl = ctk.CTkLabel(
            demo_card,
            text="Checking dataset status...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#60A5FA"
        )
        self.demo_status_lbl.pack(padx=16, pady=(0, 12), anchor="w")

        btn_row = ctk.CTkFrame(demo_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        self.load_demo_btn = ctk.CTkButton(
            btn_row,
            text="📥 Load Indian Demo Data (6 Months)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#D97706",
            hover_color="#B45309",
            height=36,
            command=self._load_demo_data
        )
        self.load_demo_btn.pack(side="left", padx=(0, 8))

        self.clear_demo_btn = ctk.CTkButton(
            btn_row,
            text="🧹 Clear Demo Data Only",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            height=36,
            command=self._clear_demo_data
        )
        self.clear_demo_btn.pack(side="left", padx=(0, 8))

        self.reset_all_btn = ctk.CTkButton(
            btn_row,
            text="⚠️ Reset All Data",
            font=ctk.CTkFont(size=11),
            fg_color="#7F1D1D",
            hover_color="#991B1B",
            height=36,
            command=self._reset_all_data
        )
        self.reset_all_btn.pack(side="left")

        # -------------------------------------------------------------
        # CARD 4: Application Metadata & Project Spec
        # -------------------------------------------------------------
        about_card = ctk.CTkFrame(self, corner_radius=12, fg_color="#1E293B", border_width=1, border_color="#334155")
        about_card.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            about_card,
            text="ℹ️ System Architecture & College Project Information",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=16, pady=(14, 4), anchor="w")

        spec_text = (
            f"• Application: {config.APP_NAME} v{config.APP_VERSION} ({config.APP_SUBTITLE})\n"
            f"• Platform: Local Windows Desktop (100% Offline, Zero Cloud Dependencies or Paid APIs)\n"
            f"• GUI Framework: CustomTkinter (Modern High-DPI Desktop Widgets)\n"
            f"• Database Engine: SQLite with Foreign Key Integrity & Query Indexing\n"
            f"• Machine Learning: scikit-learn (TF-IDF + Naive Bayes, Isolation Forest, Ridge Regression)\n"
            f"• Analytics & Visualization: Embedded Matplotlib (TkAgg Canvas) + Pandas DataFrames\n"
            f"• Document Generation: ReportLab (PDF Statements) + Python CSV Engine\n"
            f"• Currency Formatting: Indian Numbering System (Lakhs / Crores) with ₹ Symbol"
        )
        ctk.CTkLabel(
            about_card,
            text=spec_text,
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            justify="left"
        ).pack(padx=16, pady=(0, 14), anchor="w")

    def refresh(self):
        """Update demo state and currency preview."""
        has_demo = self.settings_svc.has_demo_data()
        demo_count = self.settings_svc.get_demo_count()

        user_row = self.settings_svc.db.fetch_one("SELECT COUNT(*) as count FROM expenses WHERE is_demo = 0;")
        user_count = user_row["count"] if user_row else 0

        self.demo_status_lbl.configure(
            text=f"Current Database Status: {user_count} Genuine User Records | {demo_count} Isolated Demo Records ({'Demo Mode Active' if has_demo else 'No Demo Data'})",
            text_color="#F59E0B" if has_demo else "#10B981"
        )

        self.curr_preview_lbl.configure(
            text=f"Sample Preview: {self.settings_svc.format_currency(125400.50)}"
        )

    def _on_currency_change(self, choice: str):
        # Extract currency code e.g. "INR" from "INR (₹)"
        code = choice.split()[0]
        self.settings_svc.set_currency(code)
        self.refresh()
        show_toast(self, f"Default currency switched to {code} ({self.settings_svc.get_currency_symbol()})", "success")
        if self.on_settings_changed:
            self.on_settings_changed()

    def _on_theme_change(self, choice: str):
        mode = choice.lower()
        self.settings_svc.set_appearance_mode(mode)
        ctk.set_appearance_mode(mode)
        show_toast(self, f"Appearance mode updated to {choice}!", "info")

    def _load_demo_data(self):
        count = self.settings_svc.load_demo_data()
        self.classifier.train_on_database(self.settings_svc.db)
        self.detector.fit_from_database(self.settings_svc.db)
        self.refresh()
        show_toast(self, f"Loaded {count} sample Indian expenses spanning 6 months!", "success")
        if self.on_settings_changed:
            self.on_settings_changed()

    def _clear_demo_data(self):
        count = self.settings_svc.clear_demo_data()
        self.refresh()
        show_toast(self, f"Removed {count} demo records. Real user data remains untouched!", "info")
        if self.on_settings_changed:
            self.on_settings_changed()

    def _reset_all_data(self):
        if messagebox.askyesno(
            "Confirm Database Reset",
            "WARNING: This will permanently delete ALL expenses, budgets, savings goals, and subscriptions.\n\nAre you sure you want to proceed?"
        ):
            self.settings_svc.clear_all_data()
            self.refresh()
            show_toast(self, "All transaction records have been reset.", "warning")
            if self.on_settings_changed:
                self.on_settings_changed()
