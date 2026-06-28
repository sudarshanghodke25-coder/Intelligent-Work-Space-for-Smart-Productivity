"""
file_converter/widgets/animated_button.py
Premium animated button with gradient glow, hover elevation, and pulse effect.
Reusable across the entire File Converter module.
"""


import math
import customtkinter as ctk
from theme import Colors, Dims


class AnimatedGlowButton(ctk.CTkFrame):
    """
    A large, gradient animated 'Convert Now' style button.
    Renders a glow pulse animation when idle and a progress shimmer
    when the conversion is running.
    """

    def __init__(
        self,
        parent,
        text: str = "Convert Now",
        command=None,
        width: int = 300,
        height: int = 56,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color="transparent",
            width=width,
            height=height,
            **kwargs,
        )
        self.pack_propagate(False)

        self._command = command
        self._is_pulsing = False
        self._pulse_step = 0
        self._pulse_after_id = None
        self._enabled = True

        # ── Button frame (acts as the colored background) ─────────────────
        self._btn_frame = ctk.CTkFrame(
            self,
            fg_color=Colors.ACCENT_PRIMARY,
            corner_radius=Dims.BTN_CORNER + 4,
            border_width=0,
        )
        self._btn_frame.pack(fill="both", expand=True)
        self._btn_frame.pack_propagate(False)

        # ── Icon + text row ────────────────────────────────────────────────
        inner = ctk.CTkFrame(self._btn_frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        self._icon_lbl = ctk.CTkLabel(
            inner, text="⚡",
            font=("Segoe UI", 18),
            text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent",
        )
        self._icon_lbl.pack(side="left", padx=(0, 8))

        self._text_lbl = ctk.CTkLabel(
            inner, text=text,
            font=("Segoe UI", 15, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent",
        )
        self._text_lbl.pack(side="left")

        # ── Bind hover + click ─────────────────────────────────────────────
        for w in [self, self._btn_frame, inner, self._icon_lbl, self._text_lbl]:
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_click)
            w.configure(cursor="hand2")

        self._start_pulse()

    # ── Hover effects ──────────────────────────────────────────────────────

    def _on_enter(self, _=None):
        if self._enabled:
            self._btn_frame.configure(fg_color=Colors.ACCENT_HOVER)

    def _on_leave(self, _=None):
        if self._enabled:
            self._btn_frame.configure(fg_color=Colors.ACCENT_PRIMARY)

    def _on_click(self, _=None):
        if self._enabled and self._command:
            self._command()

    # ── Pulse animation (gentle opacity oscillation via color blending) ────

    def _start_pulse(self):
        self._is_pulsing = True
        self._animate_pulse()

    def _animate_pulse(self):
        if not self._is_pulsing:
            return
        # Oscillate between ACCENT_PRIMARY and ACCENT_GLOW
        t = (math.sin(self._pulse_step * 0.08) + 1) / 2  # 0.0 – 1.0
        r1, g1, b1 = 0x7c, 0x3a, 0xed  # ACCENT_PRIMARY
        r2, g2, b2 = 0xa8, 0x55, 0xf7  # ACCENT_GLOW
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        color = f"#{r:02x}{g:02x}{b:02x}"

        try:
            self._btn_frame.configure(fg_color=color)
        except Exception:
            return

        self._pulse_step += 1
        self._pulse_after_id = self.after(50, self._animate_pulse)

    def stop_pulse(self):
        self._is_pulsing = False
        if self._pulse_after_id:
            try:
                self.after_cancel(self._pulse_after_id)
            except Exception:
                pass

    def set_text(self, text: str, icon: str = "⚡") -> None:
        self._text_lbl.configure(text=text)
        self._icon_lbl.configure(text=icon)

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if enabled:
            self._btn_frame.configure(fg_color=Colors.ACCENT_PRIMARY)
            for w in [self._btn_frame, self._text_lbl, self._icon_lbl]:
                w.configure(cursor="hand2")
            self._start_pulse()
        else:
            self.stop_pulse()
            self._btn_frame.configure(fg_color=Colors.CARD_FLOATING)
            for w in [self._btn_frame, self._text_lbl, self._icon_lbl]:
                w.configure(cursor="arrow")


class HoverCard(ctk.CTkFrame):
    """
    Generic glassmorphic card with hover elevation effect.
    Used for quick-tool cards and file category badges.
    """

    def __init__(
        self,
        parent,
        fg_color: str = Colors.CARD_BG,
        hover_color: str = Colors.CARD_HOVER,
        corner_radius: int = 14,
        border_width: int = 1,
        border_color: str = Colors.BORDER_SUBTLE,
        on_click=None,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=fg_color,
            corner_radius=corner_radius,
            border_width=border_width,
            border_color=border_color,
            **kwargs,
        )
        self._base_color = fg_color
        self._hover_color = hover_color
        self._on_click = on_click

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._handle_click)
        if on_click:
            self.configure(cursor="hand2")

    def _on_enter(self, _=None):
        self.configure(fg_color=self._hover_color,
                       border_color=Colors.BORDER_HOVER)

    def _on_leave(self, _=None):
        self.configure(fg_color=self._base_color,
                       border_color=Colors.BORDER_SUBTLE)

    def _handle_click(self, _=None):
        if self._on_click:
            self._on_click()

    def bind_children(self, widget):
        """Propagate hover/click events from child widgets."""
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<Button-1>", self._handle_click)
        if self._on_click:
            widget.configure(cursor="hand2")
