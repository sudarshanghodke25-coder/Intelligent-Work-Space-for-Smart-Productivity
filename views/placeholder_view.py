"""
PlaceholderView — Generic "Welcome to [Page]" placeholder for non-dashboard pages.
"""

import customtkinter as ctk
from theme import Colors, Fonts


class PlaceholderView(ctk.CTkFrame):
    """Displays a centered placeholder message for a named page."""

    def __init__(self, parent, page_name: str = "Unknown", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Glass container
        card = ctk.CTkFrame(
            self,
            fg_color=Colors.GLASS_FILL,
            corner_radius=20,
            border_width=1,
            border_color=Colors.GLASS_BORDER,
            width=500,
            height=280,
        )
        card.grid(row=0, column=0)
        card.grid_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        # Page icon
        icon_map = {
            "AI Assistant": "🤖",
            "AI Planner": "📋",
            "Task Manager": "✅",
            "Notes & Docs": "📝",
            "Calendar": "📅",
            "Analytics": "📈",
            "History": "🕐",
            "Focus Mode": "🎯",
            "Goal Tracker": "🏆",
            "Pomodoro Timer": "⏱️",
            "Habit Tracker": "🔄",
        }
        icon = icon_map.get(page_name, "🚀")

        ctk.CTkLabel(
            inner, text=icon,
            font=("Segoe UI", 48), text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent"
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            inner, text=f"Welcome to {page_name}",
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent"
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            inner, text="This section is coming soon.",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY,
            fg_color="transparent"
        ).pack(pady=(0, 16))

        # Subtle "Go Back" hint
        back_label = ctk.CTkLabel(
            inner, text="← Return to Dashboard",
            font=Fonts.SMALL, text_color=Colors.ACCENT_GLOW,
            fg_color="transparent", cursor="hand2"
        )
        back_label.pack()
