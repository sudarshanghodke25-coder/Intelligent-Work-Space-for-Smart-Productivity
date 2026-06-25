import os
import re

class SourceDetector:
    @staticmethod
    def detect(source: str) -> str:
        """Returns the identifier of the plugin that should handle this source."""
        source_lower = source.lower()
        
        # Check if local file
        if os.path.exists(source) or source_lower.startswith("file://"):
            if source_lower.endswith((".mp4", ".mp3", ".wav", ".m4a", ".mkv", ".mov")):
                return "local_media"
                
        # Check if YouTube
        youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        if re.match(youtube_regex, source):
            return "youtube"
            
        # Check GitHub
        if "github.com/" in source_lower:
            return "github"
            
        # Check Vimeo
        if "vimeo.com/" in source_lower:
            return "vimeo"
            
        # Check PDF URL
        if source_lower.startswith("http") and source_lower.endswith(".pdf"):
            return "pdf_url"
            
        # Check general Web URL
        if source_lower.startswith("http://") or source_lower.startswith("https://"):
            return "web"
            
        return "unknown"
