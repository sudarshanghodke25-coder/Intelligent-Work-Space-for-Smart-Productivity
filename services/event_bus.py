import threading

class EventBus:
    """
    Synchronous and thread-safe asynchronous Publish/Subscribe event bus.
    Routes cross-thread events to the CustomTkinter main loop safely.
    """
    def __init__(self):
        self.subscribers = {}
        self.app = None

    def set_app(self, app):
        """Must be called at startup with the main ctk.CTk instance."""
        self.app = app

    def subscribe(self, event_type: str, callback: callable):
        """
        Subscribe to an event. 
        The callback MUST accept exactly one argument: data (which can be None).
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        if callback not in self.subscribers[event_type]:
            self.subscribers[event_type].append(callback)

    # Note the 4 spaces of indentation here! Now it belongs to the class.
    def publish(self, event_type: str, data=None):
        """
        Publish an event with optional payload data.
        """
        callbacks = self.subscribers.get(event_type, [])
        for callback in callbacks:
            if self.app:
                try:
                    self.app.after(0, lambda cb=callback, d=data: cb(d))
                except Exception as e:
                    print(f"[EventBus Error] Failed to marshal via .after(): {e}")
            else:
                print(f"[EventBus Warning] App context missing for event '{event_type}'. Executing synchronously.")
                callback(data)

# Global singleton
bus = EventBus()