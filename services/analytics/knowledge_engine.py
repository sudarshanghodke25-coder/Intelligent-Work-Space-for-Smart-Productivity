from services.event_bus import bus

class KnowledgeEngine:
    """Tracks intelligence ingestion metrics."""
    def __init__(self):
        self.documents_analyzed = 0
        
        bus.subscribe("KNOWLEDGE_ADDED", self._on_knowledge_added)
        bus.subscribe("ANALYSIS_COMPLETED", self._on_analysis_completed)
        
    def _on_knowledge_added(self, payload):
        self.documents_analyzed += 1
        
    def _on_analysis_completed(self, payload):
        if payload.get("success"):
            self.documents_analyzed += 1

    def get_knowledge_stats(self) -> dict:
        return {
            "documents_analyzed": self.documents_analyzed
        }

knowledge_engine = KnowledgeEngine()
