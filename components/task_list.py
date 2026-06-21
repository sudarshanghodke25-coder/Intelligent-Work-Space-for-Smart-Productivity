"""
TaskList — Upcoming Tasks list widget with priority badges.
"""

import customtkinter as ctk
from theme import Colors, Fonts, blend_color
from database.database import get_connection
from services.event_bus import bus
from datetime import datetime

class TaskList(ctk.CTkFrame):
    """Scrollable list of tasks with checkbox, priority badge, and due date."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        bus.subscribe("TASKS_UPDATED", self._on_tasks_updated)
        self._load_data()

    def _on_tasks_updated(self, data):
        self._load_data()

    def _load_data(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        conn = get_connection()
        tasks_db = conn.execute("SELECT * FROM tasks WHERE status!='Completed' ORDER BY CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 3 ELSE 4 END, due_date ASC LIMIT 5").fetchall()
        conn.close()

        self.tasks = []
        for t in tasks_db:
            due = datetime.strptime(t["due_date"], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            diff = (due.date() - now.date()).days
            if diff == 0: date_str = "Today"
            elif diff == 1: date_str = "Tomorrow"
            elif diff == -1: date_str = "Yesterday"
            else: date_str = due.strftime("%b %d")

            color = Colors.PRIORITY_HIGH if t["priority"] == "High" else Colors.PRIORITY_MEDIUM if t["priority"] == "Medium" else Colors.PRIORITY_LOW

            self.tasks.append({
                "id": t["id"],
                "title": t["title"], "date": date_str, "priority": t["priority"],
                "color": color, "done": False
            })

        self._build()

    def _build(self):
        for task in self.tasks:
            row = ctk.CTkFrame(
                self.container, fg_color=Colors.GLASS_FILL_LIGHT if not task["done"] else "transparent",
                corner_radius=10, height=42
            )
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            # Checkbox circle
            check_color = Colors.ACCENT_PRIMARY if task["done"] else "transparent"
            check_border = Colors.ACCENT_PRIMARY if task["done"] else Colors.GLASS_BORDER_BRIGHT
            check = ctk.CTkFrame(
                row, width=18, height=18, corner_radius=9,
                fg_color=check_color, border_width=2, border_color=check_border
            )
            check.pack(side="left", padx=(10, 8), pady=12)

            # Check mark for completed tasks
            if task["done"]:
                ctk.CTkLabel(
                    check, text="✓", font=("Segoe UI", 9, "bold"),
                    text_color=Colors.TEXT_PRIMARY, fg_color="transparent"
                ).place(relx=0.5, rely=0.5, anchor="center")

            # Task title
            title_color = Colors.TEXT_MUTED if task["done"] else Colors.TEXT_PRIMARY
            title_lbl = ctk.CTkLabel(
                row, text=task["title"],
                font=Fonts.BODY, text_color=title_color, anchor="w"
            )
            title_lbl.pack(side="left", padx=(0, 8), expand=True, fill="x")

            # Due date
            ctk.CTkLabel(
                row, text=task["date"],
                font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED,
                width=55, anchor="e"
            ).pack(side="right", padx=(0, 8))

            # Priority badge
            badge = ctk.CTkLabel(
                row, text=task["priority"],
                font=Fonts.CAPTION, text_color=task["color"],
                fg_color=blend_color(task["color"], 0.12),
                corner_radius=8, width=55, height=20,
                anchor="center"
            )
            badge.pack(side="right", padx=(0, 6))

            # Interactive Bindings
            def make_handler(tid, r, c, t_lbl):
                def handler(event):
                    self._on_task_click(tid, r, c, t_lbl)
                return handler

            click_handler = make_handler(task["id"], row, check, title_lbl)
            check.bind("<Button-1>", click_handler)
            title_lbl.bind("<Button-1>", click_handler)
            check.configure(cursor="hand2")
            title_lbl.configure(cursor="hand2")

    def _on_task_click(self, task_id, row, check, title_lbl):
        # Update UI instantly
        check.configure(fg_color=Colors.ACCENT_PRIMARY, border_color=Colors.ACCENT_PRIMARY)
        ctk.CTkLabel(check, text="✓", font=("Segoe UI", 9, "bold"), text_color=Colors.TEXT_PRIMARY, fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")
        title_lbl.configure(text_color=Colors.TEXT_MUTED, font=(Fonts.BODY[0], Fonts.BODY[1], "overstrike"))
        row.configure(fg_color="transparent")

        import threading
        def _worker():
            conn = get_connection()
            conn.execute("UPDATE tasks SET status = 'Completed' WHERE id = ?", (task_id,))
            conn.commit()
            conn.close()
            bus.publish("COMPLETION_UPDATED", {})
            
        threading.Thread(target=_worker, daemon=True).start()
