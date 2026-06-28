import customtkinter as ctk
from datetime import datetime
from theme import Colors, Fonts, blend_color

class TaskCard(ctk.CTkFrame):
    def __init__(self, parent, task, is_selected=False, 
                 on_click=None, on_complete=None, 
                 on_edit=None, on_delete=None, on_details=None, **kwargs):
        
        self.bg_normal = Colors.ACCENT_SUBTLE if is_selected else Colors.CARD_FLOATING
        self.bg_hover = Colors.CARD_HOVER if not is_selected else blend_color(Colors.ACCENT_PRIMARY, 0.3)
        self.border_color = Colors.ACCENT_PRIMARY if is_selected else Colors.BORDER_SUBTLE
        
        super().__init__(parent, fg_color=self.bg_normal, corner_radius=12, border_width=1, border_color=self.border_color, **kwargs)
        
        self.task = task
        self.is_selected = is_selected
        self.on_click = on_click
        
        # Outer container
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(fill="x", padx=10, pady=10)
        
        # Completion Checkbox
        is_completed = task.get("status") == "Completed"
        self.comp_var = ctk.StringVar(value="on" if is_completed else "off")
        
        self.comp_chk = ctk.CTkCheckBox(
            self.inner, text="", width=24, variable=self.comp_var, onvalue="on", offvalue="off",
            command=lambda: on_complete(self.task) if on_complete else None
        )
        self.comp_chk.pack(side="left", padx=(0, 10))
        
        # Title and project
        title_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        
        # Strikethrough if completed
        title_text = f"~~{task['title']}~~" if is_completed else task["title"]
        title_color = Colors.TEXT_MUTED if is_completed else Colors.TEXT_PRIMARY
        
        self.title_lbl = ctk.CTkLabel(title_frame, text=title_text, font=Fonts.BODY_BOLD, text_color=title_color)
        self.title_lbl.pack(anchor="w")
        
        cat = task.get("category") or "Work"
        self.cat_lbl = ctk.CTkLabel(title_frame, text=cat, font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED)
        self.cat_lbl.pack(anchor="w")
        
        # Badges and Indicators
        badge_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        badge_frame.pack(side="left", padx=10)
        
        # Priority
        color_map = {"High": Colors.PRIORITY_HIGH, "Medium": Colors.PRIORITY_MEDIUM, "Low": Colors.PRIORITY_LOW}
        p_color = color_map.get(task.get("priority", "Low"), Colors.PRIORITY_LOW)
        ctk.CTkLabel(badge_frame, text=task.get("priority", "Low"), font=Fonts.CAPTION, text_color=p_color, fg_color=blend_color(p_color, 0.12), corner_radius=8, width=50).pack(side="left", padx=5)
        
        # Smart Due Date
        due_str = task.get("due_date")
        smart_due, due_color = self._get_smart_due_date(due_str)
        if smart_due:
            ctk.CTkLabel(badge_frame, text=smart_due, font=Fonts.CAPTION, text_color=due_color).pack(side="left", padx=5)
            
        # AI Badge
        if task.get("ai_generated"):
            ctk.CTkLabel(badge_frame, text="✨ AI", font=Fonts.CAPTION, text_color=Colors.ACCENT_PRIMARY).pack(side="left", padx=5)
            
        # Progress Bar
        prog_frame = ctk.CTkFrame(self.inner, fg_color="transparent", width=80)
        prog_frame.pack(side="left", padx=10)
        prog_frame.pack_propagate(False)
        
        p_val = task.get("progress", 0)
        pbar = ctk.CTkProgressBar(prog_frame, fg_color=Colors.INPUT_BG, progress_color=Colors.ACCENT_PRIMARY, height=6)
        pbar.pack(side="top", fill="x", pady=(8, 2))
        pbar.set(p_val / 100.0)
        ctk.CTkLabel(prog_frame, text=f"{p_val}%", font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED).pack(side="top")
        
        # Quick Actions
        actions_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        actions_frame.pack(side="right")
        
        btn_kwargs = {"font": Fonts.CAPTION, "width": 24, "height": 24, "fg_color": "transparent", "hover_color": Colors.CARD_HOVER}
        
        ctk.CTkButton(actions_frame, text="📄", text_color=Colors.TEXT_SECONDARY, command=lambda: on_details(task) if on_details else None, **btn_kwargs).pack(side="left", padx=2)
        ctk.CTkButton(actions_frame, text="✎", text_color=Colors.TEXT_SECONDARY, command=lambda: on_edit(task) if on_edit else None, **btn_kwargs).pack(side="left", padx=2)
        ctk.CTkButton(actions_frame, text="✕", text_color=Colors.ERROR, command=lambda: on_delete(task) if on_delete else None, **btn_kwargs).pack(side="left", padx=2)
        
        # Hover events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        for w in [self.inner, title_frame, self.title_lbl, self.cat_lbl, badge_frame, prog_frame]:
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            
        # Click events (except on buttons and checkboxes)
        self.bind("<Button-1>", self._handle_click)
        for w in [self.inner, title_frame, self.title_lbl, self.cat_lbl, badge_frame, prog_frame]:
            w.bind("<Button-1>", self._handle_click)
            
    def _get_smart_due_date(self, due_str):
        if not due_str:
            return None, Colors.TEXT_MUTED
            
        try:
            # Handle YYYY-MM-DD or YYYY-MM-DD HH:MM
            due_date = datetime.strptime(due_str[:10], "%Y-%m-%d").date()
            today = datetime.now().date()
            delta = (due_date - today).days
            
            if delta < 0:
                return "Overdue", Colors.ERROR
            elif delta == 0:
                return "Due Today", Colors.WARNING
            elif delta == 1:
                return "Due Tomorrow", Colors.INFO
            elif delta <= 7:
                return "Upcoming", Colors.SUCCESS
            else:
                return due_str[:10], Colors.TEXT_MUTED
        except ValueError:
            return due_str[:10], Colors.TEXT_MUTED

    def _on_enter(self, event):
        if not self.is_selected:
            self.configure(fg_color=self.bg_hover)

    def _on_leave(self, event):
        if not self.is_selected:
            self.configure(fg_color=self.bg_normal)

    def _handle_click(self, event):
        if self.on_click:
            self.on_click(self.task)
