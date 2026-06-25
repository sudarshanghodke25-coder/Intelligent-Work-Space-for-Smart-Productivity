import importlib
import shutil
from services.media.exceptions import DependencyMissingError, FFmpegMissingError

class DependencyManager:
    @staticmethod
    def check_dependencies():
        """
        Checks if required dependencies for the YouTube pipeline are installed.
        Raises DependencyMissingError or FFmpegMissingError with actionable instructions.
        """
        # Check ffmpeg first as yt-dlp and whisper depend on it for audio processing
        if not shutil.which("ffmpeg"):
            raise FFmpegMissingError(
                "FFmpeg Required. Install FFmpeg and add it to your system PATH."
            )

        required_packages = {
            "yt_dlp": "yt-dlp",
            "youtube_transcript_api": "youtube-transcript-api",
            "faster_whisper": "faster-whisper",
            "docx": "python-docx",
            "sentence_transformers": "sentence-transformers"
        }

        missing = []
        for module, pip_name in required_packages.items():
            try:
                importlib.import_module(module)
            except ImportError:
                missing.append(pip_name)

        if missing:
            raise DependencyMissingError(
                f"Missing required packages: {', '.join(missing)}. "
                f"Run: pip install {' '.join(missing)}"
            )

dependency_manager = DependencyManager()
