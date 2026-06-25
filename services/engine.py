import threading
import time
from datetime import datetime, timedelta
from database.database import get_connection
from services.event_bus import bus

# 1. Background Tracker (Productivity & Project Time)
class FocusTracker:
    def __init__(self):
        self.is_running = False
        self.elapsed = 0
        self.thread = None

    def start(self):
        if self.is_running: return
        self.is_running = True
        self.elapsed = 0
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False

    def _run(self):
        while self.is_running:
            time.sleep(1)
            self.elapsed += 1
            # Publish cumulative elapsed time to update graphs/UI dynamically
            bus.publish("FOCUS_TICK", {"elapsed_seconds": self.elapsed})
            
            # Simulated db sync every 60 seconds (1 minute of focus logged)
            if self.elapsed % 60 == 0:
                self._log_focus(1) # Log 1 minute to db
                bus.publish("FOCUS_UPDATED") # Tell charts to reload

    def _log_focus(self, minutes):
        from authentication.session import current_session
        user_id = current_session.user_id or 0
        conn = get_connection()
        conn.execute("INSERT INTO focus_logs (user_id, tag, duration_minutes) VALUES (?, ?, ?)", (user_id, "Work", minutes))
        conn.commit()
        conn.close()

focus_tracker = FocusTracker()

# 2. Automated AI Parsing Widget (AI Reports)
def ai_parse_text(raw_text: str):
    """Asynchronous background task to parse raw text and recalculate completion."""
    def _parse():
        from authentication.session import current_session
        user_id = current_session.user_id or 0

        conn = get_connection()

        # Insert extracted task attributed to the real logged-in user
        title = f"Extracted: {raw_text[:15]}..." if len(raw_text) > 15 else f"Extracted: {raw_text}"
        conn.execute(
            "INSERT INTO tasks (user_id, title, priority, due_date, status) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, "Medium", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Completed")
        )
        conn.commit()

        # Calculate completion % for this user only
        total = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,)).fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status='Completed'", (user_id,)).fetchone()[0]

        completion_pct = (completed / total) * 100 if total > 0 else 0
        conn.close()

        # Emit reactivity events
        bus.publish("COMPLETION_UPDATED", {"percentage": completion_pct})
        bus.publish("TASKS_UPDATED")

    threading.Thread(target=_parse, daemon=True).start()

# 3. AI Suggestions Scanner (Background Thread)
class SuggestionScanner:
    def __init__(self):
        self.is_running = False
    
    def start(self):
        if self.is_running: return
        self.is_running = True
        threading.Thread(target=self._scan_loop, daemon=True).start()
        
    def stop(self):
        self.is_running = False
        
    def _scan_loop(self):
        while self.is_running:
            time.sleep(30)  # Scan every 30 seconds
            self._evaluate_rules()
            
    def _evaluate_rules(self):
        from authentication.session import current_session
        user_id = current_session.user_id or 0

        conn = get_connection()
        now = datetime.now()

        # Rule B: High priority task due within 24 hours
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND priority='High' AND status!='Completed'", (user_id,)
        ).fetchall()
        for t in tasks:
            due = datetime.strptime(t["due_date"], "%Y-%m-%d %H:%M:%S")
            if timedelta(0) < (due - now) < timedelta(hours=24):
                bus.publish("SUGGESTION_FIRED", {
                    "title": "Task Prioritization",
                    "message": f"High priority task '{t['title']}' is due within 24h!",
                    "type": "warning"
                })
                break  # Fire only one to avoid spam

        # Rule A: Gap block > 90 mins between schedule elements
        today_str = now.strftime("%Y-%m-%d 00:00:00")
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
        schedules = conn.execute(
            "SELECT * FROM schedules WHERE user_id = ? AND start_time >= ? AND start_time < ? ORDER BY start_time",
            (user_id, today_str, tomorrow_str)
        ).fetchall()

        for i in range(len(schedules) - 1):
            end_current = datetime.strptime(schedules[i]["end_time"], "%Y-%m-%d %H:%M:%S")
            start_next = datetime.strptime(schedules[i+1]["start_time"], "%Y-%m-%d %H:%M:%S")
            gap = (start_next - end_current).total_seconds() / 60.0
            if gap > 90:
                bus.publish("SUGGESTION_FIRED", {
                    "title": "Focus Block Recommended",
                    "message": f"You have a {int(gap)} min gap at {end_current.strftime('%H:%M')}. Ideal for deep work.",
                    "type": "suggestion"
                })
                break

        conn.close()

suggestion_scanner = SuggestionScanner()
