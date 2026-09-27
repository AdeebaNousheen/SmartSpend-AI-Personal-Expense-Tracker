"""
SmartSpend - Component: StatCard
Reusable KPI metric card displaying title, formatted currency value, icon, and trend/status badge.
"""

from typing import Optional
import customtkinter as ctk
import config


class StatCard(ctk.CTkFrame):
    """Modern financial metric card with icon and trend subtitle."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        icon: str = "💳",
        subtitle: str = "",
        subtitle_color: Optional[str] = None,
        card_color: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=card_color or config.THEME_CONFIG["colors"]["card_bg_dark"],
            border_width=1,
            border_color=config.THEME_CONFIG["colors"]["border_dark"],
            **kwargs
        )

        self.grid_columnconfigure(1, weight=1)

        # Icon pill
        self.icon_frame = ctk.CTkFrame(
            self,
            width=44,
            height=44,
            corner_radius=10,
            fg_color="#334155"
        )
        self.icon_frame.grid(row=0, column=0, rowspan=2, padx=(14, 10), pady=14, sticky="w")
        self.icon_frame.grid_propagate(False)

        self.icon_label = ctk.CTkLabel(
            self.icon_frame,
            text=icon,
            font=ctk.CTkFont(size=20)
        )
        self.icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # Metric Title
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=12, weight="normal"),
            text_color="#94A3B8"
        )
        self.title_label.grid(row=0, column=1, padx=(0, 14), pady=(12, 0), sticky="w")

        # Metric Value
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        )
        self.value_label.grid(row=1, column=1, padx=(0, 14), pady=(0, 4), sticky="w")

        # Optional subtitle / trend note
        if subtitle:
            self.subtitle_label = ctk.CTkLabel(
                self,
                text=subtitle,
                font=ctk.CTkFont(size=11, weight="normal"),
                text_color=subtitle_color or "#10B981"
            )
            self.subtitle_label.grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 10), sticky="w")

    def update_value(self, new_value: str, new_subtitle: Optional[str] = None, subtitle_color: Optional[str] = None):
        """Updates the metric value and subtitle dynamically."""
        self.value_label.configure(text=new_value)
        if new_subtitle is not None and hasattr(self, "subtitle_label"):
            self.subtitle_label.configure(
                text=new_subtitle,
                text_color=subtitle_color or "#10B981"
            )
