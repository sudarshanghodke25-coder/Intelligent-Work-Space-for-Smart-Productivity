"""
SuggestionsCard — AI Suggestions widget with action buttons.
"""

import customtkinter as ctk
from theme import Colors, Fonts
from services.event_bus import bus

class SuggestionsCard(ctk.CTkFrame):
    """AI-generated suggestions with Start Now / Learn More actions."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        bus.subscribe("SUGGESTION_FIRED", self._on_suggestion)

        self.suggestions = [
            {
                "icon": "📊",
                "title": "Weekly Report Ready",
                "desc": "Your productivity increased 12% this week. View detailed analytics breakdown.",
                "action": "Learn More",
            }
        ]

        self._build()

    def _on_suggestion(self, data):
        # Prevent duplicates
        for s in self.suggestions:
            if s["title"] == data["title"]: return
            
        icon = "⚡" if data.get("type") == "warning" else "🧠"
        
        self.suggestions.insert(0, {
            "icon": icon,
            "title": data["title"],
            "desc": data["message"],
            "action": "View"
        })
        
        if len(self.suggestions) > 3:
            self.suggestions.pop()
            
        for widget in self.container.winfo_children():
            widget.destroy()
        self._build()

    def _build(self):
        for i, sug in enumerate(self.suggestions):
            item = ctk.CTkFrame(
                self.container, fg_color=Colors.GLASS_FILL_LIGHT,
                corner_radius=12, border_width=1,
                border_color=Colors.GLASS_BORDER
            )
            item.pack(fill="x", pady=4)

            # Top row: icon + title + action button
            top = ctk.CTkFrame(item, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10, 2))

            ctk.CTkLabel(
                top, text=sug["icon"],
                font=("Segoe UI", 18), text_color=Colors.TEXT_PRIMARY,
                width=28
            ).pack(side="left")

            ctk.CTkLabel(
                top, text=sug["title"],
                font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY,
                anchor="w"
            ).pack(side="left", padx=(6, 0), expand=True, fill="x")

            # Action button
            action_btn = ctk.CTkButton(
                top, text=sug["action"],
                font=Fonts.CAPTION,
                fg_color=Colors.ACCENT_PRIMARY,
                hover_color=Colors.ACCENT_HOVER,
                text_color=Colors.TEXT_PRIMARY,
                corner_radius=8, width=72, height=26
            )
            action_btn.pack(side="right")

            # Description
            ctk.CTkLabel(
                item, text=sug["desc"],
                font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY,
                anchor="w", wraplength=300, justify="left"
            ).pack(fill="x", padx=(46, 12), pady=(0, 10))
