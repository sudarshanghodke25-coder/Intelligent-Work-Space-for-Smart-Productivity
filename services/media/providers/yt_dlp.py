import os
import tempfile
from services.media.providers.base import TranscriptProvider
from services.media.cancellation import cancellation_manager

class YtDlpSubtitleProvider(TranscriptProvider):
    @property
    def name(self) -> str:
        return "yt_dlp_subtitles"

    def extract_transcript(self, video_id: str, url: str, source_id: int = None) -> str:
        cancellation_manager.check_cancelled(source_id)
        
        try:
            import yt_dlp
            print(f"[YT] Subtitle Provider Started for {video_id}")
            
            # Use temp directory to download subtitles
            with tempfile.TemporaryDirectory() as tmpdir:
                out_tmpl = os.path.join(tmpdir, '%(id)s.%(ext)s')
                
                ydl_opts = {
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': ['en'],
                    'subtitlesformat': 'vtt',
                    'outtmpl': out_tmpl,
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                    
                cancellation_manager.check_cancelled(source_id)
                
                # Check for downloaded vtt files
                vtt_files = [f for f in os.listdir(tmpdir) if f.endswith('.vtt')]
                if not vtt_files:
                    raise Exception("No subtitles found by yt-dlp")
                    
                vtt_path = os.path.join(tmpdir, vtt_files[0])
                
                # Simple VTT parser to strip timestamps
                import re
                transcript_text = []
                with open(vtt_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        # Skip empty lines, WEBVTT header, and timestamp lines
                        if not line or line == 'WEBVTT' or '-->' in line or line.startswith('Kind:') or line.startswith('Language:'):
                            continue
                        # Remove tags like <c> etc.
                        line = re.sub(r'<[^>]+>', '', line)
                        transcript_text.append(line)
                
                full_text = " ".join(transcript_text)
                
                # Deduplicate repeated lines (common in auto-generated VTTs)
                words = full_text.split()
                deduped = []
                for w in words:
                    if not deduped or deduped[-1] != w:
                        deduped.append(w)
                
                final_text = " ".join(deduped)
                
                if not final_text.strip():
                    raise Exception("Extracted yt-dlp subtitles were empty")
                
                print(f"[YT] Subtitle Provider Success. Length: {len(final_text)}")
                return final_text
                
        except Exception as e:
            print(f"[YT] Subtitle Provider Failed: {e}")
            raise Exception(f"yt-dlp subtitles failed: {e}")
