from services.event_bus import bus

class ProductivityEngine:
    """Tracks task completion metrics and basic productivity score."""
    def __init__(self):
        self.tasks_created = 0
        self.tasks_completed = 0
        
        # Subscribe to future real events
        bus.subscribe("TASK_CREATED", self._on_task_created)
        bus.subscribe("TASK_COMPLETED", self._on_task_completed)
        
    def _on_task_created(self, payload):
        self.tasks_created += 1
        
    def _on_task_completed(self, payload):
        self.tasks_completed += 1
        
    def get_completion_rate(self) -> float:
        if self.tasks_created == 0:
            return 0.0
        return (self.tasks_completed / self.tasks_created) * 100

productivity_engine = ProductivityEngine()
