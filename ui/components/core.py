import customtkinter as ctk
from theme import Colors, Fonts, Dims, blend_color
from utils.animations import apply_hover_animation

class PrimaryButton(ctk.CTkButton):
    """Modern primary action button with hover glow."""
    def __init__(self, parent, text, command=None, **kwargs):
        super().__init__(
            parent,
            text=text,
            font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Dims.RADIUS_BUTTON,
            height=Dims.BTN_HEIGHT,
            border_width=1,
            border_color=Colors.ACCENT_PRIMARY,
            command=command,
            **kwargs
        )
        # Smooth hover for border glow effect
        apply_hover_animation(self, 'border_color', Colors.ACCENT_PRIMARY, Colors.ACCENT_PRESSED)

class SecondaryButton(ctk.CTkButton):
    """Glass-style secondary button with subtle border highlight on hover."""
    def __init__(self, parent, text, command=None, **kwargs):
        super().__init__(
            parent,
            text=text,
            font=Fonts.BUTTON,
            fg_color=blend_color(Colors.TEXT_PRIMARY, 0.05, Colors.BG_PRIMARY),
            hover_color=blend_color(Colors.TEXT_PRIMARY, 0.1, Colors.BG_PRIMARY),
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Dims.RADIUS_BUTTON,
            height=Dims.BTN_HEIGHT,
            command=command,
            **kwargs
        )
        # Smooth border animation on hover
        apply_hover_animation(self, 'border_color', Colors.BORDER_SUBTLE, Colors.TEXT_SECONDARY)

class DangerButton(ctk.CTkButton):
    """Button for destructive actions."""
    def __init__(self, parent, text, command=None, **kwargs):
        super().__init__(
            parent,
            text=text,
            font=Fonts.BUTTON,
            fg_color=blend_color(Colors.ERROR, 0.1, Colors.BG_PRIMARY),
            hover_color=Colors.ERROR,
            text_color=Colors.ERROR, # text turns white on hover usually, but custom tk handles this poorly
            corner_radius=Dims.RADIUS_BUTTON,
            height=Dims.BTN_HEIGHT,
            command=command,
            **kwargs
        )
        self.bind("<Enter>", lambda e: self.configure(text_color=Colors.TEXT_PRIMARY))
        self.bind("<Leave>", lambda e: self.configure(text_color=Colors.ERROR))



class GlassEntry(ctk.CTkEntry):
    """Modern input field with focus glow."""
    def __init__(self, parent, placeholder_text="", **kwargs):
        super().__init__(
            parent,
            placeholder_text=placeholder_text,
            font=Fonts.BODY,
            fg_color=Colors.INPUT_BG,
            border_color=Colors.INPUT_BORDER,
            border_width=1,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            corner_radius=Dims.RADIUS_INPUT,
            height=Dims.INPUT_HEIGHT,
            **kwargs
        )
        self.bind("<FocusIn>", lambda e: self.configure(border_color=Colors.INPUT_FOCUS, fg_color=blend_color(Colors.INPUT_FOCUS, 0.05, Colors.INPUT_BG)))
        self.bind("<FocusOut>", lambda e: self.configure(border_color=Colors.INPUT_BORDER, fg_color=Colors.INPUT_BG))

class StatusBadge(ctk.CTkFrame):
    """Small pill-shaped badge for status indicators."""
    def __init__(self, parent, text, color, **kwargs):
        super().__init__(
            parent,
            fg_color=blend_color(color, 0.15, Colors.BG_SECONDARY),
            corner_radius=Dims.RADIUS_PILL,
            height=24,
            **kwargs
        )
        self.pack_propagate(False)
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=Fonts.CAPTION,
            text_color=color
        )
        self.label.pack(expand=True, padx=12, pady=2)
