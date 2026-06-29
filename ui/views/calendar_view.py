import threading
import customtkinter as ctk
import calendar
from datetime import datetime, timedelta
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from database.database import get_connection
from services.event_bus import bus
from services.ai_scheduling_service import ai_scheduling_service
from authentication.session import current_session

# Color mapping for entity types
ENTITY_COLORS = {
    "event": "#4A90E2",     # Blue
    "task": "#9013FE",      # Purple
    "focus": "#7ED321",     # Green
    "deadline": "#D0021B",  # Red
    "goal": "#F5A623"       # Orange
}

class CalendarView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = self.winfo_toplevel()
        
        # Master Grid: Row 0 (Header), Row 1 (Main Workspace), Row 2 (Bottom Actions)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        
        # 3-Column Layout: 30% | 45% | 25%
        self.grid_columnconfigure(0, weight=30)
        self.grid_columnconfigure(1, weight=45)
        self.grid_columnconfigure(2, weight=25)
        
        # State Variables
        self.current_date = datetime.now().date()
        self.selected_date = self.current_date
        self.view_mode = "Month"
        self.priority_mode = ctk.StringVar(value="Balanced")
        self.focus_duration = ctk.StringVar(value="50 min")
        self.density_mode = ctk.StringVar(value="Medium")
        self.is_generating = False
        
        # 5 Structural Regions
        self._build_top_header()
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()
        self._build_bottom_action_bar()
        
        # Load Data
        self._refresh_data()
        
        # Subscriptions
        bus.subscribe("EVENTS_UPDATED", self._safe_refresh)
        bus.subscribe("TASKS_UPDATED", self._safe_refresh)
        
    def _safe_refresh(self, data=None):
        self.app.after(0, self._refresh_data)
        
    def _refresh_data(self):
        self._rebuild_center_grid()
        self._rebuild_right_agenda()
        self._rebuild_right_history()
        self._rebuild_right_insights()

    # ==========================================
    # REGION 1: TOP HEADER
    # ==========================================
    def _build_top_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=(10, 5))
        
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left")
        ctk.CTkLabel(left_header, text="SCHEDULE STUDIO ✨", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(left_header, text="Plan, organize and optimize your time with AI.", font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        
        right_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_header.pack(side="right")
        
        self.status_badge = ctk.CTkLabel(right_header, text="AI Scheduler Ready", font=Fonts.SMALL_BOLD, fg_color=Colors.SUCCESS, text_color=Colors.BG_DEEPSPACE, corner_radius=10, width=120, height=36)
        self.status_badge.pack(side="left", padx=(0, 15))
        
        ctk.CTkButton(
            right_header, text="+ New Schedule", font=Fonts.BUTTON, width=120, height=36,
            fg_color=Colors.CARD_FLOATING, hover_color=Colors.ACCENT_SUBTLE,
            border_width=1, border_color=Colors.ACCENT_PRIMARY, corner_radius=12,
            command=self._clear_ai_schedules
        ).pack(side="left", padx=5)

    # ==========================================
    # REGION 2: LEFT PANEL
    # ==========================================
    def _build_left_panel(self):
        self.left_panel = GlassCard(self, title="")
        self.left_panel.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(4, 5), pady=(5, 10))
        
        container = self.left_panel.content
        
        # Section 1: Planning Mode
        ctk.CTkLabel(container, text="Planning Mode", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(10, 5))
        self.view_toggle = ctk.CTkSegmentedButton(container, values=["Day", "Week", "Month"], font=Fonts.SMALL, selected_color=Colors.ACCENT_PRIMARY, selected_hover_color=Colors.ACCENT_HOVER, command=self._set_view_mode)
        self.view_toggle.set(self.view_mode)
        self.view_toggle.pack(fill="x", pady=(0, 15))
        
        # Section 2: AI Prompt
        ctk.CTkLabel(container, text="AI Planning Prompt", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(10, 5))
        self.prompt_text = ctk.CTkTextbox(container, height=80, font=Fonts.BODY, fg_color=Colors.INPUT_BG, border_color=Colors.INPUT_BORDER, border_width=1)
        self.prompt_text.pack(fill="x", pady=(0, 5))
        self.prompt_text.insert("0.0", "Describe your schedule goals...\n(e.g., 'Plan my study sessions for this week')")
        self.prompt_text.bind("<FocusIn>", lambda e: self._clear_placeholder())
        
        # Section 3: Templates
        ctk.CTkLabel(container, text="Planning Templates", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(10, 5))
        template_grid = ctk.CTkFrame(container, fg_color="transparent")
        template_grid.pack(fill="x", pady=(0, 15))
        
        templates = ["Study Plan", "Project Plan", "Exam Prep", "Work Schedule", "Deep Focus", "Custom"]
        for i, tmp in enumerate(templates):
            btn = ctk.CTkButton(template_grid, text=tmp, font=Fonts.SMALL, fg_color=Colors.CARD_FLOATING, hover_color=Colors.CARD_HOVER, text_color=Colors.TEXT_PRIMARY, height=28, command=lambda t=tmp: self._apply_template(t))
            btn.grid(row=i//2, column=i%2, padx=4, pady=4, sticky="ew")
            template_grid.grid_columnconfigure(i%2, weight=1)
            
        # Section 4: AI Settings
        ctk.CTkLabel(container, text="AI Settings", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(10, 5))
        settings_frame = ctk.CTkFrame(container, fg_color="transparent")
        settings_frame.pack(fill="x", pady=(0, 20))
        
        self._add_setting_row(settings_frame, "Priority Mode", self.priority_mode, ["Balanced", "Productive", "Deadline Focused"])
        self._add_setting_row(settings_frame, "Focus Duration", self.focus_duration, ["25 min", "50 min", "90 min"])
        self._add_setting_row(settings_frame, "Schedule Density", self.density_mode, ["Light", "Medium", "Intensive"])
        
        # Primary Action
        self.generate_btn = ctk.CTkButton(container, text="Generate Schedule", font=Fonts.BUTTON, height=Dims.BUTTON_HEIGHT_LARGE, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, command=self._generate_schedule)
        self.generate_btn.pack(fill="x", side="bottom", pady=(20, 0))

    def _add_setting_row(self, parent, label, variable, options):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, font=Fonts.SMALL, text_color=Colors.TEXT_MUTED).pack(side="left")
        ctk.CTkOptionMenu(row, values=options, variable=variable, font=Fonts.SMALL, fg_color=Colors.CARD_FLOATING, button_color=Colors.CARD_HOVER, width=120).pack(side="right")

    def _clear_placeholder(self):
        content = self.prompt_text.get("0.0", "end").strip()
        if content.startswith("Describe your schedule goals"):
            self.prompt_text.delete("0.0", "end")

    def _apply_template(self, template):
        self.prompt_text.delete("0.0", "end")
        if template == "Study Plan":
            self.prompt_text.insert("0.0", "Create a balanced study plan for the next 3 days covering all my open tasks.")
        elif template == "Deep Focus":
            self.prompt_text.insert("0.0", "Schedule intensive deep work sessions for my highest priority tasks.")
            self.density_mode.set("Intensive")
            self.focus_duration.set("90 min")
        else:
            self.prompt_text.insert("0.0", f"Plan my schedule using the {template} template.")

    # ==========================================
    # REGION 3: CENTER WORKSPACE
    # ==========================================
    def _build_center_panel(self):
        self.center_panel = GlassCard(self, title="")
        self.center_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=(5, 5)) # Pad bottom 5 to leave room for bottom bar
        
        container = self.center_panel.content
        
        # Header (Inside Center Panel for navigation)
        header = ctk.CTkFrame(container, fg_color="transparent", height=40)
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header, text="Interactive Calendar Workspace", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        # Nav Controls
        nav_controls = ctk.CTkFrame(header, fg_color="transparent")
        nav_controls.pack(side="right")
        ctk.CTkButton(nav_controls, text="<", width=30, font=Fonts.BUTTON, fg_color=Colors.CARD_FLOATING, hover_color=Colors.CARD_HOVER, command=self._prev_period).pack(side="left", padx=2)
        self.period_label = ctk.CTkLabel(nav_controls, text="", font=Fonts.SUBHEADING, text_color=Colors.TEXT_PRIMARY, width=120)
        self.period_label.pack(side="left", padx=5)
        ctk.CTkButton(nav_controls, text=">", width=30, font=Fonts.BUTTON, fg_color=Colors.CARD_FLOATING, hover_color=Colors.CARD_HOVER, command=self._next_period).pack(side="left", padx=2)
        
        # Grid Container
        self.grid_container = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, pady=(10, 0))

    # ==========================================
    # REGION 5: BOTTOM ACTION BAR
    # ==========================================
    def _build_bottom_action_bar(self):
        self.bottom_bar = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=12, border_width=1, border_color=Colors.BORDER_SUBTLE, height=60)
        self.bottom_bar.grid(row=2, column=1, sticky="nsew", padx=5, pady=(5, 10))
        self.bottom_bar.pack_propagate(False)
        
        inner = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        inner.pack(expand=True) # Center contents
        
        actions = [
            ("Generate Day", self._generate_schedule),
            ("Optimize Schedule", lambda: print("Optimize")),
            ("Find Free Time", lambda: print("Find Free Time")),
            ("Resolve Conflicts", lambda: print("Conflicts")),
            ("Focus Blocks", lambda: print("Focus"))
        ]
        
        for txt, cmd in actions:
            ctk.CTkButton(
                inner, text=txt, font=Fonts.SMALL_BOLD, fg_color=Colors.CARD_FLOATING, 
                hover_color=Colors.CARD_HOVER, text_color=Colors.TEXT_PRIMARY, 
                height=36, command=cmd
            ).pack(side="left", padx=8)

    def _set_view_mode(self, mode):
        self.view_mode = mode
        self.view_toggle.set(mode)
        self._rebuild_center_grid()
        
    def _prev_period(self):
        if self.view_mode == "Month":
            first = self.current_date.replace(day=1)
            self.current_date = first - timedelta(days=1)
        elif self.view_mode == "Week":
            self.current_date -= timedelta(days=7)
        else:
            self.current_date -= timedelta(days=1)
        self._rebuild_center_grid()
        
    def _next_period(self):
        if self.view_mode == "Month":
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month + 1, day=1)
        elif self.view_mode == "Week":
            self.current_date += timedelta(days=7)
        else:
            self.current_date += timedelta(days=1)
        self._rebuild_center_grid()

    def _rebuild_center_grid(self):
        for widget in self.grid_container.winfo_children():
            widget.destroy()
            
        # Update Period Label
        if self.view_mode == "Month":
            self.period_label.configure(text=self.current_date.strftime("%B %Y"))
        elif self.view_mode == "Week":
            start = self.current_date - timedelta(days=self.current_date.weekday())
            end = start + timedelta(days=6)
            self.period_label.configure(text=f"{start.strftime('%b %d')} - {end.strftime('%b %d')}")
        else:
            self.period_label.configure(text=self.current_date.strftime("%B %d, %Y"))
            
        conn = get_connection()
        cursor = conn.cursor()
        
        # We need a unified query for all events/tasks across the period
        events = cursor.execute("SELECT * FROM events").fetchall()
        conn.close()
        
        events_dict = {}
        for e in events:
            date_str = None
            if e["start_time"]:
                date_str = e["start_time"].split()[0]
            elif e["event_date"]:
                date_str = e["event_date"]
                
            if date_str:
                if date_str not in events_dict:
                    events_dict[date_str] = []
                events_dict[date_str].append(dict(e))
                
        # Draw Month/Week Grid
        if self.view_mode in ["Month", "Week"]:
            days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for i, day in enumerate(days_of_week):
                self.grid_container.grid_columnconfigure(i, weight=1)
                ctk.CTkLabel(self.grid_container, text=day, font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_MUTED).grid(row=0, column=i, pady=(0, 10))
                
            cal = calendar.Calendar(firstweekday=0)
            if self.view_mode == "Month":
                weeks = cal.monthdatescalendar(self.current_date.year, self.current_date.month)
            else:
                start_of_week = self.current_date - timedelta(days=self.current_date.weekday())
                weeks = [[start_of_week + timedelta(days=i) for i in range(7)]]
                
            for row_idx, week in enumerate(weeks, start=1):
                self.grid_container.grid_rowconfigure(row_idx, weight=1)
                for col_idx, date_obj in enumerate(week):
                    is_today = (date_obj == datetime.now().date())
                    is_current_month = (date_obj.month == self.current_date.month)
                    
                    bg_color = Colors.CARD_FLOATING if is_today else "transparent"
                    border_color = Colors.ACCENT_PRIMARY if is_today else Colors.BORDER_SUBTLE
                    text_color = Colors.TEXT_PRIMARY if is_current_month else Colors.TEXT_DIM
                    
                    cell = ctk.CTkFrame(self.grid_container, fg_color=bg_color, border_width=1, border_color=border_color, corner_radius=6)
                    cell.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")
                    
                    # Date number
                    ctk.CTkLabel(cell, text=str(date_obj.day), font=Fonts.BODY_BOLD, text_color=text_color).pack(anchor="ne", padx=5, pady=2)
                    
                    # Render events
                    date_str = date_obj.strftime("%Y-%m-%d")
                    day_events = events_dict.get(date_str, [])
                    for i, ev in enumerate(day_events[:4]): # Show max 4
                        ev_type = ev.get("event_type", "event")
                        color = ENTITY_COLORS.get(ev_type, Colors.ACCENT_PRIMARY)
                        lbl = ctk.CTkLabel(cell, text=f"• {ev['title']}", font=Fonts.SMALL, text_color=color, anchor="w", justify="left")
                        lbl.pack(fill="x", padx=4, pady=1)
                        
                    if len(day_events) > 4:
                        ctk.CTkLabel(cell, text=f"+{len(day_events)-4} more", font=Fonts.SMALL, text_color=Colors.TEXT_MUTED).pack()
        else:
            # Day View
            date_str = self.current_date.strftime("%Y-%m-%d")
            day_events = events_dict.get(date_str, [])
            
            if not day_events:
                ctk.CTkLabel(self.grid_container, text="Your AI-generated schedule will appear here.", font=Fonts.HEADING, text_color=Colors.TEXT_MUTED).pack(expand=True)
                ctk.CTkLabel(self.grid_container, text="Create a plan and click Generate Schedule.", font=Fonts.BODY, text_color=Colors.TEXT_DIM).pack(pady=10)
            else:
                # Simple list for Day view
                for ev in sorted(day_events, key=lambda x: x.get('start_time') or x.get('event_time') or ''):
                    ev_type = ev.get("event_type", "event")
                    color = ENTITY_COLORS.get(ev_type, Colors.ACCENT_PRIMARY)
                    
                    card = ctk.CTkFrame(self.grid_container, fg_color=Colors.CARD_FLOATING, corner_radius=8, border_width=1, border_color=color)
                    card.pack(fill="x", padx=10, pady=5)
                    
                    time_str = ""
                    if ev.get("start_time"):
                        time_str = ev["start_time"].split()[1][:5]
                    elif ev.get("event_time"):
                        time_str = ev["event_time"]
                        
                    ctk.CTkLabel(card, text=time_str, font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_MUTED, width=60).pack(side="left", padx=10)
                    ctk.CTkLabel(card, text=ev["title"], font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=10)
                    
                    if ev.get("ai_generated"):
                        ctk.CTkLabel(card, text="✨ AI", font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_PRIMARY).pack(side="right", padx=10)

    # ==========================================
    # REGION 4: RIGHT PANEL
    # ==========================================
    def _build_right_panel(self):
        self.right_panel = GlassCard(self, title="")
        self.right_panel.grid(row=1, column=2, rowspan=2, sticky="nsew", padx=(5, 4), pady=(5, 10))
        container = self.right_panel.content
        
        # Insights Section
        ctk.CTkLabel(container, text="AI Insights", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))
        self.insights_frame = ctk.CTkFrame(container, fg_color=Colors.CARD_FLOATING, corner_radius=12, border_width=1, border_color=Colors.BORDER_SUBTLE)
        self.insights_frame.pack(fill="x", pady=(0, 20))
        
        # Deadlines Section
        ctk.CTkLabel(container, text="Upcoming Deadlines", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(0, 5))
        self.deadlines_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.deadlines_frame.pack(fill="x", pady=(0, 20))
        
        # Agenda Section
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Today's Agenda", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(header, text="+ Add", width=50, font=Fonts.SMALL, fg_color=Colors.CARD_FLOATING, hover_color=Colors.CARD_HOVER).pack(side="right")
        
        self.agenda_list = ctk.CTkScrollableFrame(container, fg_color="transparent", height=200)
        self.agenda_list.pack(fill="both", expand=True, pady=(0, 20))
        
        # History Section
        ctk.CTkLabel(container, text="Schedule History", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(0, 5))
        self.history_list = ctk.CTkScrollableFrame(container, fg_color="transparent", height=150)
        self.history_list.pack(fill="both", expand=True)

    def _rebuild_right_insights(self):
        for widget in self.insights_frame.winfo_children():
            widget.destroy()
            
        conn = get_connection()
        cursor = conn.cursor()
        
        # Calculate some dummy metrics based on tasks
        user_id = current_session.user_id or 1
        total_tasks = cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (user_id,)).fetchone()[0]
        completed = cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Completed' AND user_id=?", (user_id,)).fetchone()[0]
        score = int((completed / max(total_tasks, 1)) * 100) if total_tasks > 0 else 85
        
        # Fetch deadlines
        today = datetime.now().strftime("%Y-%m-%d")
        upcoming = cursor.execute("SELECT title, due_date FROM tasks WHERE due_date >= ? AND status != 'Completed' AND user_id=? ORDER BY due_date ASC LIMIT 2", (today, user_id)).fetchall()
        conn.close()
        
        ctk.CTkLabel(self.insights_frame, text=f"Productivity Score: {score}%", font=Fonts.BODY_BOLD, text_color=Colors.SUCCESS).pack(anchor="w", padx=10, pady=(10, 5))
        ctk.CTkLabel(self.insights_frame, text="Free Time: 2h 15m", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=0)
        ctk.CTkLabel(self.insights_frame, text="Focus Hours: 3.5h", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(0, 10))

        # Rebuild deadlines
        for widget in self.deadlines_frame.winfo_children():
            widget.destroy()
            
        if upcoming:
            for task in upcoming:
                ctk.CTkLabel(self.deadlines_frame, text=f"⚠ {task['title']}\nDue: {task['due_date'][:10]}", font=Fonts.SMALL, text_color=Colors.ERROR, justify="left").pack(anchor="w", pady=2)
        else:
            ctk.CTkLabel(self.deadlines_frame, text="No upcoming deadlines.", font=Fonts.SMALL, text_color=Colors.TEXT_MUTED).pack(anchor="w")

    def _rebuild_right_agenda(self):
        for widget in self.agenda_list.winfo_children():
            widget.destroy()
            
        conn = get_connection()
        cursor = conn.cursor()
        today_str = datetime.now().strftime("%Y-%m-%d")
        events = cursor.execute("SELECT * FROM events WHERE start_time LIKE ? OR event_date = ? ORDER BY start_time ASC", (f"{today_str}%", today_str)).fetchall()
        conn.close()
        
        if not events:
            ctk.CTkLabel(self.agenda_list, text="No events today.", font=Fonts.SMALL, text_color=Colors.TEXT_MUTED).pack(pady=20)
            return
            
        for ev in events:
            ev_type = ev.get("event_type", "event")
            color = ENTITY_COLORS.get(ev_type, Colors.ACCENT_PRIMARY)
            
            card = ctk.CTkFrame(self.agenda_list, fg_color="transparent")
            card.pack(fill="x", pady=4)
            
            time_str = ""
            if ev.get("start_time"):
                time_str = ev["start_time"].split()[1][:5]
            elif ev.get("event_time"):
                time_str = ev["event_time"]
                
            ctk.CTkLabel(card, text=time_str, font=Fonts.SMALL_BOLD, text_color=color, width=40).pack(side="left")
            ctk.CTkLabel(card, text=ev["title"], font=Fonts.SMALL, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=10)

    def _rebuild_right_history(self):
        for widget in self.history_list.winfo_children():
            widget.destroy()
            
        history = ai_scheduling_service.get_schedule_history()
        
        if not history:
            ctk.CTkLabel(self.history_list, text="No history.", font=Fonts.SMALL, text_color=Colors.TEXT_MUTED).pack()
            return
            
        for h in history:
            card = ctk.CTkFrame(self.history_list, fg_color=Colors.CARD_FLOATING, corner_radius=6)
            card.pack(fill="x", pady=4)
            
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            ctk.CTkLabel(info, text=h["schedule_name"], font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
            ctk.CTkLabel(info, text=h["created_at"][:10], font=Fonts.SMALL, text_color=Colors.TEXT_MUTED).pack(anchor="w")
            
            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(side="right", padx=5)
            ctk.CTkButton(actions, text="Load", width=40, font=Fonts.SMALL, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER).pack(pady=2)

    # ==========================================
    # ACTIONS
    # ==========================================
    def _generate_schedule(self):
        if self.is_generating: return
        
        prompt = self.prompt_text.get("0.0", "end").strip()
        if not prompt or prompt.startswith("Describe your schedule goals"):
            self.status_badge.configure(text="Error", fg_color=Colors.ERROR)
            return
            
        self.is_generating = True
        self.generate_btn.configure(text="Generating...", state="disabled")
        self.status_badge.configure(text="Thinking...", fg_color=Colors.ACCENT_PRIMARY)
        
        def run_generation():
            try:
                ai_scheduling_service.generate_schedule(
                    prompt=prompt,
                    priority_mode=self.priority_mode.get(),
                    focus_duration=self.focus_duration.get(),
                    density=self.density_mode.get()
                )
                self.app.after(0, self._on_generation_success)
            except Exception:
                self.app.after(0, lambda: self._on_generation_error(e))
                
        threading.Thread(target=run_generation, daemon=True).start()
        
    def _on_generation_success(self):
        self.is_generating = False
        self.generate_btn.configure(text="Generate Schedule", state="normal")
        self.status_badge.configure(text="Ready", fg_color=Colors.SUCCESS)
        self.prompt_text.delete("0.0", "end")
        self._refresh_data()
        
    def _on_generation_error(self, e):
        self.is_generating = False
        self.generate_btn.configure(text="Generate Schedule", state="normal")
        self.status_badge.configure(text="Failed", fg_color=Colors.ERROR)
        print(f"[CalendarView] Generation Error: {e}")

    def _clear_ai_schedules(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE ai_generated = 1")
        cursor.execute("DELETE FROM schedule_history")
        conn.commit()
        conn.close()
        self._refresh_data()
