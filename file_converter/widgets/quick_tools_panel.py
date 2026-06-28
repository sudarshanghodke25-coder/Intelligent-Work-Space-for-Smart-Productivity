"""
file_converter/widgets/quick_tools_panel.py
Sidebar grid of clickable quick-tool cards.
"""

from __future__ import annotations

from typing import Callable, List

import customtkinter as ctk
from theme import Colors, Fonts

from file_converter.constants.quick_tools import QUICK_TOOLS, QuickToolDef
from file_converter.widgets.animated_button import HoverCard


class QuickToolCard(HoverCard):
    """One compact quick-tool card (icon on left, text on right)."""

    def __init__(self, parent, tool: QuickToolDef, on_click: Callable, **kwargs):
        super().__init__(parent, on_click=lambda: on_click(tool.tool_id), height=46, **kwargs)

        self.pack_propagate(False)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=6)
        self.bind_children(inner)

        icon_part = tool.icon[:2] if len(tool.icon) >= 2 else tool.icon
        
        # Icon box
        icon_box = ctk.CTkFrame(inner, fg_color=Colors.CARD_FLOATING, corner_radius=6, width=28, height=28)
        icon_box.pack(side="left", padx=(0, 8))
        icon_box.pack_propagate(False)
        icon_lbl = ctk.CTkLabel(
            icon_box, text=icon_part, font=("Segoe UI", 14), text_color=Colors.ACCENT_PRIMARY, fg_color="transparent"
        )
        icon_lbl.place(relx=0.5, rely=0.5, anchor="center")
        self.bind_children(icon_box)
        self.bind_children(icon_lbl)

        # Name
        name_lbl = ctk.CTkLabel(
            inner, text=tool.label, font=("Segoe UI", 11, "bold"),
            text_color=Colors.TEXT_PRIMARY, fg_color="transparent", anchor="w"
        )
        name_lbl.pack(side="left", fill="x", expand=True)
        self.bind_children(name_lbl)


class QuickToolsPanel(ctk.CTkFrame):
    """
    Compact 2-column grid of quick-tool cards for the sidebar.
    """

    def __init__(
        self,
        parent,
        on_tool_click: Callable[[str], None] = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_tool_click = on_tool_click
        self._build()

    def _build(self):
        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent", height=32)
        header.pack(fill="x", pady=(0, 12))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="💡 Quick Tools", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w", fg_color="transparent"
        ).pack(side="left")
        
        ctk.CTkButton(
            header, text="View All", font=Fonts.CAPTION, text_color=Colors.ACCENT_PRIMARY,
            fg_color="transparent", hover_color=Colors.CARD_HOVER, width=50, height=20, corner_radius=4, command=lambda: None
        ).pack(side="right")

        # ── Grid ────────────────────────────────────────────
        self._grid = ctk.CTkFrame(self, fg_color="transparent")
        self._grid.pack(fill="x")
        self._grid.columnconfigure(0, weight=1, minsize=140)
        self._grid.columnconfigure(1, weight=1, minsize=140)

        self._render_tools(QUICK_TOOLS[:8])  # Top 8 tools

    def _render_tools(self, tools: List[QuickToolDef]) -> None:
        for w in self._grid.winfo_children():
            w.destroy()

        for i, tool in enumerate(tools):
            row, col = divmod(i, 2)
            card = QuickToolCard(self._grid, tool=tool, on_click=self._handle_tool_click)
            card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

    def _handle_tool_click(self, tool_id: str) -> None:
        if self._on_tool_click:
            self._on_tool_click(tool_id)
