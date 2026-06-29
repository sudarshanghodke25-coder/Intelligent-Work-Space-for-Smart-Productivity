"""
file_converter/services/ai_suggestion_service.py
Analyses uploaded files and produces intelligent conversion recommendations.
Integrates with the existing FLOWSPACE AI service infrastructure.
"""



from file_converter.models.conversion_job import ConversionJob
from file_converter.constants.formats import get_format


class AISuggestionService:
    """
    Generates format-specific conversion recommendations.
    Uses rule-based heuristics first (no API call needed for speed),
    then optionally enriches via the FLOWSPACE AI API.
    """

    # Rule-based suggestion map: (source_ext, condition) → suggestion text
    _RULES: list[tuple] = [
        # PDF rules
        (".pdf", "scanned", "This looks like a scanned PDF. Enable OCR to extract text."),
        (".pdf", "large",   "Large PDF detected. Consider compressing before sharing."),
        # Image rules
        (".png", "large",   "Large PNG found — convert to WebP for 30-50% smaller size."),
        (".bmp", "",        "BMP is uncompressed. Convert to PNG or WebP to save space."),
        (".tiff", "",       "TIFF is large. Convert to PNG or run OCR for text extraction."),
        # Office rules
        (".docx", "",       "Word document detected. Convert to PDF for universal sharing."),
        (".pptx", "",       "PowerPoint found. Export as PDF or high-res PNG images."),
        (".xlsx", "",       "Excel file detected. Convert to CSV for data analysis pipelines."),
        # Video rules
        (".mov", "",        "MOV files are large. Convert to MP4 for better compatibility."),
        (".avi", "",        "AVI is outdated. Convert to MP4 H.264 for smaller file size."),
        # Audio rules
        (".wav", "large",   "Uncompressed WAV detected. Convert to MP3 or FLAC to reduce size."),
        # Markdown rules
        (".md", "",         "Markdown file found. Convert to PDF or HTML for sharing."),
    ]

    def generate_suggestion(self, job: ConversionJob) -> str:
        """
        Return an AI-style suggestion string for the given job.
        Called from the worker thread — fast, non-blocking.
        """
        ext = job.source_ext.lower()
        size_mb = job.source_size / 1_048_576

        # Check rules in priority order
        for rule_ext, condition, suggestion in self._RULES:
            if rule_ext != ext:
                continue
            if condition == "large" and size_mb < 5:
                continue  # not large enough
            if condition == "scanned":
                # Heuristic: check if PDF has very little text via PyMuPDF
                if not self._pdf_is_scanned(job.source_path):
                    continue
            return suggestion

        # Fallback: recommend the most common target for this format
        fmt = get_format(ext)
        if fmt and fmt.can_convert_to:
            best_target = fmt.can_convert_to[0]
            return (
                f"Tip: '{fmt.label}' files are commonly converted to "
                f"'{best_target.upper().lstrip('.')}' for wider compatibility."
            )

        return ""

    @staticmethod
    def _pdf_is_scanned(path: str) -> bool:
        """Heuristic: very low text density → likely scanned."""
        try:
            import fitz
            doc = fitz.open(path)
            total_text = sum(len(doc[i].get_text()) for i in range(min(3, doc.page_count)))
            doc.close()
            # Less than 50 chars across first 3 pages → probably scanned
            return total_text < 50
        except Exception:
            return False


# Module-level singleton
ai_suggestion_service = AISuggestionService()
