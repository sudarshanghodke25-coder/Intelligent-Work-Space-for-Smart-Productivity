"""
file_converter/widgets/toast_notification.py
Lightweight toast notification overlay.
Appears at the bottom-right of the content area, auto-dismisses after 3s.
"""

from __future__ import annotations

import customtkinter as ctk
from theme import Colors, Fonts
from services.event_bus import bus
from file_converter.events.converter_events import ConverterEvents


class ToastNotification(ctk.CTkFrame):
    """Single toast popup — auto-destroys itself after timeout."""

    def __init__(
        self,
        parent,
        message: str,
        kind: str = "info",   # "success" | "error" | "info"
        duration_ms: int = 3500,
    ):
        colors = {
            "success": (Colors.SUCCESS, "✓"),
            "error":   (Colors.ERROR,   "✗"),
            "info":    (Colors.INFO,    "ℹ"),
        }
        bg_color, icon = colors.get(kind, (Colors.INFO, "ℹ"))

        super().__init__(
            parent,
            fg_color=Colors.GLASS_FILL,
            corner_radius=12,
            border_width=1,
            border_color=bg_color,
        )

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=14, pady=10)

        ctk.CTkLabel(
            inner, text=icon,
            font=("Segoe UI", 15),
            text_color=bg_color,
            fg_color="transparent",
        ).pack(side="left", padx=(0, 8))

        msg = message[:80] + ("…" if len(message) > 80 else "")
        ctk.CTkLabel(
            inner, text=msg,
            font=Fonts.SMALL,
            text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent",
            wraplength=260,
        ).pack(side="left")

        self.after(duration_ms, self._dismiss)

    def _dismiss(self):
        try:
            self.destroy()
        except Exception:
            pass


class ToastManager:
    """
    Manages a stack of toast notifications anchored to a parent container.
    Subscribes to FC_NOTIFY_* events automatically.
    """

    def __init__(self, parent: ctk.CTkFrame):
        self._parent = parent
        self._toasts: list[ToastNotification] = []

        bus.subscribe(ConverterEvents.NOTIFY_SUCCESS,
                      lambda msg: self._show(msg, "success"))
        bus.subscribe(ConverterEvents.NOTIFY_ERROR,
                      lambda msg: self._show(msg, "error"))
        bus.subscribe(ConverterEvents.NOTIFY_INFO,
                      lambda msg: self._show(msg, "info"))

    def _show(self, message: str, kind: str) -> None:
        if not message:
            return
        toast = ToastNotification(self._parent, message=message, kind=kind)
        # Stack toasts from bottom
        offset = 16 + sum(60 for t in self._toasts if t.winfo_exists())
        toast.place(relx=1.0, rely=1.0, anchor="se", x=-16, y=-(offset))
        self._toasts.append(toast)
        # Clean up destroyed toasts
        self._toasts = [t for t in self._toasts if t.winfo_exists()]
