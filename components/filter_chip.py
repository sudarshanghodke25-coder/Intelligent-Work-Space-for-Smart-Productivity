import customtkinter as ctk
from theme import Colors, Fonts, Dims

class FilterChip(ctk.CTkButton):
    def __init__(self, parent, text, command=None, is_active=False, **kwargs):
        fg_color = Colors.GLASS_FILL_HOVER if is_active else "transparent"
        
        super().__init__(
            parent,
            text=text,
            font=Fonts.SMALL_BOLD,
            fg_color=fg_color,
            hover_color=Colors.GLASS_FILL_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            border_width=1,
            border_color=Colors.GLASS_BORDER,
            corner_radius=Dims.PILL_CORNER,
            height=Dims.PILL_HEIGHT,
            command=command,
            **kwargs
        )
        self.is_active = is_active
        
    def set_active(self, active: bool):
        self.is_active = active
        self.configure(fg_color=Colors.GLASS_FILL_HOVER if active else "transparent")
