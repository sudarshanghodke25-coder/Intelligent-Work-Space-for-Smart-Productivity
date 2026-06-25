from services.media.source_detector import SourceDetector
from services.media.plugins.youtube_plugin import YouTubePlugin
from services.media.plugins.local_media_plugin import LocalMediaPlugin
from services.media.plugins.github_plugin import GitHubPlugin
from services.media.plugins.vimeo_plugin import VimeoPlugin
from services.media.plugins.pdf_url_plugin import PdfUrlPlugin
from services.media.plugins.web_plugin import WebPlugin

class MediaOrchestrator:
    def __init__(self):
        self.plugins = [
            YouTubePlugin(),
            LocalMediaPlugin(),
            GitHubPlugin(),
            VimeoPlugin(),
            PdfUrlPlugin(),
            WebPlugin()
        ]
        
    def process(self, source: str, source_id: int = None) -> dict:
        print(f"[MediaOrchestrator] Processing source: {source}")
        
        plugin_name = SourceDetector.detect(source)
        print(f"[MediaOrchestrator] SourceDetector mapped to plugin: {plugin_name}")
        
        for plugin in self.plugins:
            if plugin.name == plugin_name:
                print(f"[MediaOrchestrator] Handing off to {plugin.__class__.__name__}")
                return plugin.extract(source, source_id)
                
        raise ValueError(f"No suitable media plugin found for source: {source}")

media_orchestrator = MediaOrchestrator()
