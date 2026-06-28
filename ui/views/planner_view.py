import customtkinter as ctk
import threading
import json
import urllib.parse
import webbrowser
from datetime import datetime
from theme import Colors, Fonts, Dims
from database.database import get_connection
from services.event_bus import bus
from services.ai_service import ai_service
from authentication.session import current_session
from utils.ui_helpers import destroy_tracked

class PlannerView(ctk.CTkFrame):
    """AI-Powered Roadmap and Planning Workspace"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)
        
        self.current_plan_id = None
        self.user_id = current_session.user_id or 1
        self._roadmap_widgets = []
        self._center_widgets = []
        self._resource_widgets = []
        
        # Layout: Main Grid (Row 0: Header, Row 1: 3 Columns, Row 2: Bottom Input)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        
        self.grid_columnconfigure(0, weight=1, minsize=250) # Left (Roadmaps)
        self.grid_columnconfigure(1, weight=3) # Center (Workspace)
        self.grid_columnconfigure(2, weight=1, minsize=300) # Right (Resources)
        
        self._build_top_header()
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()
        self._build_bottom_panel()
        
        bus.subscribe("ROADMAP_GENERATED", self._on_roadmap_generated)
        
        self._load_roadmaps_list()

    def on_show(self):
        threading.Thread(target=self._load_roadmaps_list_async, daemon=True).start()

    def _load_roadmaps_list_async(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, status, plan_type, updated_at FROM plans WHERE user_id=? ORDER BY updated_at DESC", (self.user_id,))
        plans = cursor.fetchall()
        conn.close()
        self.after(0, lambda: self._render_roadmaps_list(plans))

    def _clear_center(self):
        destroy_tracked(self._center_widgets)

    def _clear_roadmaps(self):
        destroy_tracked(self._roadmap_widgets)

    def _clear_resources(self):
        destroy_tracked(self._resource_widgets)

    # --- TOP HEADER ---
    def _build_top_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=(10, 5))
        
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left")
        ctk.CTkLabel(left_header, text="AI Planner", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(left_header, text="Plan smart. Achieve more.", font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        
        right_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_header.pack(side="right")
        
        ctk.CTkButton(
            right_header, text="+ New Plan", font=Fonts.BUTTON, width=100, height=36,
            fg_color=Colors.CARD_FLOATING, hover_color=Colors.ACCENT_SUBTLE,
            border_width=1, border_color=Colors.ACCENT_PRIMARY, corner_radius=12,
            command=self._clear_workspace
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            right_header, text="⚙ Settings", font=Fonts.BUTTON, width=100, height=36,
            fg_color="transparent", hover_color=Colors.CARD_HOVER,
            text_color=Colors.TEXT_SECONDARY, corner_radius=12,
            command=lambda: bus.publish("NAVIGATE_TO", "Settings")
        ).pack(side="left", padx=5)

    # --- LEFT PANEL (ROADMAPS LIST) ---

    def _build_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=20, border_width=1, border_color=Colors.BORDER_SUBTLE)
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 10), pady=(5, 10))
        self.left_frame.pack_propagate(False)
        
        header = ctk.CTkFrame(self.left_frame, fg_color="transparent", height=50)
        header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(header, text="Your Roadmaps", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        self.roadmap_list_canvas = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.roadmap_list_canvas.pack(fill="both", expand=True, padx=10, pady=5)

    def _load_roadmaps_list(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, status, plan_type, updated_at FROM plans WHERE user_id=? ORDER BY updated_at DESC", (self.user_id,))
        plans = cursor.fetchall()
        conn.close()
        self._render_roadmaps_list(plans)

    def _render_roadmaps_list(self, plans):
        self._clear_roadmaps()
        
        if not plans:
            lbl = ctk.CTkLabel(self.roadmap_list_canvas, text="No plans created yet.\nGenerate your first roadmap\nwith Aurex AI.", font=Fonts.BODY, text_color=Colors.TEXT_MUTED, justify="center")
            lbl.pack(pady=40)
            self._roadmap_widgets.append(lbl)
            return
            
        for p in plans:
            card = ctk.CTkFrame(
                self.roadmap_list_canvas,
                fg_color=Colors.CARD_FLOATING if p["id"] != self.current_plan_id else Colors.ACCENT_SUBTLE,
                corner_radius=12, border_width=1,
                border_color=Colors.BORDER_SUBTLE if p["id"] != self.current_plan_id else Colors.BORDER_ACTIVE
            )
            card.pack(fill="x", pady=5)
            self._roadmap_widgets.append(card)
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(inner, text=p["title"], font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w", wraplength=200, justify="left").pack(fill="x")
            
            meta_frame = ctk.CTkFrame(inner, fg_color="transparent")
            meta_frame.pack(fill="x", pady=(5, 0))
            
            ctk.CTkLabel(meta_frame, text=p["status"], font=Fonts.CAPTION, text_color=Colors.ACCENT_PRIMARY).pack(side="left")
            ctk.CTkLabel(meta_frame, text=f" • {p['plan_type']}", font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED).pack(side="left")
            
            # Bindings
            pid = p["id"]
            for w in [card, inner, meta_frame] + inner.winfo_children() + meta_frame.winfo_children():
                w.bind("<Button-1>", lambda e, plan_id=pid: self._load_plan(plan_id))
                w.configure(cursor="hand2")

    # --- CENTER PANEL (WORKSPACE) ---

    def _build_center_panel(self):
        self.center_frame = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=20, border_width=1, border_color=Colors.BORDER_SUBTLE)
        self.center_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=(5, 10))
        self.center_frame.pack_propagate(False)
        
        self.center_canvas = ctk.CTkScrollableFrame(self.center_frame, fg_color="transparent")
        self.center_canvas.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._show_empty_state()

    def _show_empty_state(self):
        self._clear_center()
            
        empty_frame = ctk.CTkFrame(self.center_canvas, fg_color="transparent")
        empty_frame.pack(expand=True, pady=80)
        self._center_widgets.append(empty_frame)
        
        ctk.CTkLabel(empty_frame, text="No roadmap selected.", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(pady=(0, 10))
        ctk.CTkLabel(empty_frame, text="Select an existing plan from the left panel, or generate a new one below.\nHere are some examples:", font=Fonts.BODY, text_color=Colors.TEXT_MUTED, justify="center").pack(pady=(0, 30))
        
        examples = [
            ("Learn Python in 30 Days", "Study"),
            ("Build an AI Portfolio Project", "Project"),
            ("Become a Data Analyst", "Work"),
            ("Launch a Startup", "Project")
        ]
        
        examples_grid = ctk.CTkFrame(empty_frame, fg_color="transparent")
        examples_grid.pack()
        
        for i, (ex, ptype) in enumerate(examples):
            btn = ctk.CTkButton(
                examples_grid, text=ex, font=Fonts.BODY,
                fg_color=Colors.CARD_FLOATING, hover_color=Colors.ACCENT_SUBTLE,
                border_width=1, border_color=Colors.BORDER_SUBTLE, corner_radius=12,
                command=lambda e=ex, t=ptype: self._fill_and_generate(e, t)
            )
            btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")

    def _render_workspace(self, plan):
        self._clear_center()
        work = ctk.CTkFrame(self.center_canvas, fg_color="transparent")
        work.pack(fill="both", expand=True)
        self._center_widgets.append(work)
        self._workspace = work

        timeline = json.loads(plan.get("timeline_json", "[]"))
        steps = json.loads(plan.get("steps_json", "[]"))
        resources = json.loads(plan.get("resources_json", "[]"))
        insights_str = plan.get("insights_json")
        insights = json.loads(insights_str) if insights_str else {}
            
        # Header
        header_frame = ctk.CTkFrame(self._workspace, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header_frame, text=plan["title"], font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, anchor="w", wraplength=450, justify="left").pack(side="left", fill="x", expand=True)
        
        # Actions
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right")
        ctk.CTkButton(actions_frame, text="🗑 Delete", font=Fonts.SMALL_BOLD, fg_color="transparent", text_color="#E74C3C", hover_color=Colors.CARD_FLOATING, width=60, command=lambda: self._delete_plan(plan["id"])).pack(side="right", padx=5)
        
        # --- PLAN SNAPSHOT ---
        snapshot_frame = ctk.CTkFrame(self._workspace, fg_color="transparent")
        snapshot_frame.pack(fill="x", pady=(0, 20))
        
        badges = [
            (plan['plan_type'], Colors.CARD_FLOATING),
            (plan['status'], Colors.CARD_FLOATING),
            (insights.get("difficulty", "Moderate"), Colors.ACCENT_SUBTLE),
            (insights.get("duration", "N/A"), Colors.CARD_FLOATING),
            (insights.get("daily_time", "N/A"), Colors.CARD_FLOATING),
            (f"Success Prob: {insights.get('success_probability', 'N/A')}", Colors.CARD_FLOATING),
            (f"{len(timeline)} Milestones", Colors.CARD_FLOATING),
            (f"{len(resources)} Resources", Colors.CARD_FLOATING)
        ]
        
        wrap_frame = ctk.CTkFrame(snapshot_frame, fg_color="transparent")
        wrap_frame.pack(fill="x")
        # simple wrap emulation
        row = 0
        col = 0
        for text, bg in badges:
            ctk.CTkLabel(wrap_frame, text=f" {text} ", font=Fonts.SMALL_BOLD, fg_color=bg, corner_radius=8).grid(row=row, column=col, padx=(0, 10), pady=(0, 5), sticky="w")
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        # Description
        desc = plan.get("description", "")
        if desc:
            ctk.CTkLabel(self._workspace, text=desc, font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY, anchor="w", justify="left", wraplength=450).pack(fill="x", pady=(0, 20))
            
        # Aurex Recommendation
        tips = insights.get("tips", [])
        if tips:
            rec_frame = ctk.CTkFrame(self._workspace, fg_color=Colors.ACCENT_SUBTLE, corner_radius=12, border_width=1, border_color=Colors.BORDER_ACTIVE)
            rec_frame.pack(fill="x", pady=(0, 20))
            inner_rec = ctk.CTkFrame(rec_frame, fg_color="transparent")
            inner_rec.pack(fill="x", padx=15, pady=15)
            ctk.CTkLabel(inner_rec, text="✨ Aurex Recommendation", font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_PRIMARY).pack(anchor="w", pady=(0, 5))
            for tip in tips:
                ctk.CTkLabel(inner_rec, text=f"• {tip}", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, justify="left", wraplength=450, anchor="w").pack(fill="x", pady=2)

        # Expandable Insight Panels
        self._build_expandable_panels(insights)
        
        # Timeline
        if timeline:
            ctk.CTkLabel(self._workspace, text="TIMELINE OVERVIEW", font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 10))
            tl_frame = ctk.CTkFrame(self._workspace, fg_color=Colors.CARD_FLOATING, corner_radius=12)
            tl_frame.pack(fill="x", pady=(0, 30))
            
            inner_tl = ctk.CTkScrollableFrame(tl_frame, fg_color="transparent", orientation="horizontal", height=50)
            inner_tl.pack(fill="x", padx=15, pady=5)
            
            for i, phase in enumerate(timeline):
                ctk.CTkLabel(inner_tl, text=phase, font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=(0, 10))
                if i < len(timeline) - 1:
                    ctk.CTkLabel(inner_tl, text="➞", font=Fonts.BODY, text_color=Colors.BORDER_ACTIVE).pack(side="left", padx=(0, 10))

        # Steps
        if steps:
            ctk.CTkLabel(self._workspace, text="STRUCTURED STEPS", font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 10))
            
            for step in steps:
                step_card = ctk.CTkFrame(self._workspace, fg_color=Colors.CARD_FLOATING, corner_radius=12, border_width=1, border_color=Colors.BORDER_SUBTLE)
                step_card.pack(fill="x", pady=6)
                
                header = ctk.CTkFrame(step_card, fg_color="transparent")
                header.pack(fill="x", padx=15, pady=10)
                
                # Checkbox
                ctk.CTkCheckBox(header, text="", width=24).pack(side="left")
                
                # Title
                ctk.CTkLabel(header, text=step.get("duration", ""), font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_PRIMARY).pack(side="left", padx=(0, 10))
                ctk.CTkLabel(header, text=step.get("title", ""), font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, wraplength=350, justify="left").pack(side="left")
                
                # Details
                details_frame = ctk.CTkFrame(step_card, fg_color="transparent")
                details_frame.pack(fill="x", padx=(45, 15), pady=(0, 15))
                ctk.CTkLabel(details_frame, text=step.get("details", ""), font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY, justify="left", wraplength=450).pack(anchor="w")

    def _build_expandable_panels(self, insights):
        prereqs = insights.get("prerequisites", [])
        if prereqs:
            self._create_expandable_panel("Prerequisites", lambda f: self._build_bullet_list(f, prereqs))
            
        tools = insights.get("recommended_tools", [])
        if tools:
            self._create_expandable_panel("Recommended Tools", lambda f: self._build_tools_list(f, tools))
            
        mistakes = insights.get("common_mistakes", [])
        if mistakes:
            self._create_expandable_panel("Common Mistakes", lambda f: self._build_bullet_list(f, mistakes, color=Colors.CHART_RED))
            
        metrics = insights.get("success_metrics", [])
        if metrics:
            self._create_expandable_panel("Success Checklist", lambda f: self._build_checkbox_list(f, metrics))

    def _create_expandable_panel(self, title, content_builder):
        panel = ctk.CTkFrame(getattr(self, '_workspace', self.center_canvas), fg_color=Colors.CARD_FLOATING, corner_radius=12, border_width=1, border_color=Colors.BORDER_SUBTLE)
        panel.pack(fill="x", pady=6)
        
        header = ctk.CTkFrame(panel, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=10)
        
        lbl_title = ctk.CTkLabel(header, text=title, font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY)
        lbl_title.pack(side="left")
        
        lbl_icon = ctk.CTkLabel(header, text="▼", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_MUTED)
        lbl_icon.pack(side="right")
        
        content_frame = ctk.CTkFrame(panel, fg_color="transparent")
        
        is_built = [False]
        def toggle(e=None):
            if not is_built[0]:
                content_builder(content_frame)
                is_built[0] = True
            
            if content_frame.winfo_ismapped():
                content_frame.pack_forget()
                lbl_icon.configure(text="▼")
            else:
                content_frame.pack(fill="x", padx=15, pady=(0, 15))
                lbl_icon.configure(text="▲")
                
        for w in [panel, header, lbl_title, lbl_icon]:
            w.bind("<Button-1>", toggle)
            w.configure(cursor="hand2")

    def _build_bullet_list(self, frame, items, color=Colors.TEXT_SECONDARY):
        for item in items:
            ctk.CTkLabel(frame, text=f"• {item}", font=Fonts.BODY, text_color=color, justify="left", wraplength=450, anchor="w").pack(fill="x", pady=2)

    def _build_checkbox_list(self, frame, items):
        for item in items:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkCheckBox(row, text="", width=24).pack(side="left")
            ctk.CTkLabel(row, text=item, font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY, justify="left", wraplength=450, anchor="w").pack(side="left", fill="x")

    def _build_tools_list(self, frame, tools):
        for tool in tools:
            title = tool if isinstance(tool, str) else tool.get("title", "Tool")
            btn = ctk.CTkButton(
                frame, text=title, font=Fonts.BODY, height=28,
                fg_color="transparent", hover_color=Colors.CARD_HOVER,
                border_width=1, border_color=Colors.BORDER_SUBTLE, text_color=Colors.ACCENT_PRIMARY,
                command=lambda q=title: self._open_search(q)
            )
            btn.pack(side="left", padx=5, pady=5)


    # --- RIGHT PANEL (RESOURCES) ---

    def _build_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=20, border_width=1, border_color=Colors.BORDER_SUBTLE)
        self.right_frame.grid(row=1, column=2, sticky="nsew", padx=(0, 10), pady=(5, 10))
        self.right_frame.pack_propagate(False)
        
        header = ctk.CTkFrame(self.right_frame, fg_color="transparent", height=50)
        header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(header, text="Resources", font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        
        self.resources_canvas = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        self.resources_canvas.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._show_empty_resources()

    def _show_empty_resources(self):
        self._clear_resources()
        lbl = ctk.CTkLabel(
            self.resources_canvas, 
            text="Resources will appear automatically after roadmap generation.", 
            font=Fonts.BODY, text_color=Colors.TEXT_MUTED, wraplength=250, justify="center"
        )
        lbl.pack(pady=60)
        self._resource_widgets.append(lbl)

    def _render_resources(self, resources_json):
        self._clear_resources()
        resources = json.loads(resources_json) if resources_json else []
        
        if not resources:
            self._show_empty_resources()
            return
            
        for res in resources:
            card = ctk.CTkFrame(self.resources_canvas, fg_color=Colors.CARD_FLOATING, corner_radius=12, border_width=1, border_color=Colors.BORDER_SUBTLE)
            card.pack(fill="x", pady=6)
            self._resource_widgets.append(card)
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=12)
            
            ctk.CTkLabel(inner, text=res.get("title", "Resource"), font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, wraplength=220, justify="left", anchor="w").pack(fill="x")
            ctk.CTkLabel(inner, text=res.get("type", "Link"), font=Fonts.CAPTION, text_color=Colors.BORDER_ACTIVE, anchor="w").pack(fill="x", pady=(2, 8))
            
            btn = ctk.CTkButton(
                inner, text="Open Browser ↗", font=Fonts.SMALL_BOLD, height=24,
                fg_color="transparent", hover_color=Colors.ACCENT_SUBTLE, border_width=1, border_color=Colors.ACCENT_PRIMARY, text_color=Colors.ACCENT_PRIMARY,
                command=lambda q=res.get("search_query", res.get("title", "")): self._open_search(q)
            )
            btn.pack(anchor="w")

    def _open_search(self, query):
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        webbrowser.open(url)

    # --- BOTTOM PANEL (INPUT) ---

    def _build_bottom_panel(self):
        self.bottom_frame = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=20, border_width=1, border_color=Colors.BORDER_SUBTLE, height=120)
        self.bottom_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=(0, 10))
        self.bottom_frame.pack_propagate(False)
        
        inner = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=15)
        
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(top_row, text="Describe your goal or request a plan:", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY).pack(side="left")
        
        self.plan_type_var = ctk.StringVar(value="Study")
        self.type_seg = ctk.CTkSegmentedButton(
            top_row, values=["Study", "Project", "Work", "Habit", "Custom"],
            variable=self.plan_type_var,
            selected_color=Colors.ACCENT_PRIMARY,
            selected_hover_color=Colors.ACCENT_HOVER,
            unselected_color=Colors.CARD_FLOATING,
            unselected_hover_color=Colors.CARD_HOVER,
            font=Fonts.SMALL
        )
        self.type_seg.pack(side="right")
        
        input_row = ctk.CTkFrame(inner, fg_color="transparent")
        input_row.pack(fill="x", expand=True)
        
        self.goal_entry = ctk.CTkEntry(
            input_row, placeholder_text="Describe your goal or request a plan...",
            height=Dims.ENTRY_HEIGHT + 10, font=Fonts.ENTRY,
            fg_color=Colors.INPUT_BG, border_color=Colors.INPUT_BORDER
        )
        self.goal_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.goal_entry.bind("<Return>", lambda e: self._trigger_generation())
        
        self.gen_btn = ctk.CTkButton(
            input_row, text="Generate Plan ✨", font=Fonts.BUTTON, height=Dims.ENTRY_HEIGHT + 10, width=160,
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
            command=self._trigger_generation
        )
        self.gen_btn.pack(side="right")

    # --- LOGIC ---

    def _fill_and_generate(self, goal_text, plan_type):
        self.goal_entry.delete(0, 'end')
        self.goal_entry.insert(0, goal_text)
        self.plan_type_var.set(plan_type)
        self._trigger_generation()

    def _clear_workspace(self):
        self.current_plan_id = None
        self._show_empty_state()
        self._show_empty_resources()
        self.goal_entry.delete(0, 'end')
        self._load_roadmaps_list()

    def _trigger_generation(self):
        goal = self.goal_entry.get().strip()
        if not goal: return
        
        ptype = self.plan_type_var.get()
        
        self.gen_btn.configure(state="disabled", text="Generating...")
        self._clear_center()
        loading = ctk.CTkLabel(self.center_canvas, text="Aurex AI is building your roadmap...", font=Fonts.HEADING, text_color=Colors.ACCENT_PRIMARY)
        loading.pack(pady=100)
        self._center_widgets.append(loading)
        
        threading.Thread(target=ai_service.generate_roadmap, args=(goal, ptype), daemon=True).start()

    def _on_roadmap_generated(self, payload):
        self.gen_btn.configure(state="normal", text="Generate Plan ✨")
        
        if not payload.get("success"):
            self._clear_center()
            err = ctk.CTkLabel(self.center_canvas, text=f"Failed to generate: {payload.get('error')}", text_color=Colors.CHART_RED)
            err.pack(pady=100)
            self._center_widgets.append(err)
            return
            
        data = payload.get("data", {})
        goal = payload.get("goal", "")
        plan_type = payload.get("plan_type", "Custom")
        
        # Save to database
        conn = get_connection()
        cursor = conn.cursor()
        
        timeline_json = json.dumps(data.get("timeline", []))
        steps_json = json.dumps(data.get("steps", []))
        resources_json = json.dumps(data.get("resources", []))
        
        # Extract insights
        insights = {
            "difficulty": data.get("difficulty", "Moderate"),
            "daily_time": data.get("daily_time", "Unknown"),
            "duration": data.get("duration", "Unknown"),
            "success_probability": data.get("success_probability", "Moderate"),
            "prerequisites": data.get("prerequisites", []),
            "tips": data.get("tips", []),
            "common_mistakes": data.get("common_mistakes", []),
            "recommended_tools": data.get("recommended_tools", []),
            "success_metrics": data.get("success_metrics", [])
        }
        insights_json = json.dumps(insights)
        
        cursor.execute('''
            INSERT INTO plans (user_id, title, description, goal, plan_type, status, timeline_json, steps_json, resources_json, insights_json)
            VALUES (?, ?, ?, ?, ?, 'New', ?, ?, ?, ?)
        ''', (self.user_id, data.get("title", "New Plan"), data.get("description", ""), goal, plan_type, timeline_json, steps_json, resources_json, insights_json))
        
        new_id = cursor.lastrowid
        
        # Save version
        cursor.execute('''
            INSERT INTO plan_versions (plan_id, version_number, roadmap_json)
            VALUES (?, 1, ?)
        ''', (new_id, json.dumps(data)))
        
        conn.commit()
        conn.close()
        
        self.goal_entry.delete(0, 'end')
        self._load_plan(new_id)

    def _load_plan(self, plan_id):
        self.current_plan_id = plan_id
        self._load_roadmaps_list() # refresh highlights
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plans WHERE id=?", (plan_id,))
        plan = cursor.fetchone()
        conn.close()
        
        if plan:
            self._render_workspace(dict(plan))
            self._render_resources(plan["resources_json"])
            
    def _delete_plan(self, plan_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM plan_versions WHERE plan_id=?", (plan_id,))
        cursor.execute("DELETE FROM plans WHERE id=?", (plan_id,))
        conn.commit()
        conn.close()
        
        if self.current_plan_id == plan_id:
            self._clear_workspace()
        else:
            self._load_roadmaps_list()
