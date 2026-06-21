"""
DashboardView — Main 6-card responsive grid dashboard.
"""

import customtkinter as ctk
from theme import Colors, Fonts, Dims
from components.glass_card import GlassCard
from components.donut_chart import DonutChart
from components.line_chart import LineChart
from components.bar_chart import BarChart
from components.schedule_list import ScheduleList
from components.task_list import TaskList
from components.suggestions import SuggestionsCard


class DashboardView(ctk.CTkFrame):
    """
    Full dashboard content area with welcome header,
    quick-action pills, and a 3×2 responsive card grid.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Scrollable container for the dashboard content
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.GLASS_FILL_LIGHT,
            scrollbar_button_hover_color=Colors.GLASS_FILL_HOVER,
        )
        self.scroll.pack(fill="both", expand=True)

        self._build_header()
        self._build_pills()
        self._build_grid()

    def _build_header(self):
        """Welcome header with greeting and subtitle."""
        header = ctk.CTkFrame(self.scroll, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="Welcome back, Michael! 👋",
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

        ctk.CTkLabel(
            header, text="Let's make today productive.",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

    def _build_pills(self):
        """Quick action pill buttons row."""
        pills_frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=40)
        pills_frame.pack(fill="x", padx=4, pady=(8, 12))
        pills_frame.pack_propagate(False)

        pills = [
            ("🤖", "AI Assistant"),
            ("📋", "Planner"),
            ("📥", "Import"),
            ("🎙️", "Voice Input"),
        ]

        for icon, label in pills:
            pill = ctk.CTkButton(
                pills_frame,
                text=f"{icon}  {label}",
                font=Fonts.SMALL,
                fg_color=Colors.GLASS_FILL,
                hover_color=Colors.GLASS_FILL_HOVER,
                text_color=Colors.TEXT_SECONDARY,
                border_width=1, border_color=Colors.GLASS_BORDER,
                corner_radius=Dims.PILL_CORNER,
                height=Dims.PILL_HEIGHT,
                width=120,
            )
            pill.pack(side="left", padx=(0, 8))

    def _build_grid(self):
        """Build the 3×2 card grid layout."""
        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        # Configure 2 columns with equal weight
        grid.columnconfigure(0, weight=1, minsize=280)
        grid.columnconfigure(1, weight=2, minsize=350)

        # Configure 3 rows with equal weight
        grid.rowconfigure(0, weight=1, minsize=220)
        grid.rowconfigure(1, weight=1, minsize=220)
        grid.rowconfigure(2, weight=1, minsize=220)

        pad = 6

        # ── Row 0, Col 0: AI Reports (Donut Chart) ─────────────────────
        card1 = GlassCard(grid, title="AI Reports", action_text="See All")
        card1.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)
        DonutChart(card1.content).pack(fill="both", expand=True)

        # ── Row 0, Col 1: Productivity Overview (Line Chart) ────────────
        card2 = GlassCard(grid, title="Productivity Overview", action_text="Details")
        card2.grid(row=0, column=1, sticky="nsew", padx=pad, pady=pad)
        LineChart(card2.content).pack(fill="both", expand=True)

        # ── Row 1, Col 0: Project Time (Bar Chart) ─────────────────────
        card3 = GlassCard(grid, title="Project Time", action_text="Full Report")
        card3.grid(row=1, column=0, sticky="nsew", padx=pad, pady=pad)
        BarChart(card3.content).pack(fill="both", expand=True)

        # ── Row 1, Col 1: Today's Schedule ──────────────────────────────
        card4 = GlassCard(grid, title="Today's Schedule", action_text="View All")
        card4.grid(row=1, column=1, sticky="nsew", padx=pad, pady=pad)
        ScheduleList(card4.content).pack(fill="both", expand=True)

        # ── Row 2, Col 0: Upcoming Tasks ────────────────────────────────
        card5 = GlassCard(grid, title="Upcoming Tasks", action_text="Manage")
        card5.grid(row=2, column=0, sticky="nsew", padx=pad, pady=pad)
        TaskList(card5.content).pack(fill="both", expand=True)

        # ── Row 2, Col 1: AI Suggestions ────────────────────────────────
        card6 = GlassCard(grid, title="AI Suggestions", action_text="See All")
        card6.grid(row=2, column=1, sticky="nsew", padx=pad, pady=pad)
        SuggestionsCard(card6.content).pack(fill="both", expand=True)
