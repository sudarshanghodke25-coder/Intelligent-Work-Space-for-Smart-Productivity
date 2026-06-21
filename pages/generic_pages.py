import customtkinter as ctk
from theme import Colors, Fonts
from ui.glass_card import GlassCard

class BasePageView(ctk.CTkFrame):
    """Generic base class for page frames."""
    def __init__(self, parent, page_name, icon, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)

        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        ctk.CTkLabel(header, text=f"{icon} {page_name}", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(side="left", fill="x")

        card = GlassCard(self, title=f"{page_name} Overview")
        card.pack(fill="both", expand=True, padx=4, pady=10)
        
        ctk.CTkLabel(card.content, text=f"Welcome to the {page_name} module.\nThis feature is currently under active development.", font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY).pack(expand=True)



class NotesView(BasePageView):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, "Notes & Docs", "📝", **kwargs)

class CalendarView(BasePageView):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, "Calendar", "📅", **kwargs)

class AnalyticsView(BasePageView):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, "Analytics", "📈", **kwargs)
