"""
SmartSpend - View: Savings Goals
Tracks financial targets, progress percentage gauges, target deadlines,
and logs incremental deposit contributions.
"""

from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
from services.goal_service import GoalService
from services.settings_service import SettingsService
from ui.components.toast import show_toast


class GoalsView(ctk.CTkScrollableFrame):
    """Savings goals tracker and deposit logging interface."""

    def __init__(
        self,
        master,
        goal_service: GoalService,
        settings_service: SettingsService,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.goal_svc = goal_service
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
            text="Savings Goals & Milestones",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        self.add_goal_btn = ctk.CTkButton(
            header_f,
            text="+ New Savings Goal",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=36,
            corner_radius=8,
            command=self._open_new_goal_dialog
        )
        self.add_goal_btn.pack(side="right")

        # 2. Goals Cards Container
        self.cards_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_grid.pack(fill="both", expand=True, padx=16, pady=0)
        self.cards_grid.grid_columnconfigure(0, weight=1)
        self.cards_grid.grid_columnconfigure(1, weight=1)

    def refresh(self):
        """Fetch and render all active savings goals."""
        goals = self.goal_svc.get_goals()

        for widget in self.cards_grid.winfo_children():
            widget.destroy()

        if not goals:
            empty = ctk.CTkLabel(
                self.cards_grid,
                text="No savings goals created yet. Click '+ New Savings Goal' to start saving!",
                font=ctk.CTkFont(size=12),
                text_color="#94A3B8"
            )
            empty.pack(pady=40)
            return

        for idx, g in enumerate(goals):
            row_idx = idx // 2
            col_idx = idx % 2

            card = ctk.CTkFrame(
                self.cards_grid,
                corner_radius=12,
                fg_color="#1E293B",
                border_width=1,
                border_color="#334155"
            )
            card.grid(row=row_idx, column=col_idx, padx=6, pady=6, sticky="nsew")

            # Header: Goal Title + Completion Badge
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(12, 6))

            g_title = g["name"]
            if g["is_demo"]:
                g_title += " [Demo]"

            ctk.CTkLabel(
                top,
                text=g_title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#F8FAFC"
            ).pack(side="left")

            if g["is_completed"]:
                badge = ctk.CTkLabel(
                    top,
                    text=" COMPLETED ✓ ",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#065F46",
                    corner_radius=4,
                    text_color="#A7F3D0"
                )
                badge.pack(side="right")
            elif g["days_left"] is not None:
                badge = ctk.CTkLabel(
                    top,
                    text=f" {g['days_left']} days left ",
                    font=ctk.CTkFont(size=10),
                    fg_color="#334155",
                    corner_radius=4,
                    text_color="#94A3B8"
                )
                badge.pack(side="right")

            # Monetary Details
            mid = ctk.CTkFrame(card, fg_color="transparent")
            mid.pack(fill="x", padx=14, pady=(0, 6))

            ctk.CTkLabel(
                mid,
                text=f"Saved: {self.settings_svc.format_currency(g['current_amount'])}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#10B981"
            ).pack(side="left")

            ctk.CTkLabel(
                mid,
                text=f"Target: {self.settings_svc.format_currency(g['target_amount'])}",
                font=ctk.CTkFont(size=12),
                text_color="#94A3B8"
            ).pack(side="right")

            # Progress Bar
            prog = ctk.CTkProgressBar(card, height=10, corner_radius=5, progress_color="#10B981")
            prog.pack(fill="x", padx=14, pady=(0, 6))
            prog.set(g["percentage_completed"] / 100.0)

            # Footer: Remaining amount + Action buttons
            foot = ctk.CTkFrame(card, fg_color="transparent")
            foot.pack(fill="x", padx=14, pady=(0, 10))

            ctk.CTkLabel(
                foot,
                text=f"{g['percentage_completed']:.1f}% saved • {self.settings_svc.format_currency(g['remaining_amount'])} to go",
                font=ctk.CTkFont(size=11),
                text_color="#94A3B8"
            ).pack(side="left")

            act_box = ctk.CTkFrame(foot, fg_color="transparent")
            act_box.pack(side="right")

            ctk.CTkButton(
                act_box,
                text="+ Deposit",
                width=75,
                height=24,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#059669",
                hover_color="#047857",
                command=lambda gid=g["id"], gname=g["name"]: self._open_deposit_dialog(gid, gname)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                act_box,
                text="✕",
                width=24,
                height=24,
                font=ctk.CTkFont(size=11),
                fg_color="#334155",
                hover_color="#7F1D1D",
                command=lambda gid=g["id"]: self._delete_goal(gid)
            ).pack(side="left", padx=2)

    def _open_new_goal_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create Savings Goal")
        dialog.geometry("420x400")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color="#0F172A")

        ctk.CTkLabel(
            dialog,
            text="New Savings Goal",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=20, pady=(20, 12), anchor="w")

        ctk.CTkLabel(dialog, text="Goal Name *", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        name_entry = ctk.CTkEntry(dialog, placeholder_text="e.g. Goa Trip, MacBook Pro, Emergency Fund", height=36, fg_color="#1E293B", border_color="#334155")
        name_entry.pack(fill="x", padx=20, pady=(2, 8))

        sym = self.settings_svc.get_currency_symbol()
        ctk.CTkLabel(dialog, text=f"Target Amount ({sym}) *", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        target_entry = ctk.CTkEntry(dialog, placeholder_text="e.g. 50000", height=36, fg_color="#1E293B", border_color="#334155")
        target_entry.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(dialog, text=f"Initial Saved Amount ({sym})", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        init_entry = ctk.CTkEntry(dialog, placeholder_text="0.00", height=36, fg_color="#1E293B", border_color="#334155")
        init_entry.insert(0, "0.00")
        init_entry.pack(fill="x", padx=20, pady=(2, 8))

        ctk.CTkLabel(dialog, text="Target Completion Date (YYYY-MM-DD)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        date_entry = ctk.CTkEntry(dialog, placeholder_text="YYYY-MM-DD", height=36, fg_color="#1E293B", border_color="#334155")
        date_entry.pack(fill="x", padx=20, pady=(2, 16))

        def save():
            name = name_entry.get().strip()
            if not name:
                name_entry.configure(border_color="#EF4444")
                return

            try:
                target = float(target_entry.get().strip())
                if target <= 0:
                    raise ValueError
            except ValueError:
                target_entry.configure(border_color="#EF4444")
                return

            try:
                init_amt = float(init_entry.get().strip() or 0.0)
            except ValueError:
                init_amt = 0.0

            dt_str = date_entry.get().strip() or None

            self.goal_svc.create_goal(
                name=name,
                target_amount=target,
                current_amount=init_amt,
                target_date=dt_str,
                is_demo=0
            )
            dialog.destroy()
            show_toast(self, f"Created savings goal '{name}'!", "success")
            self.refresh()

        ctk.CTkButton(
            dialog,
            text="Create Goal",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            height=38,
            command=save
        ).pack(fill="x", padx=20, pady=(0, 20))

    def _open_deposit_dialog(self, goal_id: int, goal_name: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Deposit to {goal_name}")
        dialog.geometry("380x280")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color="#0F172A")

        ctk.CTkLabel(
            dialog,
            text=f"Log Savings Contribution",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#F8FAFC"
        ).pack(padx=20, pady=(20, 4), anchor="w")

        ctk.CTkLabel(
            dialog,
            text=f"Goal: {goal_name}",
            font=ctk.CTkFont(size=12),
            text_color="#60A5FA"
        ).pack(padx=20, pady=(0, 12), anchor="w")

        sym = self.settings_svc.get_currency_symbol()
        ctk.CTkLabel(dialog, text=f"Deposit Amount ({sym}) *", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        amt_entry = ctk.CTkEntry(dialog, placeholder_text="e.g. 5000", height=36, fg_color="#1E293B", border_color="#334155")
        amt_entry.pack(fill="x", padx=20, pady=(2, 10))

        ctk.CTkLabel(dialog, text="Note (Optional)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#94A3B8").pack(padx=20, anchor="w")
        note_entry = ctk.CTkEntry(dialog, placeholder_text="e.g. Monthly salary savings", height=36, fg_color="#1E293B", border_color="#334155")
        note_entry.pack(fill="x", padx=20, pady=(2, 16))

        def deposit():
            try:
                amt = float(amt_entry.get().strip())
                if amt <= 0:
                    raise ValueError
            except ValueError:
                amt_entry.configure(border_color="#EF4444")
                return

            self.goal_svc.add_contribution(
                goal_id=goal_id,
                amount=amt,
                notes=note_entry.get().strip()
            )
            dialog.destroy()
            show_toast(self, f"Saved {sym}{amt:,.2f} towards '{goal_name}'!", "success")
            self.refresh()

        ctk.CTkButton(
            dialog,
            text="Confirm Deposit",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=38,
            command=deposit
        ).pack(fill="x", padx=20, pady=(0, 20))

    def _delete_goal(self, goal_id: int):
        if messagebox.askyesno("Confirm Removal", "Delete this savings goal and its deposit logs?"):
            self.goal_svc.delete_goal(goal_id)
            show_toast(self, "Savings goal deleted.", "info")
            self.refresh()
