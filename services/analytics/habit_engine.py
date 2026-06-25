from services.event_bus import bus

class HabitEngine:
    """Tracks habit streaks and daily completion."""
    def __init__(self):
        self.current_streak = 0
        
        bus.subscribe("HABIT_LOGGED", self._on_habit_logged)
        
    def _on_habit_logged(self, payload):
        # Future logic for streak calculation
        pass

    def get_habit_stats(self) -> dict:
        return {
            "current_streak": self.current_streak
        }

habit_engine = HabitEngine()
