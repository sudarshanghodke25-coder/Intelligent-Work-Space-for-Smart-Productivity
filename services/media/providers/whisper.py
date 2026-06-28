import os
import tempfile
from services.media.providers.base import TranscriptProvider
from services.media.cancellation import cancellation_manager

class WhisperProvider(TranscriptProvider):
    def __init__(self, model_size: str = "small"):
        self.model_size = model_size

    @property
    def name(self) -> str:
        return "whisper"

    def extract_transcript(self, video_id: str, url: str, source_id: int = None) -> str:
        cancellation_manager.check_cancelled(source_id)
        
        try:
            import yt_dlp
            from faster_whisper import WhisperModel
            
            print(f"[YT] Whisper Fallback Started for {video_id} using model '{self.model_size}'")
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path_tmpl = os.path.join(tmpdir, f'{video_id}.%(ext)s')
                
                # Download audio
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '128',
                    }],
                    'outtmpl': audio_path_tmpl,
                    'quiet': True,
                    'no_warnings': True,
                }
                
                print(f"[YT] Downloading audio for {video_id}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                cancellation_manager.check_cancelled(source_id)
                
                audio_file = os.path.join(tmpdir, f"{video_id}.mp3")
                if not os.path.exists(audio_file):
                    raise Exception("Audio download failed or file not found")
                
                print("[YT] Audio extracted. Running faster-whisper...")
                model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                segments, info = model.transcribe(audio_file, beam_size=5)
                
                transcript_text = []
                for segment in segments:
                    cancellation_manager.check_cancelled(source_id)
                    transcript_text.append(segment.text.strip())
                
                full_text = " ".join(transcript_text)
                
                if not full_text.strip():
                    raise Exception("Whisper transcribed empty text")
                
                print(f"[YT] Whisper Provider Success. Length: {len(full_text)}")
                return full_text
                
        except Exception as e:
            print(f"[YT] Whisper Provider Failed: {e}")
            raise Exception(f"Whisper fallback failed: {e}")
