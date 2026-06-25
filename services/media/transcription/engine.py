import os
from services.api_service import aurex_api

class TranscriptionProvider:
    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError

class FasterWhisperProvider(TranscriptionProvider):
    def transcribe(self, audio_path: str) -> str:
        from faster_whisper import WhisperModel
        print(f"[Transcription] Running local Faster Whisper for {audio_path}...")
        model = WhisperModel("small", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, beam_size=5)
        text = " ".join([s.text for s in segments])
        return text.strip()

class APIWhisperProvider(TranscriptionProvider):
    def transcribe(self, audio_path: str) -> str:
        print(f"[Transcription] Running API Whisper ({aurex_api.provider}) for {audio_path}...")
        if not aurex_api.client:
            raise Exception("AI API Client not configured. Cannot transcribe.")
            
        model = "whisper-large-v3" if aurex_api.provider == "Groq" else "whisper-1"
        
        with open(audio_path, "rb") as file:
            transcription = aurex_api.client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), file.read()),
                model=model,
                response_format="text"
            )
        
        # Depending on openai library version, response_format='text' might return a string directly
        if isinstance(transcription, str):
            return transcription.strip()
        else:
            return transcription.text.strip()

class TranscriptionProviderManager:
    def get_provider(self, duration_seconds: float) -> TranscriptionProvider:
        # Default Auto mode: < 30 min (1800s) -> Local, else API
        if duration_seconds > 1800:
            print(f"[Transcription] Auto Mode: Media > 30 min, routing to {aurex_api.provider} Cloud...")
            return APIWhisperProvider()
        else:
            print("[Transcription] Auto Mode: Media < 30 min, routing to Local Whisper...")
            return FasterWhisperProvider()
