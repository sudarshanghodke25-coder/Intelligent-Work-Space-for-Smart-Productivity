import customtkinter as ctk
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from database.database import get_connection
from authentication.session import current_session
from datetime import datetime

class GoalTrackerView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.pack_propagate(False)
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 20))
        ctk.CTkLabel(header, text="🏆 Goal Tracker", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(side="left", fill="x")
        
        # Add Goal Section
        self.add_card = GlassCard(self, title="New Target Milestone")
        self.add_card.pack(fill="x", padx=4, pady=(0, 20))
        self._build_add_form()
        
        # Goals List Section
        self.list_card = GlassCard(self, title="Active Objectives")
        self.list_card.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        
        self.scroll = ctk.CTkScrollableFrame(self.list_card.content, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, pady=10)
        
        self._load_goals()
        
    def _build_add_form(self):
        container = ctk.CTkFrame(self.add_card.content, fg_color="transparent")
        container.pack(fill="x", pady=10)
        
        self.title_entry = ctk.CTkEntry(
            container, placeholder_text="Goal Title (e.g. Launch v1.0)",
            font=Fonts.ENTRY, fg_color=Colors.INPUT_BG,
            border_color=Colors.INPUT_BORDER, height=Dims.ENTRY_HEIGHT, corner_radius=Dims.ENTRY_CORNER
        )
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.date_entry = ctk.CTkEntry(
            container, placeholder_text="Target Date (YYYY-MM-DD)",
            font=Fonts.ENTRY, fg_color=Colors.INPUT_BG,
            border_color=Colors.INPUT_BORDER, height=Dims.ENTRY_HEIGHT, corner_radius=Dims.ENTRY_CORNER,
            width=200
        )
        self.date_entry.pack(side="left", padx=(0, 10))
        
        btn = ctk.CTkButton(
            container, text="Add Goal", font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY, width=120, height=Dims.ENTRY_HEIGHT,
            corner_radius=Dims.ENTRY_CORNER, command=self._add_goal
        )
        btn.pack(side="left")
        
        self.feedback = ctk.CTkLabel(container, text="", font=Fonts.SMALL, text_color=Colors.TEXT_DIM)
        self.feedback.pack(side="left", padx=10)
        
    def _add_goal(self):
        title = self.title_entry.get().strip()
        date_str = self.date_entry.get().strip()
        
        if not title:
            self.feedback.configure(text="Title cannot be empty.", text_color=Colors.ERROR)
            return
            
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                self.feedback.configure(text="Invalid date. Use YYYY-MM-DD", text_color=Colors.ERROR)
                return
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        conn = get_connection()
        user_id = current_session.user_id or 1
        conn.execute("INSERT INTO goals (user_id, title, target_date, progress) VALUES (?, ?, ?, ?)", (user_id, title, date_str, 0))
        conn.commit()
        conn.close()
        
        self.feedback.configure(text="Goal added!", text_color=Colors.SUCCESS)
        self.after(3000, lambda: self.feedback.configure(text=""))
        
        self.title_entry.delete(0, 'end')
        self.date_entry.delete(0, 'end')
        self._load_goals()
        
    def _load_goals(self):
        for widget in self.scroll.winfo_children(): widget.destroy()
        
        conn = get_connection()
        user_id = current_session.user_id or 1
        goals = conn.execute("SELECT id, title, target_date, progress, status FROM goals WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
        conn.close()
        
        if not goals:
            ctk.CTkLabel(self.scroll, text="No active goals yet. Add one above to get started!", font=Fonts.BODY, text_color=Colors.TEXT_MUTED).pack(pady=40)
            return
            
        for g in goals:
            self._create_goal_item(g)
            
    def _create_goal_item(self, goal):
        item = ctk.CTkFrame(self.scroll, fg_color=Colors.CARD_FLOATING, corner_radius=10, border_width=1, border_color=Colors.BORDER_SUBTLE)
        item.pack(fill="x", pady=5)
        
        top = ctk.CTkFrame(item, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(top, text=goal['title'], font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(top, text=f"Target: {goal['target_date']}", font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY).pack(side="right")
        
        bot = ctk.CTkFrame(item, fg_color="transparent")
        bot.pack(fill="x", padx=15, pady=(5, 15))
        
        progress = goal['progress']
        color = Colors.SUCCESS if progress == 100 else Colors.ACCENT_PRIMARY
        
        bar = ctk.CTkProgressBar(bot, height=12, corner_radius=6, fg_color=Colors.CARD_BG, progress_color=color)
        bar.pack(side="left", fill="x", expand=True, padx=(0, 15))
        bar.set(progress / 100.0)
        
        ctk.CTkLabel(bot, text=f"{progress}%", font=Fonts.BODY_BOLD, text_color=color, width=40).pack(side="left")
        
        btn = ctk.CTkButton(bot, text="+10%", width=50, height=24, font=Fonts.SMALL, fg_color=Colors.BORDER_SUBTLE, hover_color=Colors.BORDER_HOVER, command=lambda g=goal['id'], p=progress: self._update_progress(g, p))
        btn.pack(side="right", padx=(10, 0))
        
        del_btn = ctk.CTkButton(bot, text="🗑️", width=30, height=24, font=Fonts.SMALL, fg_color="transparent", hover_color=Colors.ERROR, text_color=Colors.TEXT_MUTED, border_width=0, command=lambda g=goal['id']: self._delete_goal(g))
        del_btn.pack(side="right", padx=(0, 10))

    def _delete_goal(self, goal_id):
        conn = get_connection()
        conn.execute("DELETE FROM goals WHERE id=?", (goal_id,))
        conn.commit()
        conn.close()
        self._load_goals()

    def _update_progress(self, goal_id, current_progress):
        new_progress = min(100, current_progress + 10)
        status = "Completed" if new_progress == 100 else "In Progress"
        
        conn = get_connection()
        conn.execute("UPDATE goals SET progress=?, status=? WHERE id=?", (new_progress, status, goal_id))
        conn.commit()
        conn.close()
        
        self._load_goals()
