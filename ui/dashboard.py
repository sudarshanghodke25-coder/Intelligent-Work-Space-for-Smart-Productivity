import customtkinter as ctk
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.GLASS_FILL_LIGHT,
            scrollbar_button_hover_color=Colors.GLASS_FILL_HOVER,
        )
        self.scroll.pack(fill="both", expand=True)

        self._build_header()
        self._build_status_panel()

    def _build_header(self):
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", padx=4, pady=(20, 10))
        
        ctk.CTkLabel(
            header, text="AUREX Intelligence Center",
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

        ctk.CTkLabel(
            header, text="Dashboard will become available after core systems are connected.",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

    def _build_status_panel(self):
        panel = GlassCard(self.scroll, title="Core Systems Status")
        panel.pack(fill="both", expand=True, padx=4, pady=10)
        
        statuses = [
            ("Task Manager", "Implemented", Colors.CHART_GREEN),
            ("Summarizer", "Implemented", Colors.CHART_GREEN),
            ("AI Planner", "In Progress", Colors.CHART_BLUE),
            ("Focus Mode", "In Progress", Colors.CHART_BLUE),
            ("Goal Tracker", "In Progress", Colors.CHART_BLUE),
            ("Pomodoro", "In Progress", Colors.CHART_BLUE),
            ("Calendar", "Not Connected", Colors.TEXT_MUTED),
            ("Habit Tracker", "Not Connected", Colors.TEXT_MUTED),
        ]
        
        for name, status_text, color in statuses:
            row = ctk.CTkFrame(panel.content, fg_color="transparent")
            row.pack(fill="x", pady=8)
            
            ctk.CTkLabel(row, text=name, font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left")
            
            status_badge = ctk.CTkFrame(row, fg_color=color, corner_radius=6, width=120, height=24)
            status_badge.pack(side="right")
            status_badge.pack_propagate(False)
            
            # Simple text color contrast calculation (White text for colored badges)
            text_col = "white" if status_text != "Not Connected" else Colors.TEXT_PRIMARY
            ctk.CTkLabel(status_badge, text=status_text, font=Fonts.SMALL_BOLD, text_color=text_col).pack(expand=True)
