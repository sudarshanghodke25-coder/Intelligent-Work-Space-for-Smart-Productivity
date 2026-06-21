"""
ScheduleList — Today's Schedule timeline widget.
"""

import customtkinter as ctk
from theme import Colors, Fonts, blend_color
from database.database import get_connection
from services.event_bus import bus
from datetime import datetime, timedelta

class ScheduleList(ctk.CTkFrame):
    """Timeline showing chronological events with category tags."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        bus.subscribe("SCHEDULE_UPDATED", self._on_schedule_updated)
        self._load_data()

    def _on_schedule_updated(self, data):
        self._load_data()

    def _load_data(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        conn = get_connection()
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d 00:00:00")
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
        sched_db = conn.execute("SELECT * FROM schedules WHERE start_time >= ? AND start_time < ? ORDER BY start_time ASC LIMIT 6", (today_str, tomorrow_str)).fetchall()
        conn.close()

        self.events = []
        for s in sched_db:
            st = datetime.strptime(s["start_time"], "%Y-%m-%d %H:%M:%S")
            time_str = st.strftime("%H:%M")
            color = Colors.TAG_WORK if s["category"] == "Work" else Colors.TAG_MEETING if s["category"] == "Meeting" else Colors.TAG_PERSONAL
            self.events.append({"time": time_str, "title": s["title"], "tag": s["category"], "color": color})
            
        self._build()

    def _build(self):
        for i, ev in enumerate(self.events):
            row = ctk.CTkFrame(self.container, fg_color="transparent", height=36)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            # Timeline dot and line
            dot_frame = ctk.CTkFrame(row, fg_color="transparent", width=24)
            dot_frame.pack(side="left")
            dot_frame.pack_propagate(False)

            dot = ctk.CTkFrame(dot_frame, width=8, height=8, corner_radius=4,
                               fg_color=ev["color"])
            dot.place(relx=0.5, rely=0.5, anchor="center")

            # Time
            ctk.CTkLabel(
                row, text=ev["time"],
                font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY,
                width=48, anchor="w"
            ).pack(side="left", padx=(4, 8))

            # Title
            ctk.CTkLabel(
                row, text=ev["title"],
                font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY,
                anchor="w"
            ).pack(side="left", padx=(0, 8), expand=True, fill="x")

            # Category tag capsule
            tag = ctk.CTkLabel(
                row, text=ev["tag"],
                font=Fonts.CAPTION, text_color=ev["color"],
                fg_color=blend_color(ev["color"], 0.12),  # 12% opacity simulated
                corner_radius=8,
                width=60, height=22,
                anchor="center"
            )
            tag.pack(side="right", padx=(4, 0))
