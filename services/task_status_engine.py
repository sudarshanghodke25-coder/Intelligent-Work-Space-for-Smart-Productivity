import threading
import time
from datetime import datetime
from database.database import get_connection
from services.event_bus import bus

class TaskStatusEngine:
    def __init__(self):
        self.is_running = False

    def start(self):
        if self.is_running: return
        self.is_running = True
        threading.Thread(target=self._scan_loop, daemon=True).start()
        
    def stop(self):
        self.is_running = False

    def evaluate_all(self):
        """Runs the rules engine on all tasks in the database."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # We don't touch already Completed tasks
        tasks = cursor.execute("SELECT id, due_date, status FROM tasks WHERE status != 'Completed'").fetchall()
        
        today_date = datetime.now().date()
        updates_made = 0
        
        for task in tasks:
            task_id = task["id"]
            due_str = task["due_date"]
            current_status = task["status"]
            
            new_status = "Upcoming"
            
            if due_str:
                try:
                    due_date = datetime.strptime(due_str[:10], "%Y-%m-%d").date()
                    if due_date < today_date:
                        new_status = "Overdue"
                    elif due_date == today_date:
                        new_status = "Today"
                except ValueError:
                    pass # Keep as Upcoming if format is invalid
            
            if new_status != current_status:
                cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
                updates_made += 1
                
        if updates_made > 0:
            conn.commit()
            # Inform UI
            bus.publish("TASKS_UPDATED", {"reason": "status_engine"})
            
        conn.close()

    def _scan_loop(self):
        while self.is_running:
            self.evaluate_all()
            time.sleep(60 * 5) # Check every 5 minutes

task_status_engine = TaskStatusEngine()
