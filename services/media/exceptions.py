class TranscriptNotFoundError(Exception):
    """Raised when no transcript can be found or generated for the video."""
    pass

class AudioExtractionError(Exception):
    """Raised when yt-dlp fails to extract audio."""
    pass

class WhisperError(Exception):
    """Raised when faster-whisper fails to transcribe the audio."""
    pass

class YoutubeDownloadError(Exception):
    """Raised when yt-dlp fails to download metadata or video info."""
    pass

class DependencyMissingError(Exception):
    """Raised when a required python package is missing."""
    pass

class FFmpegMissingError(Exception):
    """Raised when ffmpeg is not found in the system PATH."""
    pass

class CancellationError(Exception):
    """Raised when the user cancels the analysis."""
    pass
