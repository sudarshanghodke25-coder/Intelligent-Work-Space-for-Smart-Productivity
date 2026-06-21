import customtkinter as ctk
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from components.donut_chart import DonutChart
from components.line_chart import LineChart
from components.bar_chart import BarChart
from components.schedule_list import ScheduleList
from components.task_list import TaskList
from components.suggestions import SuggestionsCard
from authentication.session import current_session

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

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
        header = ctk.CTkFrame(self.scroll, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        header.pack_propagate(False)

        username = current_session.username or "Username"
        ctk.CTkLabel(
            header, text=f"Welcome back, {username} 👋",
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

        ctk.CTkLabel(
            header, text="Let's make today productive.",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

    def _build_pills(self):
        pills_frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=40)
        pills_frame.pack(fill="x", padx=4, pady=(8, 12))
        pills_frame.pack_propagate(False)

        app = self.winfo_toplevel()

        actions = [
            ("🤖", "Aurex AI", lambda: app.navigate("Aurex AI") if hasattr(app, "navigate") else None),
            ("📅", "Planner", lambda: app.navigate("AI Planner") if hasattr(app, "navigate") else None),
            ("📥", "Import", self._action_import),
            ("🎙️", "Voice Input", self._action_voice)
        ]

        for icon, label, cmd in actions:
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
                command=cmd
            )
            pill.pack(side="left", padx=(0, 8))

    def _action_import(self):
        filename = ctk.filedialog.askopenfilename(
            title="Import File",
            filetypes=[("Text files", "*.txt *.csv *.json"), ("All files", "*.*")]
        )
        if filename:
            from services.engine import ai_parse_text
            ai_parse_text(f"Imported content from {filename}")

    def _action_voice(self):
        from services.engine import ai_parse_text
        import threading
        def _listen():
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    # Normally would be: audio = recognizer.listen(source)
                    pass
            except Exception as e:
                print("Voice input simulated due to missing dependencies:", e)
            
            # Simulate Voice input being transcribed and sent to AI
            ai_parse_text("Simulated voice input: Please schedule a team sync tomorrow.")
            
        threading.Thread(target=_listen, daemon=True).start()

    def _build_grid(self):
        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        grid.columnconfigure(0, weight=1, minsize=280)
        grid.columnconfigure(1, weight=2, minsize=350)
        grid.rowconfigure(0, weight=1, minsize=220)
        grid.rowconfigure(1, weight=1, minsize=220)
        grid.rowconfigure(2, weight=1, minsize=220)

        pad = 6

        card1 = GlassCard(grid, title="AI Reports", action_text="See All")
        card1.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)
        DonutChart(card1.content).pack(fill="both", expand=True)

        card2 = GlassCard(grid, title="Productivity Overview", action_text="Details")
        card2.grid(row=0, column=1, sticky="nsew", padx=pad, pady=pad)
        LineChart(card2.content).pack(fill="both", expand=True)

        card3 = GlassCard(grid, title="Project Time", action_text="Full Report")
        card3.grid(row=1, column=0, sticky="nsew", padx=pad, pady=pad)
        BarChart(card3.content).pack(fill="both", expand=True)

        card4 = GlassCard(grid, title="Today's Schedule", action_text="View All")
        card4.grid(row=1, column=1, sticky="nsew", padx=pad, pady=pad)
        ScheduleList(card4.content).pack(fill="both", expand=True)

        card5 = GlassCard(grid, title="Upcoming Tasks", action_text="Manage")
        card5.grid(row=2, column=0, sticky="nsew", padx=pad, pady=pad)
        TaskList(card5.content).pack(fill="both", expand=True)

        card6 = GlassCard(grid, title="AI Suggestions", action_text="See All")
        card6.grid(row=2, column=1, sticky="nsew", padx=pad, pady=pad)
        SuggestionsCard(card6.content).pack(fill="both", expand=True)
