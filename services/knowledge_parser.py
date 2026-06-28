import os
import json

class KnowledgeParser:
    """Extracts raw text and basic metadata from various file types."""
    
    @staticmethod
    def extract_text(file_path: str, file_type: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_type = file_type.lower()
        
        try:
            if file_type == "pdf":
                return KnowledgeParser._parse_pdf(file_path)
            elif file_type == "docx":
                return KnowledgeParser._parse_docx(file_path)
            elif file_type in ["txt", "md", "csv"]:
                return KnowledgeParser._parse_text(file_path)
            elif file_type == "json":
                return KnowledgeParser._parse_json(file_path)
            elif file_type == "xlsx":
                return KnowledgeParser._parse_xlsx(file_path)
            else:
                return f"[Unsupported file type for extraction: {file_type}]"
        except Exception as e:
            print(f"Extraction error for {file_path}: {e}")
            return f"[Extraction Error: {str(e)}]"

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        try:
            import fitz # PyMuPDF
            doc = fitz.open(file_path)
            text = []
            for page in doc:
                text.append(page.get_text())
            doc.close()
            return "\n\n".join(text)
        except ImportError:
            return "[PyMuPDF (fitz) is not installed. PDF extraction failed.]"

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            return "[python-docx is not installed. DOCX extraction failed.]"

    @staticmethod
    def _parse_text(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def _parse_json(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return json.dumps(data, indent=2)

    @staticmethod
    def _parse_xlsx(file_path: str) -> str:
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_string()
        except ImportError:
            return "[pandas/openpyxl not installed. XLSX extraction failed.]"

    @staticmethod
    def extract_from_url(url: str, source_type: str, source_id: int = None) -> any:
        """Extracts content from a Website or YouTube URL."""
        source_type = source_type.lower()
        try:
            if source_type == "youtube":
                return KnowledgeParser._parse_youtube(url, source_id)
            elif source_type == "website":
                return KnowledgeParser._parse_website(url)
            else:
                raise ValueError(f"Unsupported URL type: {source_type}")
        except Exception as e:
            print(f"URL Extraction error for {url}: {e}")
            raise Exception(f"Extraction Error: {str(e)}")

    @staticmethod
    def _parse_website(url: str) -> str:
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=10)
            print(f"[WEBSITE]\nURL: {url}\nStatus Code: {response.status_code}\n")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts, styles, navs
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
                
            # Priority extraction
            content_node = soup.find('article') or soup.find('main') or soup.find('body') or soup
            text = content_node.get_text(separator="\n", strip=True)
            
            char_count = len(text)
            word_count = len(text.split())
            print(f"Extracted Text Length: {char_count}\nWords Extracted: {word_count}\n")
            print(f"Website chars: {len(text)}")
            
            return text
        except Exception as e:
            print(f"Website parsing failed: {e}")
            return ""

    @staticmethod
    def _parse_youtube(url: str, source_id: int = None) -> dict:
        from services.youtube.provider_manager import provider_manager
        # provider_manager.extract returns a dict containing transcript and metadata
        return provider_manager.extract(url, source_id)

knowledge_parser = KnowledgeParser()
