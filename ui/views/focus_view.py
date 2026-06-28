import customtkinter as ctk
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from database.database import get_connection
from authentication.session import current_session

class FocusView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.pack_propagate(False)
        self.default_time = 25 * 60
        self.time_left = self.default_time
        self.is_running = False
        self.timer_job = None
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 20))
        ctk.CTkLabel(header, text="🎯 Focus Mode", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(side="left", fill="x")
        
        # Main Layout
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Timer Card
        self.timer_card = GlassCard(self, title="Pomodoro Timer")
        self.timer_card.grid(row=0, column=0, sticky="nsew", padx=(4, 6), pady=(0, 4))
        
        # Build Timer UI
        self._build_timer()
        
        # Info Card
        self.info_card = GlassCard(self, title="Focus Stats")
        self.info_card.grid(row=0, column=1, sticky="nsew", padx=(6, 4), pady=(0, 4))
        self._build_stats()
        
    def _build_timer(self):
        container = ctk.CTkFrame(self.timer_card.content, fg_color="transparent")
        container.pack(expand=True)
        
        # Massive Clock Display
        self.clock_label = ctk.CTkLabel(
            container, text="25:00",
            font=("Segoe UI", 96, "bold"),
            text_color=Colors.ACCENT_PRIMARY
        )
        self.clock_label.pack(pady=(20, 40))
        
        # Controls Frame
        controls = ctk.CTkFrame(container, fg_color="transparent")
        controls.pack(pady=10)
        
        self.start_btn = ctk.CTkButton(
            controls, text="Start", font=Fonts.BUTTON,
            fg_color=Colors.SUCCESS, hover_color=Colors.CHART_GREEN,
            text_color=Colors.TEXT_PRIMARY,
            width=120, height=Dims.BTN_HEIGHT, corner_radius=Dims.BTN_CORNER,
            command=self._start_timer
        )
        self.start_btn.pack(side="left", padx=10)
        
        self.pause_btn = ctk.CTkButton(
            controls, text="Pause", font=Fonts.BUTTON,
            fg_color=Colors.WARNING, hover_color=Colors.CHART_AMBER,
            text_color=Colors.TEXT_PRIMARY,
            width=120, height=Dims.BTN_HEIGHT, corner_radius=Dims.BTN_CORNER,
            command=self._pause_timer, state="disabled"
        )
        self.pause_btn.pack(side="left", padx=10)
        
        self.reset_btn = ctk.CTkButton(
            controls, text="Reset", font=Fonts.BUTTON,
            fg_color=Colors.CARD_FLOATING, hover_color=Colors.CARD_HOVER,
            text_color=Colors.TEXT_PRIMARY, border_width=1, border_color=Colors.BORDER_SUBTLE,
            width=120, height=Dims.BTN_HEIGHT, corner_radius=Dims.BTN_CORNER,
            command=self._reset_timer
        )
        self.reset_btn.pack(side="left", padx=10)
        
    def _build_stats(self):
        for widget in self.info_card.content.winfo_children(): widget.destroy()
        
        conn = get_connection()
        user_id = current_session.user_id or 1
        total_focus = conn.execute("SELECT SUM(duration_minutes) FROM focus_logs WHERE user_id=?", (user_id,)).fetchone()[0] or 0
        sessions_count = conn.execute("SELECT COUNT(*) FROM focus_logs WHERE user_id=?", (user_id,)).fetchone()[0] or 0
        conn.close()
        
        ctk.CTkLabel(self.info_card.content, text="Total Focus Time", font=Fonts.SUBHEADING, text_color=Colors.TEXT_SECONDARY).pack(pady=(30, 5))
        ctk.CTkLabel(self.info_card.content, text=f"{total_focus} Mins", font=("Segoe UI", 48, "bold"), text_color=Colors.ACCENT_PRIMARY).pack(pady=(0, 20))
        
        ctk.CTkLabel(self.info_card.content, text="Completed Sessions", font=Fonts.SUBHEADING, text_color=Colors.TEXT_SECONDARY).pack(pady=(10, 5))
        ctk.CTkLabel(self.info_card.content, text=f"{sessions_count}", font=("Segoe UI", 48, "bold"), text_color=Colors.CHART_CYAN).pack()
        
    def _update_clock_label(self):
        mins, secs = divmod(self.time_left, 60)
        self.clock_label.configure(text=f"{mins:02d}:{secs:02d}")
        
    def _tick(self):
        if self.is_running and self.time_left > 0:
            self.time_left -= 1
            self._update_clock_label()
            self.timer_job = self.after(1000, self._tick)
        elif self.time_left == 0:
            self.is_running = False
            self._handle_completion()
            
    def _start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal")
            self._tick()
            
    def _pause_timer(self):
        self.is_running = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")
        
    def _reset_timer(self):
        self._pause_timer()
        self.time_left = self.default_time
        self._update_clock_label()
        
    def _handle_completion(self):
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")
        
        # Save to DB
        conn = get_connection()
        user_id = current_session.user_id or 1
        conn.execute("INSERT INTO focus_logs (user_id, tag, duration_minutes) VALUES (?, ?, ?)", (user_id, "Work", 25))
        conn.commit()
        conn.close()
        
        self.time_left = self.default_time
        self._update_clock_label()
        self._build_stats() # Refresh stats
