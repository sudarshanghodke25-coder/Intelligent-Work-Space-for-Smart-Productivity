import datetime
import psutil
import customtkinter as ctk
from theme import Colors
from database.database import get_connection
from authentication.session import current_session
from services.event_bus import bus

# =========================================================================
# HELPER CUSTOM WIDGETS FOR GLASSMORPHISM & VISUALS
# =========================================================================

class CircularProgress(ctk.CTkCanvas):
    """Sleek canvas-based donut progress ring for productivity score."""
    def __init__(self, parent, size=110, thickness=12, value=78, fg_color="#8B5CF6", bg_color="#1E293B", **kwargs):
        super().__init__(parent, width=size, height=size, bg=Colors.CARD_BG, highlightthickness=0, **kwargs)
        self.size = size
        self.thickness = thickness
        self.value = value
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.draw()

    def draw(self):
        self.delete("all")
        margin = 4
        # Draw background ring
        self.create_oval(
            margin + self.thickness//2, margin + self.thickness//2,
            self.size - margin - self.thickness//2, self.size - margin - self.thickness//2,
            outline=self.bg_color, width=self.thickness
        )
        # Draw value arc
        extent = -(self.value / 100.0) * 360
        self.create_arc(
            margin + self.thickness//2, margin + self.thickness//2,
            self.size - margin - self.thickness//2, self.size - margin - self.thickness//2,
            start=90, extent=extent, outline=self.fg_color, width=self.thickness, style="arc"
        )
        # Draw percentage text
        self.create_text(
            self.size//2, self.size//2,
            text=f"{self.value}%", fill="#FFFFFF",
            font=("Inter", 18, "bold")
        )


class DashboardView(ctk.CTkFrame):
    """
    FLOWSPACE Premium Glassmorphism Dashboard.
    Matches the space theme interface with glowing elements.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        # Grid Layout: Main Content (100%)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main Content Area (Scrollable)
        self.left_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.BORDER_SUBTLE,
            scrollbar_button_hover_color=Colors.BORDER_HOVER
        )
        self.left_scroll.grid(row=0, column=0, sticky="nsew")
        
        # Build Dashboard Widgets
        self._build_left_section()
        
        # Start Time & Stats Loops
        self._update_system_stats()
        
        # Subscribe to events for live updates
        self._subscribe_to_events()

    def _subscribe_to_events(self):
        events = [
            "HISTORY_UPDATED", "TASK_CREATED", "TASK_COMPLETED", "TASK_DELETED",
            "CHAT_RESPONSE", "SUMMARY_GENERATED", "IMAGE_GEN_SUCCESS",
            "LOGOUT", "USER_LOGGED_IN", "ACTIVITY_ADDED", "FC_HISTORY_UPDATED"
        ]
        for event in events:
            bus.subscribe(event, self._refresh_all_safe)

    def _refresh_all_safe(self, *args, **kwargs):
        self.after(0, self._refresh_stats)
        if hasattr(self, '_refresh_recent_activity'):
            self.after(0, self._refresh_recent_activity)

    # =========================================================================
    # LEFT MAIN SECTION
    # =========================================================================

    def _build_left_section(self):
        # 1. Header (Greeting + Date)
        self._build_header()
        
        # 2. Stats Summary Row (6 glowing cards)
        self._build_stats_row()
        
        # 3. FLOWSPACE Tools Grid
        self._build_tools_grid()
        
        # 4. Three columns at the bottom
        self._build_bottom_widgets()
        
    def on_show(self):
        """Called automatically when navigating back to the dashboard."""
        self._refresh_stats()
        if hasattr(self, '_refresh_recent_activity'):
            self._refresh_recent_activity()

    def _refresh_stats(self, *args, **kwargs):
        """Update KPI stats dynamically."""
        if not hasattr(self, '_stat_labels'):
            return
            
        db_stats = self._get_db_stats()
        
        keys = ["conversations", "plans", "summaries", "files", "images"]
        for key in keys:
            if key in self._stat_labels:
                v_lbl, c_lbl = self._stat_labels[key]
                val = db_stats[key]
                v_lbl.configure(text=str(val))
                if val > 0:
                    c_lbl.configure(text="Active", text_color=Colors.SUCCESS)
                else:
                    c_lbl.configure(text="No Activity", text_color=Colors.TEXT_MUTED)

    def _build_header(self):
        header_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 20), padx=8)
        
        username = current_session.full_name or "FLOWSPACE User"
            
        greeting = "Good Evening"
        hour = datetime.datetime.now().hour
        if hour < 12: greeting = "Good Morning"
        elif hour < 17: greeting = "Good Afternoon"
        
        header_frame.grid_columnconfigure(0, weight=1)
        
        text_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        text_container.grid(row=0, column=0, sticky="w")
        
        title_lbl = ctk.CTkLabel(
            text_container, 
            text=f"{greeting}, {username}! 👋", 
            font=("Sora", 24, "bold"), 
            text_color=Colors.TEXT_PRIMARY
        )
        title_lbl.pack(anchor="w")
        
        subtitle_lbl = ctk.CTkLabel(
            text_container, 
            text="Here's what's happening in your workspace today.", 
            font=("Inter", 13), 
            text_color=Colors.TEXT_MUTED
        )
        subtitle_lbl.pack(anchor="w", pady=(4, 0))
        
        settings_btn = ctk.CTkButton(
            header_frame, 
            text="⚙️ Settings", 
            font=("Inter", 12, "bold"),
            fg_color=Colors.CARD_BG, 
            hover_color=Colors.CARD_HOVER, 
            text_color=Colors.TEXT_PRIMARY,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            corner_radius=8,
            width=100, 
            height=32,
            command=lambda: bus.publish("NAVIGATE_TO", "Settings")
        )
        settings_btn.grid(row=0, column=1, sticky="e")

    def _get_db_stats(self):
        """Query actual stats from DB. No fake fallbacks."""
        stats = {
            "conversations": 0,
            "plans": 0,
            "summaries": 0,
            "files": 0,
            "images": 0
        }
        try:
            conn = get_connection()
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM chat_messages")
            val = c.fetchone()[0]
            stats["conversations"] = val
            
            c.execute("SELECT COUNT(*) FROM plans WHERE user_id = ?", (current_session.user_id,))
            val = c.fetchone()[0]
            stats["plans"] = val
            
            c.execute("SELECT COUNT(*) FROM knowledge_sources")
            val = c.fetchone()[0]
            stats["summaries"] = val
            
            c.execute("SELECT COUNT(*) FROM image_history WHERE user_id = ?", (current_session.user_id,))
            val = c.fetchone()[0]
            stats["images"] = val
            
            # Count conversions
            try:
                c.execute("SELECT COUNT(*) FROM converter_history WHERE status='COMPLETED' AND user_id = ?", (current_session.user_id,))
                val = c.fetchone()[0]
                stats["files"] = val
            except:
                c.execute("SELECT COUNT(*) FROM converter_history WHERE status='COMPLETED'")
                val = c.fetchone()[0]
                stats["files"] = val
            
            conn.close()
        except:
            pass
        return stats

    def _build_stats_row(self):
        stats_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20), padx=4)
        
        db_stats = self._get_db_stats()
        self._stat_labels = {}
        
        cards_data = [
            ("conversations", "AI Conversations", db_stats["conversations"], "↑ Activity", "💬", Colors.ACCENT_PRIMARY),
            ("plans", "Plans Created", db_stats["plans"], "↑ Activity", "📋", Colors.ACCENT_ACTIVE),
            ("summaries", "Summaries", db_stats["summaries"], "↑ Activity", "📝", Colors.WARNING),
            ("files", "Files Converted", db_stats["files"], "↑ Activity", "🔄", Colors.SUCCESS),
            ("images", "Images Generated", db_stats["images"], "↑ Activity", "🎨", Colors.ACCENT_HOVER),
        ]
        
        # Grid config: 5 columns
        for col_idx in range(5):
            stats_frame.grid_columnconfigure(col_idx, weight=1)
            
        for i, (key, title, value, change, icon, color) in enumerate(cards_data):
            card = ctk.CTkFrame(
                stats_frame, fg_color=Colors.CARD_BG, 
                corner_radius=16, border_width=1, border_color=Colors.BORDER_SUBTLE,
                height=130
            )
            card.grid(row=0, column=i, padx=5, pady=4, sticky="nsew")
            card.pack_propagate(False)
            
            # Icon
            icon_lbl = ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 16), text_color=color)
            icon_lbl.pack(anchor="w", padx=12, pady=(10, 2))
            
            # Title
            t_lbl = ctk.CTkLabel(card, text=title, font=("Inter", 11), text_color=Colors.TEXT_MUTED)
            t_lbl.pack(anchor="w", padx=12)
            
            # Value
            v_lbl = ctk.CTkLabel(card, text=str(value), font=("Sora", 18, "bold"), text_color=Colors.TEXT_PRIMARY)
            v_lbl.pack(anchor="w", padx=12)
            
            # Determine initial change text
            change_text = "Active" if value > 0 else "No Activity"
            change_color = Colors.SUCCESS if value > 0 else Colors.TEXT_MUTED
            
            # Change
            c_lbl = ctk.CTkLabel(card, text=change_text, font=("Inter", 9), text_color=change_color)
            c_lbl.pack(anchor="w", padx=12, pady=(2, 0))
            
            self._stat_labels[key] = (v_lbl, c_lbl)
            
            # Hover Glow bindings
            self._bind_glow_hover(card, color)

    def _build_tools_grid(self):
        # Section title
        title_lbl = ctk.CTkLabel(self.left_scroll, text="FLOWSPACE TOOLS", font=("Sora", 12, "bold"), text_color=Colors.TEXT_SECONDARY)
        title_lbl.pack(anchor="w", padx=8, pady=(10, 10))
        
        grid_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        grid_frame.pack(fill="x", padx=4)
        
        tools = [
            ("FLOWSPACE AI", "Chat with AI and get intelligent assistance for any task.", "🤖", "FLOWSPACE AI", Colors.ACCENT_PRIMARY),
            ("AI Planner", "Plan smart. Create roadmaps, set goals and achieve more.", "📋", "AI Planner", Colors.ACCENT_ACTIVE),
            ("Summarizer", "Extract key insights and summarize your documents fast.", "📝", "Summarizer", Colors.WARNING),
            ("Image Studio", "Generate, edit, and enhance images using AI models.", "🎨", "Image Studio", Colors.ACCENT_HOVER),
            ("File Converter", "Convert files between various formats seamlessly.", "🔄", "File Converter", Colors.SUCCESS),
            ("Settings", "Manage your workspace preferences and configurations.", "⚙️", "Settings", Colors.TEXT_MUTED),
        ]
        
        for col_idx in range(6):
            grid_frame.grid_columnconfigure(col_idx, weight=1)
            
        for i, (title, desc, icon, target, color) in enumerate(tools):
            card = ctk.CTkFrame(
                grid_frame, fg_color="transparent", 
                corner_radius=18, border_width=1, border_color=Colors.BORDER_SUBTLE,
                height=180
            )
            card.grid(row=0, column=i, padx=5, pady=4, sticky="nsew")
            card.pack_propagate(False)
            
            card.bind("<Button-1>", lambda e, t=target: bus.publish("NAVIGATE_TO", t))
            
            # Custom Icon Container
            icon_frame = ctk.CTkFrame(card, fg_color=color, corner_radius=12, width=38, height=38)
            icon_frame.pack(anchor="w", padx=15, pady=(15, 10))
            icon_frame.pack_propagate(False)
            icon_frame.bind("<Button-1>", lambda e, t=target: bus.publish("NAVIGATE_TO", t))
            ctk.CTkLabel(icon_frame, text=icon, font=("Segoe UI Emoji", 16)).pack(expand=True)
            
            # Text Details
            ctk.CTkLabel(card, text=title, font=("Sora", 14, "bold"), text_color=Colors.TEXT_PRIMARY).pack(anchor="w", padx=15)
            
            desc_lbl = ctk.CTkLabel(
                card, text=desc, font=("Inter", 11), 
                text_color=Colors.TEXT_MUTED, wraplength=140, justify="left"
            )
            desc_lbl.pack(anchor="w", padx=15, pady=(4, 0))
            desc_lbl.bind("<Button-1>", lambda e, t=target: bus.publish("NAVIGATE_TO", t))
            
            # Arrow
            arrow = ctk.CTkLabel(card, text="→", font=("Sora", 16, "bold"), text_color=color)
            arrow.pack(side="bottom", anchor="e", padx=15, pady=10)
            arrow.bind("<Button-1>", lambda e, t=target: bus.publish("NAVIGATE_TO", t))
            
            # Hover Glow bindings
            self._bind_glow_hover(card, color)

    def _build_bottom_widgets(self):
        bottom_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=20, padx=4)
        
        # 1 column grid
        bottom_frame.grid_columnconfigure(0, weight=1)
        
        # --- Column 1: Recent Activity ---
        act_card = ctk.CTkFrame(bottom_frame, fg_color=Colors.CARD_BG, corner_radius=18, border_width=1, border_color=Colors.BORDER_SUBTLE, height=260)
        act_card.grid(row=0, column=0, padx=5, pady=4, sticky="nsew")
        act_card.pack_propagate(False)
        self._build_recent_activity(act_card)

    def _build_today_schedule(self, card):
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(header, text="Today's Schedule", font=("Sora", 13, "bold"), text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="View All", font=("Inter", 11), text_color=Colors.ACCENT_PRIMARY, cursor="hand2").pack(side="right")
        
        timeline = [
            ("10:00 AM", "AI Study Session", "Prepare for ML interview", Colors.ACCENT_PRIMARY),
            ("02:00 PM", "Project Meeting", "Discuss new requirements", Colors.ACCENT_ACTIVE),
            ("05:30 PM", "Workout Time", "Fitness and health", Colors.SUCCESS)
        ]
        
        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8)
        
        for time, title, desc, color in timeline:
            item_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            item_frame.pack(fill="x", pady=6)
            
            # Left timeline dot/line
            line_frame = ctk.CTkFrame(item_frame, fg_color="transparent", width=18)
            line_frame.pack(side="left", fill="y", padx=(2, 8))
            line_frame.pack_propagate(False)
            
            dot = ctk.CTkFrame(line_frame, width=8, height=8, corner_radius=4, fg_color=color)
            dot.place(relx=0.5, rely=0.3, anchor="center")
            
            # Content
            details = ctk.CTkFrame(item_frame, fg_color="transparent")
            details.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(details, text=time, font=("Inter", 10, "bold"), text_color=color).pack(anchor="w")
            ctk.CTkLabel(details, text=title, font=("Inter", 11, "bold"), text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
            ctk.CTkLabel(details, text=desc, font=("Inter", 9), text_color=Colors.TEXT_MUTED).pack(anchor="w")

    def _build_recent_activity(self, card):
        self.recent_activity_card = card
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(header, text="Recent Activity", font=("Sora", 13, "bold"), text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="View All", font=("Inter", 11), text_color=Colors.ACCENT_PRIMARY, cursor="hand2").pack(side="right")
        
        self.recent_activity_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.recent_activity_scroll.pack(fill="both", expand=True, padx=8)
        self._refresh_recent_activity()

    def _refresh_recent_activity(self, *args):
        if not hasattr(self, 'recent_activity_scroll'):
            return
            
        for widget in self.recent_activity_scroll.winfo_children():
            widget.destroy()
            
        activities = []
        try:
            conn = get_connection()
            # Fetch with user details for accurate account name
            rows = conn.execute('''
                SELECT a.description, a.timestamp, u.full_name 
                FROM activities a 
                LEFT JOIN users u ON a.user_id = u.id 
                WHERE a.user_id = ?
                ORDER BY a.id DESC LIMIT 10
            ''', (current_session.user_id,)).fetchall()
            
            if rows and len(rows) > 0:
                for r in rows:
                    desc = r["description"]
                    t_str = r["timestamp"]
                    user_name = r["full_name"] or "FLOWSPACE User"
                    
                    # Formatting time and date accurately
                    formatted_time = t_str # fallback
                    try:
                        dt = datetime.datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")
                        # DB stores as UTC, calculate manual offset to avoid astimezone() issues on Windows GUI
                        offset = datetime.datetime.now() - datetime.datetime.utcnow()
                        dt_local = dt + offset
                        formatted_time = dt_local.strftime("%b %d, %Y at %I:%M %p")
                    except:
                        pass
                        
                    activities.append((desc, f"{user_name} • {formatted_time}", Colors.ACCENT_PRIMARY))
            conn.close()
        except Exception:
            pass
            
        if not activities:
            activities = [("No recent activity.", "", Colors.TEXT_MUTED)]
            
        for desc, time_str, color in activities:
            item = ctk.CTkFrame(self.recent_activity_scroll, fg_color="transparent")
            item.pack(fill="x", pady=5)
            
            dot = ctk.CTkFrame(item, width=6, height=6, corner_radius=3, fg_color=color)
            dot.pack(side="left", padx=(5, 8))
            
            details = ctk.CTkFrame(item, fg_color="transparent")
            details.pack(side="left", fill="x", expand=True)
            
            desc_lbl = ctk.CTkLabel(details, text=desc, font=("Inter", 10), text_color=Colors.TEXT_SECONDARY, wraplength=180, justify="left")
            desc_lbl.pack(anchor="w")
            
            if time_str:
                time_lbl = ctk.CTkLabel(details, text=time_str, font=("Inter", 9), text_color=Colors.TEXT_MUTED)
                time_lbl.pack(anchor="w")

    def _build_productivity_score(self, card):
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 8))
        ctk.CTkLabel(header, text="Productivity Score", font=("Sora", 13, "bold"), text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=15)
        
        # Donut Chart & Note
        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x")
        
        donut = CircularProgress(row1, size=95, thickness=10, value=78, fg_color=Colors.ACCENT_PRIMARY, bg_color=Colors.BORDER_SUBTLE)
        donut.pack(side="left")
        
        note_lbl = ctk.CTkLabel(
            row1, text="Great job! You are more productive than 78% of users.", 
            font=("Inter", 10), text_color=Colors.TEXT_MUTED, wraplength=110, justify="left"
        )
        note_lbl.pack(side="left", padx=(12, 0))
        
        # Custom Bar Chart
        bar_frame = ctk.CTkFrame(body, fg_color="transparent", height=90)
        bar_frame.pack(fill="x", pady=(15, 0))
        bar_frame.pack_propagate(False)
        
        days_data = [
            ("Mon", 45), ("Tue", 70), ("Wed", 60), ("Thu", 80), ("Fri", 40), ("Sat", 30), ("Sun", 50)
        ]
        
        # Create columns
        for col_idx in range(7):
            bar_frame.grid_columnconfigure(col_idx, weight=1)
            
        for idx, (day, val) in enumerate(days_data):
            col = ctk.CTkFrame(bar_frame, fg_color="transparent")
            col.grid(row=0, column=idx, sticky="nsew")
            
            # Chart Bar Container
            bar_container = ctk.CTkFrame(col, fg_color="transparent", height=50)
            bar_container.pack(fill="x")
            
            # Vertical Bar itself
            bar_h = int((val / 100) * 45)
            # spacer
            spacer = ctk.CTkFrame(bar_container, fg_color="transparent", height=45 - bar_h)
            spacer.pack(fill="x")
            
            bar = ctk.CTkFrame(bar_container, fg_color=Colors.ACCENT_PRIMARY, corner_radius=4, height=bar_h)
            bar.pack(fill="x", padx=4)
            
            lbl = ctk.CTkLabel(col, text=day, font=("Inter", 9), text_color=Colors.TEXT_MUTED)
            lbl.pack(pady=(2, 0))



    def _build_upcoming_plans(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(0, 6))
        ctk.CTkLabel(header, text="Upcoming Plans", font=("Sora", 12, "bold"), text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="View All", font=("Inter", 10), text_color=Colors.ACCENT_PRIMARY, cursor="hand2").pack(side="right")
        
        plans = [
            ("Complete Python Course", "Study", "25 Jun"),
            ("Build Portfolio Website", "Project", "28 Jun"),
            ("Data Analysis Project", "Work", "01 Jul"),
            ("Daily Workout", "Habit", "Everyday")
        ]
        
        # Load from plans table if available
        try:
            conn = get_connection()
            rows = conn.execute("SELECT title, created_at FROM plans WHERE user_id = ? LIMIT 4", (current_session.user_id,)).fetchall()
            if rows and len(rows) > 0:
                plans = []
                for idx, r in enumerate(rows):
                    tag = "Project" if idx % 2 == 0 else "Study"
                    date_str = "Jun 28"
                    plans.append((r["title"], tag, date_str))
            conn.close()
        except:
            pass

        for title, tag, date in plans:
            row = ctk.CTkFrame(parent, fg_color="transparent", height=32)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)
            
            checkbox = ctk.CTkCheckBox(row, text=title, font=("Inter", 11), border_color=Colors.TEXT_MUTED, text_color=Colors.TEXT_SECONDARY)
            checkbox.pack(side="left", padx=5)
            
            # Right date/tag info
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="right")
            
            tag_color = Colors.ACCENT_PRIMARY if tag == "Study" else (Colors.ACCENT_ACTIVE if tag == "Project" else Colors.SUCCESS)
            tag_lbl = ctk.CTkLabel(info, text=tag, font=("Inter", 8, "bold"), text_color=tag_color)
            tag_lbl.pack(side="left", padx=4)
            
            date_lbl = ctk.CTkLabel(info, text=date, font=("Inter", 9), text_color=Colors.TEXT_MUTED)
            date_lbl.pack(side="left", padx=4)

    def _build_workspace_insights(self, parent):
        ctk.CTkLabel(parent, text="Workspace Insights", font=("Sora", 12, "bold"), text_color=Colors.TEXT_PRIMARY).pack(anchor="w", padx=8, pady=(0, 8))
        
        insights = [
            ("Focus Time", "17h 45m", "⏱️", Colors.ACCENT_PRIMARY),
            ("Task Completion", "89%", "☑️", Colors.ACCENT_ACTIVE),
            ("Goals Achieved", "12", "🏆", Colors.SUCCESS),
            ("Day Streak", "4", "🔥", Colors.WARNING)
        ]
        
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=4)
        
        # Grid config: 2x2
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        
        for idx, (title, value, icon, color) in enumerate(insights):
            r = idx // 2
            c = idx % 2
            
            card = ctk.CTkFrame(grid, fg_color=Colors.CARD_FLOATING, corner_radius=12, border_width=1, border_color=Colors.BORDER_SUBTLE, height=75)
            card.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            card.pack_propagate(False)
            
            # Icon row
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(8, 0))
            
            icon_lbl = ctk.CTkLabel(header, text=icon, font=("Segoe UI Emoji", 14), text_color=color)
            icon_lbl.pack(side="left")
            
            val_lbl = ctk.CTkLabel(header, text=value, font=("Sora", 12, "bold"), text_color=Colors.TEXT_PRIMARY)
            val_lbl.pack(side="right")
            
            title_lbl = ctk.CTkLabel(card, text=title, font=("Inter", 10), text_color=Colors.TEXT_MUTED)
            title_lbl.pack(anchor="w", padx=10, pady=(2, 0))

    # =========================================================================
    # VISUAL & GLOW TRANSITIONS (Hover logic)
    # =========================================================================

    def _bind_glow_hover(self, widget, glow_color):
        """Bind hover animations to dynamically change border colors and add subtle glow."""
        def on_enter(event):
            widget.configure(border_color=glow_color, border_width=1)
            
        def on_leave(event):
            widget.configure(border_color=Colors.BORDER_SUBTLE, border_width=1)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
        # Bind children to let them delegate events
        for child in widget.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

    def _update_system_stats(self):
        try:
            psutil.cpu_percent(interval=None)
            psutil.virtual_memory().percent
        except:
            pass
        self.after(60000, self._update_system_stats)
