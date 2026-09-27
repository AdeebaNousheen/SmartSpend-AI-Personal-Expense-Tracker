"""
SmartSpend - Component: Toast Notification
Displays auto-dismissing feedback messages for user actions.
"""

from typing import Optional
import customtkinter as ctk


class Toast(ctk.CTkFrame):
    """Floating notification toast message."""

    def __init__(
        self,
        master,
        message: str,
        toast_type: str = "success",
        duration_ms: int = 3000,
        **kwargs
    ):
        color_map = {
            "success": ("#065F46", "#10B981", "✓"),
            "error": ("#991B1B", "#EF4444", "✗"),
            "warning": ("#92400E", "#F59E0B", "⚠"),
            "info": ("#1E40AF", "#3B82F6", "ℹ"),
        }
        bg_col, border_col, icon = color_map.get(toast_type, color_map["info"])

        super().__init__(
            master,
            corner_radius=8,
            fg_color=bg_col,
            border_width=1,
            border_color=border_col,
            **kwargs
        )

        self.label = ctk.CTkLabel(
            self,
            text=f"{icon}  {message}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FFFFFF"
        )
        self.label.pack(padx=16, pady=8)

        # Place toast at bottom right of master
        self.place(relx=0.98, rely=0.96, anchor="se")

        # Auto-dismiss timer
        self.after(duration_ms, self.dismiss)

    def dismiss(self):
        """Fade out or destroy toast."""
        try:
            self.destroy()
        except Exception:
            pass


def show_toast(master, message: str, toast_type: str = "success", duration_ms: int = 3000):
    """Helper function to summon toast on any frame/window."""
    return Toast(master, message, toast_type=toast_type, duration_ms=duration_ms)
