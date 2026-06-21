import customtkinter as ctk
import threading
from theme import Colors, Fonts, Dims, blend_color
from ui.glass_card import GlassCard
from database.database import get_connection
from services.event_bus import bus
from datetime import datetime

class TasksView(ctk.CTkFrame):
    """Hybrid Task Manager: Creation + Reactive Management."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)

        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        ctk.CTkLabel(
            header, text="✅ Task Manager", 
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left", fill="x")

        # Section A: Creation Form (Top)
        self.card = GlassCard(self, title="Create New Task")
        self.card.pack(fill="x", padx=4, pady=(10, 20))
        
        self._build_form()
        
        # Section B: Reactive Task List (Bottom)
        ctk.CTkLabel(self, text="Active Tasks", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x", padx=10, pady=(0, 5))
        
        self.task_list_frame = ctk.CTkScrollableFrame(
            self, fg_color=Colors.GLASS_FILL,
            border_width=1, border_color=Colors.GLASS_BORDER, corner_radius=10,
            scrollbar_button_color=Colors.GLASS_FILL_LIGHT,
            scrollbar_button_hover_color=Colors.GLASS_FILL_HOVER
        )
        self.task_list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 10))
        
        bus.subscribe("TASKS_UPDATED", self._on_tasks_updated)
        self._load_tasks()

    def _on_tasks_updated(self, payload):
        self.after(10, self._load_tasks)
        
    def _build_form(self):
        # Task Title
        ctk.CTkLabel(self.card.content, text="Task Title", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 4))
        self.title_entry = ctk.CTkEntry(self.card.content, placeholder_text="Enter task description...", height=Dims.ENTRY_HEIGHT, font=Fonts.ENTRY)
        self.title_entry.pack(fill="x", pady=(0, 16))
        
        # Due Date
        ctk.CTkLabel(self.card.content, text="Due Date (YYYY-MM-DD HH:MM)", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 4))
        self.date_entry = ctk.CTkEntry(self.card.content, placeholder_text="e.g. 2026-06-25 15:00", height=Dims.ENTRY_HEIGHT, font=Fonts.ENTRY)
        self.date_entry.pack(fill="x", pady=(0, 16))
        
        # Priority
        ctk.CTkLabel(self.card.content, text="Priority", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 4))
        self.priority_var = ctk.StringVar(value="Medium")
        self.priority_seg = ctk.CTkSegmentedButton(
            self.card.content, values=["Low", "Medium", "High"],
            variable=self.priority_var,
            selected_color=Colors.ACCENT_PRIMARY,
            selected_hover_color=Colors.ACCENT_HOVER,
            unselected_color=Colors.GLASS_FILL_LIGHT,
            unselected_hover_color=Colors.GLASS_FILL_HOVER,
            font=Fonts.BODY
        )
        self.priority_seg.pack(fill="x", pady=(0, 24))
        
        # Save Button
        self.save_btn = ctk.CTkButton(
            self.card.content, text="Save Task", font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
            height=Dims.BTN_HEIGHT, command=self._save_task
        )
        self.save_btn.pack(anchor="e")

        # Feedback label
        self.feedback = ctk.CTkLabel(self.card.content, text="", font=Fonts.SMALL, text_color=Colors.TEXT_DIM, anchor="w")
        self.feedback.pack(fill="x", pady=(8, 0))

    def _save_task(self):
        title = self.title_entry.get().strip()
        date_str = self.date_entry.get().strip()
        priority = self.priority_var.get()
        
        if not title:
            self.feedback.configure(text="Task title cannot be empty.", text_color=Colors.CHART_RED)
            return
            
        try:
            if not date_str:
                due = datetime.now()
            else:
                due = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            self.feedback.configure(text="Invalid date format. Use YYYY-MM-DD HH:MM", text_color=Colors.CHART_RED)
            return
            
        due_str = due.strftime("%Y-%m-%d %H:%M:%S")
        user_id = 1 
        
        # Synchronously save to DB
        conn = get_connection()
        conn.execute("INSERT INTO tasks (user_id, title, priority, due_date, progress) VALUES (?, ?, ?, ?, 0)",
                     (user_id, title, priority, due_str))
        conn.commit()
        conn.close()
        
        self.feedback.configure(text="Task created successfully!", text_color=Colors.CHART_GREEN)
        self.after(4000, lambda: self.feedback.configure(text=""))
        
        self.title_entry.delete(0, 'end')
        self.date_entry.delete(0, 'end')
        
        # Broadcast via EventBus
        bus.publish("TASKS_UPDATED", {"title": title, "priority": priority, "due_date": due_str})

    def _load_tasks(self):
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
            
        conn = get_connection()
        tasks = conn.execute("SELECT * FROM tasks WHERE status != 'Completed' ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END, due_date ASC").fetchall()
        conn.close()
        
        for task in tasks:
            self._build_task_card(task)

    def _build_task_card(self, task):
        # Card Container
        card = ctk.CTkFrame(self.task_list_frame, fg_color=Colors.GLASS_FILL_LIGHT, corner_radius=10, border_width=1, border_color=Colors.GLASS_BORDER)
        card.pack(fill="x", pady=5, padx=5)
        
        # Top Row (Title & Priority)
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(top_row, text=task["title"], font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(side="left", fill="x", expand=True)
        
        color_map = {
            "High": Colors.PRIORITY_HIGH,
            "Medium": Colors.PRIORITY_MEDIUM,
            "Low": Colors.PRIORITY_LOW
        }
        color = color_map.get(task["priority"], Colors.PRIORITY_LOW)
        
        badge = ctk.CTkLabel(
            top_row, text=task["priority"], font=Fonts.CAPTION,
            text_color=color, fg_color=blend_color(color, 0.12),
            corner_radius=8, width=60, height=20
        )
        badge.pack(side="right")
        
        # Bottom Row (Progress & Buttons)
        bot_row = ctk.CTkFrame(card, fg_color="transparent")
        bot_row.pack(fill="x", padx=15, pady=(5, 15))
        
        # Progress text
        progress_val = task["progress"] if task["progress"] is not None else 0
        ctk.CTkLabel(bot_row, text=f"{progress_val}%", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=(0, 10))
        
        # Progress Bar
        p_bar = ctk.CTkProgressBar(bot_row, fg_color=Colors.ENTRY_BG, progress_color=Colors.ACCENT_PRIMARY, height=8)
        p_bar.pack(side="left", fill="x", expand=True, padx=(0, 15))
        p_bar.set(progress_val / 100.0)
        
        # +25% Button
        ctk.CTkButton(
            bot_row, text="+25%", font=Fonts.SMALL_BOLD, width=50, height=24,
            fg_color=Colors.GLASS_FILL_LIGHT, hover_color=Colors.GLASS_FILL_HOVER,
            text_color=Colors.TEXT_PRIMARY, border_color=Colors.GLASS_BORDER_BRIGHT, border_width=1,
            command=lambda t=task: self._update_progress(t["id"], t["progress"])
        ).pack(side="right")

    def _update_progress(self, task_id, current_progress):
        def _worker():
            prog = current_progress if current_progress is not None else 0
            new_prog = min(prog + 25, 100)
            status = 'Completed' if new_prog == 100 else 'Pending'
            
            conn = get_connection()
            conn.execute("UPDATE tasks SET progress = ?, status = ? WHERE id = ?", (new_prog, status, task_id))
            conn.commit()
            conn.close()
            
            bus.publish("TASKS_UPDATED", {})
            bus.publish("COMPLETION_UPDATED", {})
            
        threading.Thread(target=_worker, daemon=True).start()
