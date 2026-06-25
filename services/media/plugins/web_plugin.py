import requests
from bs4 import BeautifulSoup
import json
import time
import re
from services.media.plugins.base import MediaPlugin

class WebPlugin(MediaPlugin):
    @property
    def name(self) -> str:
        return "web"

    def extract(self, source: str, source_id: int = None) -> tuple[str, str, str, int]:
        """
        Extract content from generic web pages using a layered approach.
        Returns: (raw_text, title, channel, duration)
        """
        t0 = time.time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            resp = requests.get(source, headers=headers, timeout=15)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            title = soup.title.string.strip() if soup.title else "Web Page"
            channel = source.split('/')[2] if '//' in source else "Web"
            
            # Layer 1: JSON-LD Metadata
            metadata = []
            json_lds = soup.find_all('script', type='application/ld+json')
            for script in json_lds:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if data.get('description'): metadata.append(data.get('description'))
                        if data.get('articleBody'): metadata.append(data.get('articleBody'))
                except:
                    pass
                    
            # Layer 2: Main Content Tags
            for tag in ['nav', 'footer', 'header', 'script', 'style', 'aside']:
                for el in soup.find_all(tag):
                    el.decompose()
                    
            content_tags = soup.find_all(['article', 'main'])
            if not content_tags:
                # Fallback to elements with specific classes/ids
                content_tags = soup.find_all(class_=re.compile(r'content|article|post|body', re.I))
                
            if content_tags:
                extracted_text = " ".join([t.get_text(separator=' ', strip=True) for t in content_tags])
            else:
                # Ultimate fallback: Body
                extracted_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
                
            # Combine JSON-LD and HTML text
            full_text = "\n\n".join(metadata) + "\n\n" + extracted_text
            
            # Clean up excessive whitespace
            full_text = re.sub(r'\s+', ' ', full_text).strip()
            
            elapsed = time.time() - t0
            print(f"[PERF] Web Extraction: {elapsed:.2f}s")
            
            return {
                "transcript": full_text,
                "title": title,
                "channel": channel,
                "duration": 0,
                "video_id": f"web:{source}",
                "extraction_method": "web_scraper"
            }
            
        except Exception as e:
            elapsed = time.time() - t0
            print(f"[PERF] Web Extraction: {elapsed:.2f}s (Failed)")
            raise Exception(f"Failed to fetch or parse web page: {e}")
