import os
import time
import subprocess
from services.media.plugins.base import MediaPlugin
from services.media.transcription.engine import TranscriptionProviderManager

class LocalMediaPlugin(MediaPlugin):
    @property
    def name(self) -> str:
        return "local_media"

    def can_handle(self, source: str) -> bool:
        source_lower = source.lower()
        if os.path.exists(source) or source_lower.startswith("file://"):
            return source_lower.endswith((".mp4", ".mp3", ".wav", ".m4a", ".mkv", ".mov"))
        return False

    def _get_duration(self, file_path: str) -> float:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of",
                 "default=noprint_wrappers=1:nokey=1", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            return float(result.stdout)
        except Exception:
            return 0.0

    def _extract_audio(self, file_path: str) -> str:
        # If it's already an audio file, just use it, but to be safe we can always convert
        # to a standard 16kHz wav for whisper
        import tempfile
        temp_dir = tempfile.gettempdir()
        base_name = os.path.basename(file_path).split('.')[0]
        out_path = os.path.join(temp_dir, f"{base_name}_extracted.wav")
        
        print(f"[LocalMediaPlugin] Extracting audio from {file_path} to {out_path}")
        subprocess.run([
            "ffmpeg", "-y", "-i", file_path, 
            "-vn", "-acodec", "pcm_s16le", 
            "-ar", "16000", "-ac", "1", 
            out_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return out_path

    def extract(self, source: str, source_id: int = None) -> dict:
        if source.startswith("file://"):
            source = source[7:]
            
        if not os.path.exists(source):
            raise FileNotFoundError(f"Local file not found: {source}")
            
        start_time = time.time()
        
        # 1. Get Duration
        duration = self._get_duration(source)
        
        # 2. Extract Audio
        audio_path = self._extract_audio(source)
        
        # 3. Transcribe using Hybrid Engine
        try:
            manager = TranscriptionProviderManager()
            provider = manager.get_provider(duration)
            transcript = provider.transcribe(audio_path)
            method = provider.__class__.__name__
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
        processing_time = time.time() - start_time
        title = os.path.basename(source)
        
        return {
            "transcript": transcript,
            "duration": duration,
            "title": title,
            "channel": "Local System",
            "video_id": title,
            "extraction_method": method,
            "processing_time": processing_time
        }
