from services.event_bus import bus

class FocusEngine:
    """Tracks deep work sessions and focus time."""
    def __init__(self):
        self.total_focus_minutes = 0
        self.sessions_completed = 0
        
        bus.subscribe("FOCUS_SESSION_COMPLETED", self._on_session_completed)
        
    def _on_session_completed(self, payload):
        duration = payload.get("duration_minutes", 0)
        self.total_focus_minutes += duration
        self.sessions_completed += 1

    def get_focus_stats(self) -> dict:
        return {
            "total_minutes": self.total_focus_minutes,
            "total_hours": round(self.total_focus_minutes / 60, 1),
            "sessions": self.sessions_completed
        }

focus_engine = FocusEngine()
