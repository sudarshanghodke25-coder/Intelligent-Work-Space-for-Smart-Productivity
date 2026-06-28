"""DEPRECATED
This file is deprecated and will be removed in a future release.
Please use the new plugin architecture in `services/media/plugins/` and `services/media/orchestrator.py` instead.
"""
from typing import Dict, Any
from services.youtube.dependency_manager import dependency_manager
from services.youtube.cancellation import cancellation_manager
from services.youtube.exceptions import TranscriptNotFoundError, YoutubeDownloadError

from services.youtube.providers.transcript_api import YouTubeTranscriptProvider
from services.youtube.providers.yt_dlp import YtDlpSubtitleProvider
from services.youtube.providers.whisper import WhisperProvider

class TranscriptProviderManager:
    def __init__(self):
        self.providers = [
            YouTubeTranscriptProvider(),
            YtDlpSubtitleProvider(),
            WhisperProvider(model_size="small")  # Default model, can be made configurable
        ]

    def extract(self, url: str, source_id: int = None) -> Dict[str, Any]:
        """
        Main entry point for extracting YouTube content.
        Returns a dict: {video_id, title, channel, duration, transcript, extraction_method}
        """
        # 1. Dependency Check
        dependency_manager.check_dependencies()
        cancellation_manager.check_cancelled(source_id)

        # 2. Extract Metadata via yt-dlp
        print(f"[YT] Extracting metadata for {url}")
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False, # Need full metadata for duration etc
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            raise YoutubeDownloadError(f"Failed to fetch metadata: {e}")

        video_id = info.get('id')
        if not video_id:
            raise YoutubeDownloadError("Could not extract video_id from metadata")

        # --- Cache Lookup ---
        from database.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cached = cursor.execute(
            "SELECT * FROM knowledge_sources WHERE video_id = ? AND status = 'COMPLETED' LIMIT 1", 
            (video_id,)
        ).fetchone()
        conn.close()

        if cached and cached["transcript"]:
            print(f"[YT] Cache Hit for video {video_id}. Returning cached transcript.")
            return {
                "video_id": video_id,
                "title": cached["title"],
                "channel": cached["channel"],
                "duration": info.get('duration', 0),
                "description": info.get('description', ''),
                "transcript": cached["transcript"],
                "extraction_method": cached["extraction_method"] or "cached"
            }
        # --------------------

        metadata = {
            "video_id": video_id,
            "title": info.get('title', 'Unknown Title'),
            "channel": info.get('uploader', 'Unknown Channel'),
            "duration": info.get('duration', 0),
            "description": info.get('description', ''),
        }
        
        print(f"[YT] Metadata Retrieved: {metadata['title']} by {metadata['channel']}")

        # 3. Provider Chain Execution
        best_transcript = None
        successful_provider = None
        
        for provider in self.providers:
            cancellation_manager.check_cancelled(source_id)
            try:
                print(f"[YT] Attempting extraction with {provider.name}")
                transcript = provider.extract_transcript(video_id, url, source_id)
                if transcript and len(transcript.strip()) > 0:
                    best_transcript = transcript
                    successful_provider = provider.name
                    print(f"[YT] Extraction Method: {successful_provider}")
                    break
            except Exception as e:
                print(f"[YT] Provider {provider.name} failed. Moving to next. Error: {str(e)}")
                continue

        if not best_transcript:
            raise TranscriptNotFoundError("All transcript providers failed. Content extraction failed.")

        return {
            **metadata,
            "transcript": best_transcript,
            "extraction_method": successful_provider
        }

provider_manager = TranscriptProviderManager()
