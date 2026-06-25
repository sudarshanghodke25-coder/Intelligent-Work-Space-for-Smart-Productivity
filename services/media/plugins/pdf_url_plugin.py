import requests
import tempfile
import os
import time
from services.media.plugins.base import MediaPlugin

class PdfUrlPlugin(MediaPlugin):
    @property
    def name(self) -> str:
        return "pdf_url"

    def extract(self, source: str, source_id: int = None) -> tuple[str, str, str, int]:
        """
        Download PDF from URL to temp file, parse, and delete temp file.
        Returns: (raw_text, title, channel, duration)
        """
        t0 = time.time()
        
        try:
            import fitz  # PyMuPDF
            
            print(f"[PdfUrlPlugin] Downloading PDF from {source}")
            resp = requests.get(source, timeout=15)
            resp.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name
                
            print(f"[PdfUrlPlugin] Parsing PDF {tmp_path}")
            doc = fitz.open(tmp_path)
            content = ""
            for page in doc:
                content += page.get_text() + "\n"
            doc.close()
            
            os.remove(tmp_path)
            
            title = source.split("/")[-1] if "/" in source else "PDF Document"
            if not title.endswith(".pdf"):
                title += ".pdf"
                
            elapsed = time.time() - t0
            print(f"[PERF] PDF URL Extraction: {elapsed:.2f}s")
            
            return {
                "transcript": content,
                "title": title,
                "channel": "Web PDF",
                "duration": 0,
                "video_id": f"pdf:{source.split('/')[-1]}",
                "extraction_method": "PyMuPDF"
            }
            
        except Exception as e:
            elapsed = time.time() - t0
            print(f"[PERF] PDF URL Extraction: {elapsed:.2f}s (Failed)")
            raise Exception(f"Failed to fetch or parse PDF from URL: {e}")
