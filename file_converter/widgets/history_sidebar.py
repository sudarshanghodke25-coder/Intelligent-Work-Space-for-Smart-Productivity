"""
file_converter/widgets/history_sidebar.py
Sidebar panel showing recent conversion history and storage used.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List

import customtkinter as ctk
from services.event_bus import bus
from theme import Colors, Fonts

from file_converter.events.converter_events import ConverterEvents
from file_converter.models.conversion_history import HistoryEntry, ConverterStats
from file_converter.constants.formats import get_format


class HistoryEntryRow(ctk.CTkFrame):
    """Single row in the recent conversions list."""

    def __init__(
        self,
        parent,
        entry: HistoryEntry,
        on_open: Callable[[str], None] = None,
        on_open_folder: Callable[[str], None] = None,
        on_delete: Callable[[int], None] = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._entry = entry
        self._on_open = on_open
        self._build()

        self.bind("<Enter>", lambda _: self.configure(fg_color=Colors.CARD_HOVER))
        self.bind("<Leave>", lambda _: self.configure(fg_color="transparent"))

    def _build(self):
        # File type icon box
        fmt = get_format(self._entry.source_ext)
        icon = fmt.icon if fmt else "📁"
        icon_box = ctk.CTkFrame(self, fg_color=Colors.CARD_FLOATING, corner_radius=6, width=32, height=32)
        icon_box.pack(side="left", padx=(4, 10), pady=8)
        icon_box.pack_propagate(False)
        ctk.CTkLabel(
            icon_box, text=icon, font=("Segoe UI", 16), text_color=Colors.ACCENT_PRIMARY, fg_color="transparent"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Info block (Name + Conversion Arrow + Size)
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=8)

        name = self._entry.source_name
        if len(name) > 22:
            name = name[:19] + "…"
        ctk.CTkLabel(
            info, text=name, font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w", fg_color="transparent"
        ).pack(fill="x")

        details_row = ctk.CTkFrame(info, fg_color="transparent")
        details_row.pack(fill="x", pady=(2, 0))
        
        ctk.CTkLabel(
            details_row, text="→ " + self._entry.target_ext.upper().lstrip("."),
            font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED, fg_color="transparent"
        ).pack(side="left", padx=(0, 12))
        
        ctk.CTkLabel(
            details_row, text=self._entry.source_size_human,
            font=Fonts.CAPTION, text_color=Colors.TEXT_DIM, fg_color="transparent"
        ).pack(side="left")

        # Status and Download icon
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="right", padx=(0, 8))

        if self._entry.status == "COMPLETED":
            ctk.CTkLabel(
                right_frame, text="Completed", font=Fonts.CAPTION, text_color=Colors.SUCCESS, fg_color="transparent"
            ).pack(side="left", padx=(0, 10))
            
            if Path(self._entry.output_path).exists():
                dl_btn = ctk.CTkButton(
                    right_frame, text="↓", font=("Segoe UI", 14), width=28, height=28, corner_radius=6,
                    fg_color="transparent", hover_color=Colors.CARD_HOVER, text_color=Colors.TEXT_SECONDARY,
                    border_width=1, border_color=Colors.BORDER_SUBTLE,
                    command=lambda: self._on_open and self._on_open(self._entry.output_path)
                )
                dl_btn.pack(side="left")
        elif self._entry.status == "FAILED":
            ctk.CTkLabel(
                right_frame, text="Failed", font=Fonts.CAPTION, text_color=Colors.ERROR, fg_color="transparent"
            ).pack(side="left", padx=(0, 10))
        else:
            ctk.CTkLabel(
                right_frame, text=self._entry.status.capitalize(), font=Fonts.CAPTION, text_color=Colors.TEXT_DIM, fg_color="transparent"
            ).pack(side="left", padx=(0, 10))


from utils.ui_helpers import destroy_tracked


class HistorySidebar(ctk.CTkFrame):
    """
    Sidebar showing recent conversion history and storage.
    """

    def __init__(
        self,
        parent,
        on_open_file: Callable[[str], None] = None,
        on_open_folder: Callable[[str], None] = None,
        on_delete_entry: Callable[[int], None] = None,
        on_clear_all: Callable[[], None] = None,
        on_refresh: Callable[[str, str], List[HistoryEntry]] = None,
        on_get_stats: Callable[[], ConverterStats] = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_open_file = on_open_file
        self._on_clear_all = on_clear_all
        self._on_refresh = on_refresh
        self._on_get_stats = on_get_stats
        self._history_widgets = []

        self._build()
        self._subscribe()
        self._load_history()

    def _build(self):
        # ── History Header ────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent", height=32)
        header.pack(fill="x", pady=(0, 12))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="🕒 Conversion History", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w", fg_color="transparent"
        ).pack(side="left")
        
        ctk.CTkButton(
            header, text="Clear All", font=Fonts.CAPTION, text_color=Colors.ACCENT_PRIMARY,
            fg_color="transparent", hover_color=Colors.CARD_HOVER, width=50, height=20, corner_radius=4, command=self._on_clear_all_click
        ).pack(side="right")

        # ── Scrollable List ──────────────────────────────────────────────
        self._history_list = ctk.CTkScrollableFrame(
            self, fg_color=Colors.CARD_BG, corner_radius=12, border_width=1, border_color=Colors.BORDER_SUBTLE,
            scrollbar_button_color=Colors.CARD_FLOATING,
        )
        self._history_list.pack(fill="both", expand=True, pady=(0, 20))


    def _subscribe(self):
        bus.subscribe(ConverterEvents.HISTORY_UPDATED, lambda _: self._load_history())

    def _on_clear_all_click(self):
        if self._on_clear_all:
            self._on_clear_all()

    def _load_history(self):
        entries: List[HistoryEntry] = []
        if self._on_refresh:
            entries = self._on_refresh("All", "")

        destroy_tracked(self._history_widgets)

        if not entries:
            lbl = ctk.CTkLabel(
                self._history_list, text="No conversions yet.", font=Fonts.SMALL, text_color=Colors.TEXT_DIM, fg_color="transparent"
            )
            lbl.pack(pady=20)
            self._history_widgets.append(lbl)
        else:
            for i, entry in enumerate(entries[:10]):
                row = HistoryEntryRow(self._history_list, entry=entry, on_open=self._on_open_file)
                row.pack(fill="x")
                self._history_widgets.append(row)
                if i < len(entries[:10]) - 1:
                    sep = ctk.CTkFrame(self._history_list, fg_color=Colors.BORDER_SUBTLE, height=1)
                    sep.pack(fill="x", padx=10)
                    self._history_widgets.append(sep)
