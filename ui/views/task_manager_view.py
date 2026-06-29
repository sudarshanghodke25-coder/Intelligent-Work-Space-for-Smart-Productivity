import customtkinter as ctk
import threading
from theme import Colors, Fonts
from services.event_bus import bus
from services.task_service import task_service
from services.task_parser import task_parser
from services.task_analytics import task_analytics
from authentication.session import current_session

from components.task_card import TaskCard
from components.stats_card import StatsCard
from components.filter_chip import FilterChip
from components.search_bar import SearchBar
from components.task_detail_panel import TaskDetailPanel
from components.task_modal import TaskModal

class TasksView(ctk.CTkFrame):
    """FLOWSPACE Task Manager V3 – Premium Productivity Workspace"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)
        
        self.user_id = current_session.user_id or 1
        self.current_filter = "All"
        self.current_sort = "Due Date"
        self.search_query = ""
        self.selected_task_id = None
        
        # Pagination
        self.current_offset = 0
        self.limit = 50
        self.all_loaded_tasks = []
        self.has_more = True
        self.is_loading = False
        
        # Responsive state
        self.left_visible = True
        self.right_visible = False
        
        # Grid Layout (3 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=200) # Left
        self.grid_columnconfigure(1, weight=3, minsize=400) # Center
        self.grid_columnconfigure(2, weight=0, minsize=0) # Right (hidden initially)
        
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()
        
        # Quick Add Bar at bottom of center panel
        self._build_quick_add_bar()
        
        # Subscriptions
        bus.subscribe("TASK_CREATED", self._on_task_event)
        bus.subscribe("TASK_UPDATED", self._on_task_event)
        bus.subscribe("TASK_DELETED", self._on_task_event)
        bus.subscribe("TASK_COMPLETED", self._on_task_event)
        bus.subscribe("TASKS_UPDATED", self._on_task_event) # from status engine
        
        # Keyboard Shortcuts
        app = self.winfo_toplevel()
        app.bind("<Control-n>", lambda e: self._open_task_modal())
        app.bind("<Control-f>", lambda e: self.search_bar.focus_search())
        app.bind("<Escape>", lambda e: self._toggle_right(False))
        
        self.bind("<Configure>", self._on_resize)
        
        self._load_data(reset=True)

    def _on_resize(self, event):
        width = event.width
        if width < 100: return # ignore initialization
        
        # 1600px+: Three columns
        # <1600px: Right panel collapsible (hidden by default unless explicitly toggled? we'll just hide it if <1400)
        # <1366px: Left panel collapsible
        
        if width >= 1600:
            if not self.left_visible: self._toggle_left(True)
            # Do NOT auto-toggle right panel. Only toggle left based on size.
        elif width >= 1366:
            if not self.left_visible: self._toggle_left(True)
            if self.right_visible: self._toggle_right(False)
        else:
            if self.left_visible: self._toggle_left(False)
            if self.right_visible: self._toggle_right(False)

    def _toggle_left(self, show: bool):
        self.left_visible = show
        if show:
            self.left_frame.grid()
            self.grid_columnconfigure(0, weight=1, minsize=200)
        else:
            self.left_frame.grid_remove()
            self.grid_columnconfigure(0, weight=0, minsize=0)
            
    def _toggle_right(self, show: bool):
        self.right_visible = show
        if show:
            self.right_frame.grid()
            self.grid_columnconfigure(2, weight=2, minsize=350)
        else:
            self.right_frame.grid_remove()
            self.grid_columnconfigure(2, weight=0, minsize=0)

    # --- LEFT PANEL (NAVIGATION) ---
    def _build_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=20, border_width=1, border_color=Colors.BORDER_SUBTLE)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 10), pady=10)
        self.left_frame.pack_propagate(False)
        
        header = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(20, 10))
        ctk.CTkLabel(header, text="Navigation", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        ctk.CTkButton(
            self.left_frame, text="+ New Task", font=Fonts.BUTTON, height=40,
            fg_color=Colors.CARD_FLOATING, hover_color=Colors.ACCENT_SUBTLE,
            border_width=1, border_color=Colors.ACCENT_PRIMARY, corner_radius=12,
            command=self._open_task_modal
        ).pack(fill="x", padx=15, pady=10)
        
        self.nav_container = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.nav_container.pack(fill="both", expand=True, padx=10, pady=10)

    def _render_left_nav(self):
        for widget in self.nav_container.winfo_children(): widget.destroy()
        
        nav_items = ["All", "Today", "Upcoming", "Completed", "Overdue"]
        for item in nav_items:
            self._create_nav_btn(item)
            
        # Get unique projects from loaded tasks (ideal: separate projects table fetch)
        projects = set(t.get("category") for t in self.all_loaded_tasks if t.get("category"))
        ctk.CTkLabel(self.nav_container, text="Projects", font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED).pack(anchor="w", pady=(15, 5), padx=5)
        if projects:
            for proj in sorted(list(projects)):
                self._create_nav_btn(f"Project: {proj}")
        else:
            ctk.CTkLabel(self.nav_container, text="No projects created", font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED).pack(anchor="w", padx=15, pady=2)

    def _create_nav_btn(self, name):
        btn_fg = Colors.CARD_HOVER if self.current_filter == name else "transparent"
        btn = ctk.CTkButton(
            self.nav_container, text=name.replace("Project: ", "📁 "), font=Fonts.BODY_BOLD, anchor="w",
            fg_color=btn_fg, hover_color=Colors.CARD_HOVER, text_color=Colors.TEXT_PRIMARY,
            command=lambda n=name: self._set_filter(n)
        )
        btn.pack(fill="x", pady=2)

    def _set_filter(self, name):
        self.current_filter = name
        self._load_data(reset=True)

    # --- CENTER PANEL (WORKSPACE) ---
    def _build_center_panel(self):
        self.center_frame = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=20, border_width=1, border_color=Colors.BORDER_SUBTLE)
        self.center_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.center_frame.pack_propagate(False)
        
        # Header Area (Search & Sort)
        header_area = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        header_area.pack(fill="x", padx=15, pady=(15, 5))
        
        # Responsive Toggles (Visible only on small screens)
        self.toggle_left_btn = ctk.CTkButton(header_area, text="☰", width=30, height=30, fg_color="transparent", hover_color=Colors.CARD_HOVER, command=lambda: self._toggle_left(not self.left_visible))
        self.toggle_left_btn.pack(side="left", padx=(0, 10))
        
        self.search_bar = SearchBar(header_area, command=self._on_search)
        self.search_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.sort_var = ctk.StringVar(value="Due Date")
        sort_combo = ctk.CTkComboBox(
            header_area, values=["Due Date", "Priority", "Created Date", "Progress", "Alphabetical"],
            variable=self.sort_var, command=self._on_sort, width=120, font=Fonts.BODY,
            fg_color=Colors.INPUT_BG, border_color=Colors.INPUT_BORDER, button_color=Colors.CARD_FLOATING, button_hover_color=Colors.CARD_HOVER
        )
        sort_combo.pack(side="right")
        
        # Filter Chips
        self.chips_frame = ctk.CTkScrollableFrame(self.center_frame, fg_color="transparent", height=40, orientation="horizontal")
        self.chips_frame.pack(fill="x", padx=10, pady=5)
        
        # KPIs
        self.kpi_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent", height=80)
        self.kpi_frame.pack(fill="x", padx=10, pady=5)
        
        # Main Content Container
        self.content_container = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.task_list_canvas = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        self.task_list_canvas.pack(fill="both", expand=True)
        
        # Quick Add Bar (will be packed at bottom)

    def _build_quick_add_bar(self):
        self.quick_add_frame = ctk.CTkFrame(self.center_frame, fg_color=Colors.INPUT_BG, corner_radius=12, border_width=1, border_color=Colors.INPUT_BORDER)
        self.quick_add_frame.pack(fill="x", side="bottom", padx=15, pady=15)
        
        self.quick_add_entry = ctk.CTkEntry(self.quick_add_frame, placeholder_text="Try: 'Study Python tomorrow at 8 PM' (Press Enter)", font=Fonts.ENTRY, fg_color="transparent", border_width=0)
        self.quick_add_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.quick_add_entry.bind("<Return>", self._on_quick_add)

    def _on_quick_add(self, event):
        text = self.quick_add_entry.get().strip()
        if not text: return
        
        # Parse and create task via parser
        self.quick_add_entry.delete(0, 'end')
        self.quick_add_entry.configure(placeholder_text="Parsing...")
        
        def _parse():
            try:
                task_parser.parse_and_create(self.user_id, text)
            finally:
                self.quick_add_entry.configure(placeholder_text="Try: 'Study Python tomorrow at 8 PM' (Press Enter)")
        
        threading.Thread(target=_parse, daemon=True).start()

    def _on_search(self, query):
        self.search_query = query.lower()
        self._load_data(reset=True)
        
    def _on_sort(self, choice):
        self.current_sort = choice
        self._load_data(reset=True)

    def _render_filter_chips(self):
        for widget in self.chips_frame.winfo_children(): widget.destroy()
        chips = ["All", "Today", "Upcoming", "High Priority", "Completed", "Overdue"]
        for c in chips:
            chip = FilterChip(self.chips_frame, text=c, is_active=(self.current_filter == c), command=lambda name=c: self._set_filter(name))
            chip.pack(side="left", padx=5)

    def _render_kpis(self):
        for widget in self.kpi_frame.winfo_children(): widget.destroy()
        
        stats = task_analytics.get_user_stats(self.user_id)
        
        kpis = [
            ("Total Active", stats["total_tasks"] - stats["completed_tasks"]),
            ("Completed", stats["completed_tasks"]),
            ("Overdue", stats["overdue_tasks"]),
            ("Completion", f"{stats['completion_rate']}%"),
            ("Prod. Score", f"{stats['productivity_score']}/100")
        ]
        
        for name, val in kpis:
            card = StatsCard(self.kpi_frame, title=name, value=val)
            card.pack(side="left", expand=True, fill="both", padx=2)

    def _render_empty_center_state(self):
        for widget in self.task_list_canvas.winfo_children(): widget.destroy()
        
        empty_frame = ctk.CTkFrame(self.task_list_canvas, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, pady=100)
        
        ctk.CTkLabel(empty_frame, text="Welcome to FLOWSPACE Task Manager", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(pady=(10, 5))
        ctk.CTkLabel(empty_frame, text="Start organizing your work.\nCreate your first task using the + New Task button or the AI Quick Add below.", font=Fonts.BODY, text_color=Colors.TEXT_MUTED, justify="center").pack(pady=(0, 20))
        
        ctk.CTkButton(
            empty_frame, text="+ New Task", font=Fonts.BUTTON, height=40,
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, corner_radius=12,
            command=self._open_task_modal
        ).pack()

    def _render_task_list(self, append=False):
        if not append:
            for widget in self.task_list_canvas.winfo_children(): widget.destroy()
            
        for task in self.all_loaded_tasks[self.current_offset:]:
            card = TaskCard(
                self.task_list_canvas, 
                task=task, 
                is_selected=(self.selected_task_id == task["id"]),
                on_click=self._on_task_click,
                on_complete=self._toggle_task_complete,
                on_edit=self._open_task_modal,
                on_delete=self._delete_single_task,
                on_details=self._request_open_details
            )
            card.pack(fill="x", pady=5)
            
        self.current_offset = len(self.all_loaded_tasks)
        
        # Load More button
        if hasattr(self, 'load_more_btn'):
            self.load_more_btn.destroy()
            
        if self.has_more:
            self.load_more_btn = ctk.CTkButton(self.task_list_canvas, text="Load More", font=Fonts.BODY_BOLD, fg_color="transparent", hover_color=Colors.CARD_HOVER, command=lambda: self._load_data(reset=False))
            self.load_more_btn.pack(pady=10)

    def _on_task_click(self, task):
        self.selected_task_id = task["id"]
        # Only select and highlight, do not open details automatically
        # Close the detail panel if it was open to prevent mismatch between selection and details
        if self.right_visible:
            self._toggle_right(False)
        self._render_task_list(append=False) 
        
    def _request_open_details(self, task):
        self.selected_task_id = task["id"]
        self._render_task_list(append=False)
        
        # Requirement: Do not display if it only contains basic info
        full_task = task_service.get_task(task["id"])
        subs = task_service.get_subtasks(task["id"])
        # Check if there's notes, description, or subtasks. We'll use a fast DB check for notes.
        from database.database import get_connection
        conn = get_connection()
        notes = conn.execute("SELECT content FROM task_notes WHERE task_id=?", (task["id"],)).fetchone()
        conn.close()
        
        has_desc = bool(full_task.get("description") and full_task.get("description").strip())
        has_notes = bool(notes and notes["content"] and notes["content"].strip())
        has_subs = len(subs) > 0
        
        if not (has_desc or has_notes or has_subs):
            # No meaningful content to show
            return
            
        if not self.right_visible:
            self._toggle_right(True)
        self._populate_right_panel(task)

    # --- ACTIONS ---
    def _open_task_modal(self, task=None):
        TaskModal(self.winfo_toplevel(), task=task, on_save=self._save_task_from_modal)
        
    def _save_task_from_modal(self, data):
        if "id" in data:
            task_service.update_task(data["id"], self.user_id, data)
        else:
            task_service.create_task(self.user_id, data)

    def _toggle_task_complete(self, task):
        new_status = "Pending" if task.get("status") == "Completed" else "Completed"
        task_service.update_task(task["id"], self.user_id, {"status": new_status, "progress": 100 if new_status == "Completed" else 0})

    def _delete_single_task(self, task):
        task_service.delete_task(task["id"], self.user_id)

    def _on_task_event(self, payload):
        # Refresh on any task modification
        self._load_data(reset=True)

    # --- RIGHT PANEL ---
    def _build_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=20, border_width=1, border_color=Colors.BORDER_SUBTLE)
        self.right_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=10)
        self.right_frame.pack_propagate(False)
        
        # Close button for right panel
        header = ctk.CTkFrame(self.right_frame, fg_color="transparent", height=30)
        header.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkButton(header, text="✕", width=24, height=24, fg_color="transparent", hover_color=Colors.CARD_HOVER, command=lambda: self._toggle_right(False)).pack(side="right")
        
        self.right_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.right_container.pack(fill="both", expand=True, padx=10, pady=10)

    def _populate_empty_state(self):
        for widget in self.right_container.winfo_children(): widget.destroy()
        
        stats = task_analytics.get_user_stats(self.user_id)
        
        if stats["total_tasks"] == 0:
            ctk.CTkLabel(self.right_container, text="FLOWSPACE Setup", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(10, 5), padx=5)
            ctk.CTkLabel(self.right_container, text="Create your first task to unlock productivity analytics.", font=Fonts.BODY, text_color=Colors.TEXT_MUTED).pack(anchor="w", pady=(0, 20), padx=5)
        else:
            ctk.CTkLabel(self.right_container, text="No Task Selected", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(10, 20), padx=5)
            score = stats["productivity_score"]
            score_card = StatsCard(self.right_container, "Productivity Summary", f"{score}/100 Score")
            score_card.pack(fill="x", pady=10)

    def _populate_right_panel(self, task_summary):
        for widget in self.right_container.winfo_children(): widget.destroy()
        
        task = task_service.get_task(task_summary["id"])
        if not task:
            self._populate_empty_state()
            return
            
        # Header
        header = ctk.CTkFrame(self.right_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text=task["title"], font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, wraplength=280, justify="left").pack(anchor="w")
        ctk.CTkLabel(header, text=f"Project: {task.get('category', 'Work')}  •  Priority: {task['priority']}", font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED).pack(anchor="w")
        
        self.detail_panel = TaskDetailPanel(self.right_container)
        self.detail_panel.pack(fill="both", expand=True)
        self.detail_panel.current_task = task
        
        # Overview Tab
        p_val = task.get("progress", 0)
        ctk.CTkLabel(self.detail_panel.overview_scroll, text="Progress", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0,5))
        pbar2 = ctk.CTkProgressBar(self.detail_panel.overview_scroll, fg_color=Colors.INPUT_BG, progress_color=Colors.ACCENT_PRIMARY, height=8)
        pbar2.pack(fill="x", pady=(0, 10))
        pbar2.set(p_val/100.0)
        
        # Subtasks rendering
        ctk.CTkLabel(self.detail_panel.overview_scroll, text="Subtasks", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(15,5))
        subs = task_service.get_subtasks(task["id"])
        
        for sub in subs:
            sf = ctk.CTkFrame(self.detail_panel.overview_scroll, fg_color="transparent")
            sf.pack(fill="x", pady=2)
            chk = ctk.CTkCheckBox(
                sf, text=sub["title"], font=Fonts.BODY, 
                command=lambda s=sub: task_service.update_subtask(s["id"], {"completed": not s["completed"]})
            )
            if sub["completed"]: chk.select()
            chk.pack(side="left")
        
        self.new_sub_entry = ctk.CTkEntry(self.detail_panel.overview_scroll, placeholder_text="+ Add subtask...", font=Fonts.ENTRY, fg_color="transparent")
        self.new_sub_entry.pack(fill="x", pady=10)
        self.new_sub_entry.bind("<Return>", lambda e: self._add_subtask(task["id"]))
        
        # Description Tab
        desc = task.get("description", "")
        if not desc: desc = "No description provided."
        ctk.CTkLabel(self.detail_panel.description_scroll, text=desc, font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, wraplength=260, justify="left").pack(anchor="w")
        
    def _add_subtask(self, task_id):
        title = self.new_sub_entry.get().strip()
        if title:
            task_service.create_subtask(task_id, title)
            self._load_data(reset=True) # refresh
            self.new_sub_entry.delete(0, 'end')

    # --- DATA LOADING ---
    def _load_data(self, reset=False):
        if self.is_loading: return
        self.is_loading = True
        
        if reset:
            self.all_loaded_tasks = []
            self.current_offset = 0
            self.has_more = True
            
        filters = {}
        if self.current_filter == "Today": filters["status"] = "Today" # Status engine sets this
        elif self.current_filter == "Upcoming": filters["status"] = "Upcoming"
        elif self.current_filter == "High Priority": filters["priority"] = "High"
        elif self.current_filter == "Completed": filters["status"] = "Completed"
        elif self.current_filter == "Overdue": filters["status"] = "Overdue"
        elif self.current_filter.startswith("Project: "): filters["category"] = self.current_filter.split("Project: ")[1]
        
        if self.search_query:
            filters["search"] = self.search_query
            
        tasks = task_service.get_tasks(self.user_id, filters, limit=self.limit, offset=self.current_offset)
        
        if len(tasks) < self.limit:
            self.has_more = False
            
        self.all_loaded_tasks.extend(tasks)
        
        # Post-sort because DB sort is simple
        def get_priority_val(p): return {"High": 0, "Medium": 1, "Low": 2}.get(p, 3)
        if self.current_sort == "Due Date": self.all_loaded_tasks.sort(key=lambda x: (x.get('due_date') or "9999-99-99"))
        elif self.current_sort == "Priority": self.all_loaded_tasks.sort(key=lambda x: get_priority_val(x.get('priority')))
        elif self.current_sort == "Progress": self.all_loaded_tasks.sort(key=lambda x: x.get('progress', 0), reverse=True)
        elif self.current_sort == "Created Date": self.all_loaded_tasks.sort(key=lambda x: (x.get('created_at') or "1970-01-01"), reverse=True)
        elif self.current_sort == "Alphabetical": self.all_loaded_tasks.sort(key=lambda x: x.get('title', '').lower())
        
        self._render_left_nav()
        self._render_kpis()
        self._render_filter_chips()
        
        if not self.all_loaded_tasks:
            self._render_empty_center_state()
            self._populate_empty_state()
        else:
            self._render_task_list(append=not reset)
            
            if self.selected_task_id:
                task = next((t for t in self.all_loaded_tasks if t["id"] == self.selected_task_id), None)
                if task:
                    self._populate_right_panel(task)
                else:
                    self.selected_task_id = None
                    self._populate_empty_state()
            else:
                self._populate_empty_state()
                
        self.is_loading = False
