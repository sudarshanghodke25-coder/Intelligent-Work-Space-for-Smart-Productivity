from services.media.providers.base import TranscriptProvider
from services.media.cancellation import cancellation_manager

class YouTubeTranscriptProvider(TranscriptProvider):
    @property
    def name(self) -> str:
        return "transcript_api"

    def extract_transcript(self, video_id: str, url: str, source_id: int = None) -> str:
        cancellation_manager.check_cancelled(source_id)
        import time
        start_time = time.time()
        
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            print(f"[YT] Transcript API Started for {video_id}")
            ytt_api = YouTubeTranscriptApi()
            
            # Fetch directly with language fallback
            transcript_list = ytt_api.list(video_id)
            transcript = None
            
            try:
                # Try common languages, starting with English variants
                transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB', 'en-IN', 'hi', 'es', 'fr', 'de', 'ru', 'ja', 'ko'])
            except:
                # Fallback to the first available transcript
                for t in transcript_list:
                    transcript = t
                    break
            
            if not transcript:
                raise Exception("No transcripts found.")
                
            # If transcript is not English and is translatable, translate it
            if not transcript.language_code.startswith('en') and transcript.is_translatable:
                try:
                    transcript = transcript.translate('en')
                    print(f"[YT] Translated transcript to English from {transcript.language_code}")
                except Exception as e:
                    print(f"[YT] Failed to translate transcript: {e}")
                    
            fetched = transcript.fetch()
            full_text = " ".join([snippet.text for snippet in fetched.snippets])
            
            elapsed = time.time() - start_time
            print(f"[PERF] Transcript API: {elapsed:.2f}s")
            print(f"[YT] Transcript API Success. Length: {len(full_text)}")
            return full_text
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[PERF] Transcript API: {elapsed:.2f}s (Failed)")
            print(f"[YT] Transcript API Failed: {e}")
            raise Exception(f"Transcript API failed: {e}")
