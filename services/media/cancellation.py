import threading
from services.media.exceptions import CancellationError

class CancellationManager:
    def __init__(self):
        self._cancellation_events = {}
        self._lock = threading.Lock()

    def register(self, source_id: int):
        with self._lock:
            self._cancellation_events[source_id] = threading.Event()

    def cancel(self, source_id: int):
        with self._lock:
            event = self._cancellation_events.get(source_id)
            if event:
                event.set()

    def check_cancelled(self, source_id: int):
        if source_id is None:
            return
        with self._lock:
            event = self._cancellation_events.get(source_id)
        if event and event.is_set():
            raise CancellationError("Analysis Cancelled")

    def unregister(self, source_id: int):
        with self._lock:
            if source_id in self._cancellation_events:
                del self._cancellation_events[source_id]

cancellation_manager = CancellationManager()
