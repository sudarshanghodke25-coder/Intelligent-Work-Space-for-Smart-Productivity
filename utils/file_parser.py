import os
import fitz  # PyMuPDF
import docx

def extract_text(filepath: str) -> str:
    """
    Extracts raw text from a document based on its extension.
    Supports .pdf, .docx, and .txt files.
    """
    if not os.path.exists(filepath):
        return ""
        
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext == ".pdf":
            text = ""
            with fitz.open(filepath) as doc:
                for page in doc:
                    text += page.get_text()
            return text
            
        elif ext == ".docx":
            doc = docx.Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
            
        elif ext == ".txt":
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
                
        else:
            # Fallback text read
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
                
    except Exception as e:
        return f"[Error extracting text from {filepath}: {str(e)}]"
