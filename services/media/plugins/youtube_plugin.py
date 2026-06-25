import os
import re
import time
from services.media.plugins.base import MediaPlugin
from services.media.providers.transcript_api import YouTubeTranscriptProvider
from services.media.providers.yt_dlp import YtDlpSubtitleProvider
from services.media.providers.whisper import WhisperProvider

class YouTubePlugin(MediaPlugin):
    @property
    def name(self) -> str:
        return "youtube"

    def can_handle(self, source: str) -> bool:
        youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        return bool(re.match(youtube_regex, source))

    def _extract_video_id(self, url: str) -> str:
        import re
        youtube_regex = r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=|embed/|v/|shorts/)?([^&=%\?]{11})'
        match = re.search(youtube_regex, url)
        if match:
            return match.group(1)
        return None

    def extract(self, source: str, source_id: int = None) -> dict:
        video_id = self._extract_video_id(source)
        if not video_id:
            raise ValueError(f"Could not extract video ID from {source}")

        # Try metadata
        from yt_dlp import YoutubeDL
        ydl_opts = {'quiet': True, 'no_warnings': True}
        meta_start = time.time()
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source, download=False)
                title = info.get('title', 'Unknown Title')
                channel = info.get('uploader', 'Unknown Channel')
                duration = info.get('duration', 0)
            meta_elapsed = time.time() - meta_start
            print(f"[PERF] YouTube Metadata: {meta_elapsed:.2f}s")
        except Exception as e:
            meta_elapsed = time.time() - meta_start
            print(f"[PERF] YouTube Metadata: {meta_elapsed:.2f}s (Failed)")
            print(f"[YouTubePlugin] Metadata extraction failed: {e}")
            title = "YouTube Video"
            channel = "Unknown"
            duration = 0

        providers = [
            YouTubeTranscriptProvider(),
            YtDlpSubtitleProvider(),
            WhisperProvider()
        ]

        transcript = None
        method = None
        start_time = time.time()

        for provider in providers:
            try:
                t0 = time.time()
                print(f"[YouTubePlugin] Attempting extraction with {provider.name}")
                transcript = provider.extract_transcript(video_id, source, source_id)
                elapsed = time.time() - t0
                if transcript and len(transcript.strip()) > 100:
                    method = provider.name
                    print(f"[PERF] Extraction ({provider.name}): {elapsed:.2f}s")
                    print(f"[YouTubePlugin] Provider {provider.name} succeeded.")
                    break  # Abort other providers once successful
                else:
                    print(f"[PERF] Extraction ({provider.name}): {elapsed:.2f}s (Empty)")
                    print(f"[YouTubePlugin] Provider {provider.name} returned empty/short transcript.")
            except Exception as e:
                elapsed = time.time() - t0
                print(f"[PERF] Extraction ({provider.name}): {elapsed:.2f}s (Failed)")
                print(f"[YouTubePlugin] Provider {provider.name} failed: {e}")

        if not transcript or len(transcript.strip()) < 100:
            raise Exception("All transcript providers failed or returned empty content.")

        processing_time = time.time() - start_time

        return {
            "transcript": transcript,
            "duration": duration,
            "title": title,
            "channel": channel,
            "video_id": video_id,
            "extraction_method": method,
            "processing_time": processing_time
        }
