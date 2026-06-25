from abc import ABC, abstractmethod

class TranscriptProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider (e.g., 'transcript_api', 'yt_dlp_subtitles', 'whisper')"""
        pass

    @abstractmethod
    def extract_transcript(self, video_id: str, url: str, source_id: int = None) -> str:
        """
        Extracts the transcript for the given video.
        Should check `cancellation_manager.check_cancelled(source_id)` periodically if long-running.
        Returns the transcript string.
        Raises an Exception if extraction fails.
        """
        pass
