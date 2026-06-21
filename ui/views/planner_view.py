import customtkinter as ctk
import threading
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from database.database import get_connection
from services.event_bus import bus
from datetime import datetime
from services.ai_service import ai_service

class PlannerView(ctk.CTkFrame):
    """Planner View for scheduling blocks of time."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)

        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        ctk.CTkLabel(
            header, text="📋 AI Planner", 
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left", fill="x")

        self.card = GlassCard(self, title="Schedule Event")
        self.card.pack(fill="x", padx=4, pady=10)
        
        self._build_form()
        
        bus.subscribe("NLP_SCHEDULE_PARSED", self._on_ai_parsed)
        
    def _build_form(self):
        # --- AI Magic Input ---
        ai_frame = ctk.CTkFrame(self.card.content, fg_color="transparent")
        ai_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(ai_frame, text="✨ Ask AI to Schedule", font=Fonts.BODY_BOLD, text_color=Colors.ACCENT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 4))
        
        input_container = ctk.CTkFrame(ai_frame, fg_color="transparent")
        input_container.pack(fill="x")
        
        self.ai_entry = ctk.CTkEntry(input_container, placeholder_text="e.g., Schedule a team standup tomorrow from 10 AM to 11 AM...", height=Dims.ENTRY_HEIGHT, font=Fonts.ENTRY)
        self.ai_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ai_entry.bind("<Return>", lambda e: self._process_ai_schedule())
        
        self.ai_btn = ctk.CTkButton(
            input_container, text="Generate", font=Fonts.BUTTON, width=80,
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
            height=Dims.ENTRY_HEIGHT, command=self._process_ai_schedule
        )
        self.ai_btn.pack(side="right")
        
        # Divider
        div = ctk.CTkFrame(self.card.content, height=1, fg_color=Colors.GLASS_BORDER)
        div.pack(fill="x", pady=(0, 20))

        # --- Manual Fallback Form ---
        
        # Event Name
        ctk.CTkLabel(self.card.content, text="Event Name", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 4))
        self.name_entry = ctk.CTkEntry(self.card.content, placeholder_text="Enter event description...", height=Dims.ENTRY_HEIGHT, font=Fonts.ENTRY)
        self.name_entry.pack(fill="x", pady=(0, 16))
        
        # Time Frame
        time_frame = ctk.CTkFrame(self.card.content, fg_color="transparent")
        time_frame.pack(fill="x", pady=(0, 16))
        
        start_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
        start_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(start_frame, text="Start Time (YYYY-MM-DD HH:MM)", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 4))
        self.start_entry = ctk.CTkEntry(start_frame, placeholder_text="e.g. 2026-06-25 09:00", height=Dims.ENTRY_HEIGHT, font=Fonts.ENTRY)
        self.start_entry.pack(fill="x")
        
        end_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
        end_frame.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ctk.CTkLabel(end_frame, text="End Time (YYYY-MM-DD HH:MM)", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 4))
        self.end_entry = ctk.CTkEntry(end_frame, placeholder_text="e.g. 2026-06-25 10:30", height=Dims.ENTRY_HEIGHT, font=Fonts.ENTRY)
        self.end_entry.pack(fill="x")
        
        # Category Tags
        ctk.CTkLabel(self.card.content, text="Category", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(0, 4))
        self.cat_var = ctk.StringVar(value="Work")
        self.cat_seg = ctk.CTkSegmentedButton(
            self.card.content, values=["Work", "Meeting", "Personal", "Break"],
            variable=self.cat_var,
            selected_color=Colors.ACCENT_PRIMARY,
            selected_hover_color=Colors.ACCENT_HOVER,
            unselected_color=Colors.GLASS_FILL_LIGHT,
            unselected_hover_color=Colors.GLASS_FILL_HOVER,
            font=Fonts.BODY
        )
        self.cat_seg.pack(fill="x", pady=(0, 24))
        
        # Save Button
        self.save_btn = ctk.CTkButton(
            self.card.content, text="Schedule Event", font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
            height=Dims.BTN_HEIGHT, command=self._save_event
        )
        self.save_btn.pack(anchor="e")

        self.feedback = ctk.CTkLabel(self.card.content, text="", font=Fonts.SMALL, text_color=Colors.TEXT_DIM, anchor="w")
        self.feedback.pack(fill="x", pady=(8, 0))

    def _process_ai_schedule(self):
        user_input = self.ai_entry.get().strip()
        if not user_input: return
        
        self.ai_btn.configure(state="disabled", text="Parsing timeline...")
        self.feedback.configure(text="")
        
        current_time = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
        threading.Thread(target=ai_service.parse_schedule_intent, args=(user_input, current_time), daemon=True).start()

    def _on_ai_parsed(self, payload):
        self.ai_btn.configure(state="normal", text="Generate")
        
        if not payload.get("success"):
            self.feedback.configure(text=f"AI Parse Failed: {payload.get('error')}", text_color=Colors.CHART_RED)
            return
            
        data = payload.get("data", {})
        
        self.ai_entry.delete(0, 'end')
        
        # Auto-fill
        self.name_entry.delete(0, 'end')
        self.name_entry.insert(0, data.get("event_name", ""))
        
        self.start_entry.delete(0, 'end')
        self.start_entry.insert(0, data.get("start_time", ""))
        
        self.end_entry.delete(0, 'end')
        self.end_entry.insert(0, data.get("end_time", ""))
        
        cat = data.get("category", "Work")
        if cat in ["Work", "Meeting", "Personal", "Break"]:
            self.cat_var.set(cat)
            
        # Automatically commit to database
        self._save_event()

    def _set_error_border(self, widget):
        widget.configure(border_color=Colors.CHART_RED)
        self.after(4000, lambda: widget.configure(border_color=Colors.ENTRY_BORDER))

    def _save_event(self):
        title = self.name_entry.get().strip()
        start_str = self.start_entry.get().strip()
        end_str = self.end_entry.get().strip()
        category = self.cat_var.get()
        
        if not title:
            self._set_error_border(self.name_entry)
            return
            
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        except ValueError:
            self._set_error_border(self.start_entry)
            return
            
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
        except ValueError:
            self._set_error_border(self.end_entry)
            return
            
        start_fmt = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_fmt = end_date.strftime("%Y-%m-%d %H:%M:%S")
        user_id = 1 
        
        # Synchronously save to DB
        conn = get_connection()
        conn.execute("INSERT INTO schedules (user_id, title, category, start_time, end_time) VALUES (?, ?, ?, ?, ?)",
                     (user_id, title, category, start_fmt, end_fmt))
        conn.commit()
        conn.close()
        
        self.feedback.configure(text="Event scheduled successfully!", text_color=Colors.CHART_GREEN)
        self.after(4000, lambda: self.feedback.configure(text=""))
        
        self.name_entry.delete(0, 'end')
        self.start_entry.delete(0, 'end')
        self.end_entry.delete(0, 'end')
        
        # Broadcast via EventBus
        bus.publish("SCHEDULE_UPDATED", {"title": title, "category": category})
