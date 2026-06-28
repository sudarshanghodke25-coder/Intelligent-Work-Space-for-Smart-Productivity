"""
GlassCard — Reusable glassmorphism container frame.
"""

import customtkinter as ctk
from theme import Colors, Fonts, Dims


class GlassCard(ctk.CTkFrame):
    """
    A semi-transparent card with thin reflective border.
    Simulates glassmorphism in CustomTkinter.
    """

    def __init__(
        self,
        parent,
        title: str = "",
        action_text: str = "",
        action_command=None,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=Colors.CARD_BG,
            corner_radius=Dims.RADIUS_CARD,
            border_width=Dims.CARD_BORDER,
            border_color=Colors.BORDER_SUBTLE,
            **kwargs
        )

        self._title = title
        self._action_text = action_text

        # ── Header row (title + action link) ────────────────────────────
        if title or action_text:
            header = ctk.CTkFrame(self, fg_color="transparent", height=30)
            header.pack(fill="x", padx=Dims.CARD_PAD, pady=(Dims.CARD_PAD, 4))
            header.pack_propagate(False)

            if title:
                ctk.CTkLabel(
                    header,
                    text=title,
                    font=Fonts.SUBHEADING,
                    text_color=Colors.TEXT_PRIMARY,
                    anchor="w"
                ).pack(side="left")

            if action_text:
                action_btn = ctk.CTkLabel(
                    header,
                    text=action_text,
                    font=Fonts.SMALL,
                    text_color=Colors.ACCENT_PRIMARY,
                    cursor="hand2",
                    anchor="e"
                )
                action_btn.pack(side="right")
                if action_command:
                    action_btn.bind("<Button-1>", lambda e: action_command())

        # ── Content area ────────────────────────────────────────────────
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=Dims.CARD_PAD, pady=(0, Dims.CARD_PAD))
