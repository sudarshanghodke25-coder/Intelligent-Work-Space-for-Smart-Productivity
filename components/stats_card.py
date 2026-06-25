import customtkinter as ctk
from theme import Colors, Fonts

class StatsCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, **kwargs):
        super().__init__(parent, fg_color=Colors.GLASS_FILL_LIGHT, corner_radius=12, border_width=1, border_color=Colors.GLASS_BORDER, **kwargs)
        
        self.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(self, text=title, font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED)
        self.title_label.pack(side="top", pady=(10, 0), anchor="w", padx=15)
        
        self.value_label = ctk.CTkLabel(self, text=str(value), font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY)
        self.value_label.pack(side="top", pady=(0, 10), anchor="w", padx=15)
        
    def set_value(self, value):
        self.value_label.configure(text=str(value))
