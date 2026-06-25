from services.event_bus import bus

class GoalEngine:
    """Tracks long-term goals and milestone progress."""
    def __init__(self):
        self.active_goals = 0
        self.completed_goals = 0
        
        bus.subscribe("GOAL_UPDATED", self._on_goal_updated)
        
    def _on_goal_updated(self, payload):
        status = payload.get("status")
        if status == "COMPLETED":
            self.completed_goals += 1
            
    def get_goal_stats(self) -> dict:
        return {
            "active": self.active_goals,
            "completed": self.completed_goals
        }

goal_engine = GoalEngine()
