class MediaPlugin:
    @property
    def name(self) -> str:
        raise NotImplementedError
        
    def can_handle(self, source: str) -> bool:
        """Return True if this plugin can handle the given URL or file path."""
        raise NotImplementedError
        
    def extract(self, source: str, source_id: int = None) -> dict:
        """
        Extract content from the source.
        Should return a dictionary with at least:
        {
            "transcript": "...",
            "duration": float,
            "title": str,
            "channel": str,
            "video_id": str,
            "extraction_method": str
        }
        """
        raise NotImplementedError
