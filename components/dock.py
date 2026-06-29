"""
Dock — Bottom global interaction bar with input and utility icons.
"""

import customtkinter as ctk
from theme import Colors, Fonts, Dims


class Dock(ctk.CTkFrame):
    """Full-width translucent glass input bar at the bottom of the app."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=Colors.BG_DOCK,
            height=Dims.DOCK_HEIGHT,
            corner_radius=0,
            border_width=0,
            **kwargs
        )
        self.pack_propagate(False)

        self._build()

    def _build(self):
        # Inner container with glass styling
        inner = ctk.CTkFrame(
            self, fg_color=Colors.CARD_BG,
            corner_radius=14, border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            height=44
        )
        inner.pack(fill="x", padx=16, pady=6)
        inner.pack_propagate(False)

        # Text input field
        self.entry = ctk.CTkEntry(
            inner,
            placeholder_text="Ask FLOWSPACE anything...",
            placeholder_text_color=Colors.TEXT_DIM,
            font=Fonts.BODY,
            fg_color="transparent",
            border_width=0,
            text_color=Colors.TEXT_PRIMARY,
            height=36
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(14, 8))

        # Right-side utility icons
        icons_frame = ctk.CTkFrame(inner, fg_color="transparent")
        icons_frame.pack(side="right", padx=(0, 8))

        # Microphone
        self._make_icon_btn(icons_frame, "🎤")
        # Attachment
        self._make_icon_btn(icons_frame, "📎")
        # Camera
        self._make_icon_btn(icons_frame, "📷")

        # Separator dot
        ctk.CTkLabel(
            icons_frame, text="·",
            font=("Segoe UI", 16), text_color=Colors.TEXT_DIM,
            fg_color="transparent", width=8
        ).pack(side="left", padx=2)

        # Send button (purple action button)
        send_btn = ctk.CTkButton(
            icons_frame,
            text="➤",
            font=("Segoe UI", 16, "bold"),
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            width=Dims.DOCK_BTN_SIZE, height=Dims.DOCK_BTN_SIZE - 4,
            corner_radius=10
        )
        send_btn.pack(side="left", padx=(4, 0))

    def _make_icon_btn(self, parent, icon: str):
        """Create a small transparent icon button."""
        btn = ctk.CTkButton(
            parent,
            text=icon, font=("Segoe UI", 14),
            fg_color="transparent",
            hover_color=Colors.CARD_HOVER,
            text_color=Colors.TEXT_SECONDARY,
            width=32, height=32, corner_radius=8
        )
        btn.pack(side="left", padx=2)
        return btn
