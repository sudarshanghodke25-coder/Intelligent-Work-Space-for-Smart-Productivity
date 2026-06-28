"""
file_converter/adapters/pdf_adapter.py
PDF conversion adapter using PyMuPDF (fitz).
Handles: PDF→images, PDF→text, PDF compress, PDF merge/split/rotate.
Also handles: images→PDF, text/markdown→PDF (basic).
"""


from pathlib import Path
from typing import List

import fitz  # PyMuPDF

from file_converter.adapters.base_adapter import BaseAdapter
from file_converter.models.conversion_job import ConversionJob
from file_converter.exceptions.converter_errors import (
    CorruptFileError, ConversionFailureError, InvalidPageRangeError,
    JobCancelledError,
)


import multiprocessing

def _run_pdf2docx(source_path: str, out_path: str):
    from pdf2docx import Converter
    cv = Converter(source_path)
    cv.convert(out_path)
    cv.close()

def _parse_page_range(page_range_str: str, total_pages: int) -> List[int]:
    """
    Parse a page range string like "1-3,5,7-9" into a sorted list of
    0-based page indices.  Returns all pages if the string is empty.
    """
    if not page_range_str.strip():
        return list(range(total_pages))

    pages: set[int] = set()
    parts = page_range_str.replace(" ", "").split(",")
    for part in parts:
        if "-" in part:
            try:
                a, b = part.split("-", 1)
                a, b = int(a) - 1, int(b) - 1
                pages.update(range(max(0, a), min(total_pages - 1, b) + 1))
            except ValueError:
                raise InvalidPageRangeError(f"Invalid page range: '{part}'")
        else:
            try:
                p = int(part) - 1
                if 0 <= p < total_pages:
                    pages.add(p)
            except ValueError:
                raise InvalidPageRangeError(f"Invalid page number: '{part}'")
    return sorted(pages)


class PDFAdapter(BaseAdapter):
    """
    Handles all conversions that involve PDF as input or output.
    Uses PyMuPDF for reading/writing PDF and Pillow for image ops.
    """

    adapter_name = "PDFAdapter"
    supported_input_formats = [
        ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif",
        ".tiff", ".txt", ".md",
    ]
    supported_output_formats = [
        ".pdf", ".png", ".jpg", ".jpeg", ".txt", ".docx",
    ]

    def convert(self, job: ConversionJob) -> str:
        self._check_cancelled(job)
        src_ext = job.source_ext.lower()
        tgt_ext = job.target_ext.lower()

        job.report_progress(0.05, "Analysing file…")
        self._check_cancelled(job)

        try:
            if src_ext == ".pdf" and tgt_ext in (".png", ".jpg", ".jpeg"):
                return self._pdf_to_images(job)
            elif src_ext == ".pdf" and tgt_ext == ".txt":
                return self._pdf_to_text(job)
            elif src_ext == ".pdf" and tgt_ext == ".docx":
                return self._pdf_to_docx(job)
            elif src_ext == ".pdf" and tgt_ext == ".pdf":
                return self._pdf_process(job)
            elif src_ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff") \
                    and tgt_ext == ".pdf":
                return self._image_to_pdf(job)
            elif src_ext in (".txt", ".md") and tgt_ext == ".pdf":
                return self._text_to_pdf(job)
            else:
                raise ConversionFailureError(
                    f"PDFAdapter cannot handle {src_ext} → {tgt_ext}"
                )
        except JobCancelledError:
            raise
        except Exception as exc:
            if isinstance(exc, ConversionFailureError):
                raise
            raise ConversionFailureError(str(exc), exc) from exc

    # ── PDF → Images ───────────────────────────────────────────────────────

    def _pdf_to_images(self, job: ConversionJob) -> str:
        """Render each PDF page as a separate PNG/JPG image."""
        try:
            doc = fitz.open(job.source_path)
        except Exception as exc:
            raise CorruptFileError(f"Cannot open PDF: {exc}", exc) from exc

        total = doc.page_count
        pages = _parse_page_range(job.page_range, total)

        # For multi-page, output to a folder
        out_dir = self._resolve_output_path(job).with_suffix("")
        out_dir.mkdir(parents=True, exist_ok=True)

        quality_dpi = {"Maximum": 300, "High": 200, "Medium": 150, "Low": 96, "Minimum": 72}
        dpi = quality_dpi.get(job.quality, 200)
        mat = fitz.Matrix(dpi / 72, dpi / 72)

        for i, pg_idx in enumerate(pages):
            self._check_cancelled(job)
            self._check_paused(job)
            page = doc[pg_idx]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            out_file = out_dir / f"page_{pg_idx + 1:03d}{job.target_ext}"
            if job.target_ext.lower() in (".jpg", ".jpeg"):
                pix.save(str(out_file), output="jpeg")
            else:
                pix.save(str(out_file))
            job.report_progress(0.05 + 0.9 * (i + 1) / len(pages),
                                f"Rendering page {pg_idx + 1}/{total}…")

        doc.close()
        job.report_progress(1.0, "Done!")
        return str(out_dir)

    # ── PDF → Text ─────────────────────────────────────────────────────────

    def _pdf_to_docx(self, job: ConversionJob) -> str:
        try:
            from pdf2docx import Converter
        except ImportError:
            raise ConversionFailureError("pdf2docx not installed.")
            
        self._check_cancelled(job)
        job.report_progress(0.2, "Initializing converter…")
        
        try:
            out_path = self._resolve_output_path(job)
            
            job.report_progress(0.5, "Converting pages to Word format…")
            
            # Run conversion in a separate process to allow immediate cancellation
            import time
            p = multiprocessing.Process(target=_run_pdf2docx, args=(job.source_path, str(out_path)))
            p.start()
            
            while p.is_alive():
                # Check for cancellation while waiting
                if job.is_cancelled():
                    p.terminate()
                    p.join()
                    raise JobCancelledError("Conversion was stopped.")
                time.sleep(0.2)
                
            p.join()
            if p.exitcode != 0:
                raise ConversionFailureError(f"PDF to Word process failed with exit code {p.exitcode}")
            
            job.report_progress(1.0, "Done!")
            return str(out_path)
        except JobCancelledError:
            raise
        except Exception as exc:
            raise ConversionFailureError(f"PDF to Word failed: {exc}", exc)

    def _pdf_to_text(self, job: ConversionJob) -> str:
        """Extract all text from PDF via PyMuPDF."""
        try:
            doc = fitz.open(job.source_path)
        except Exception as exc:
            raise CorruptFileError(str(exc), exc) from exc

        total = doc.page_count
        pages = _parse_page_range(job.page_range, total)

        lines: List[str] = []
        for i, pg_idx in enumerate(pages):
            self._check_cancelled(job)
            self._check_paused(job)
            lines.append(doc[pg_idx].get_text())
            job.report_progress(0.1 + 0.8 * (i + 1) / len(pages),
                                f"Extracting page {pg_idx + 1}/{total}…")

        doc.close()

        out_path = self._resolve_output_path(job)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    # ── PDF → PDF (compress / rotate) ─────────────────────────────────────

    def _pdf_process(self, job: ConversionJob) -> str:
        """Apply compression, rotation, or page selection to a PDF."""
        try:
            doc = fitz.open(job.source_path)
        except Exception as exc:
            raise CorruptFileError(str(exc), exc) from exc

        total = doc.page_count
        pages = _parse_page_range(job.page_range, total)

        # Build new document with selected / rotated pages
        new_doc = fitz.open()
        rotation_map = {"90": 90, "180": 180, "270": 270}
        rotate = int(rotation_map.get(job.extra_settings.get("rotate", "0"), 0))

        for i, pg_idx in enumerate(pages):
            self._check_cancelled(job)
            self._check_paused(job)
            new_doc.insert_pdf(doc, from_page=pg_idx, to_page=pg_idx, rotate=rotate)
            job.report_progress(0.1 + 0.7 * (i + 1) / len(pages),
                                f"Processing page {pg_idx + 1}/{total}…")

        out_path = self._resolve_output_path(job)

        # Compression deflate level: 0 = none, 9 = maximum
        compress_level = {"None": 0, "Light": 3, "Medium": 6, "Heavy": 8, "Maximum": 9}
        deflate = compress_level.get(job.compression, 6)
        new_doc.save(str(out_path), deflate=deflate, garbage=4)
        new_doc.close()
        doc.close()
        job.report_progress(1.0, "Done!")
        return str(out_path)

    # ── Image(s) → PDF ─────────────────────────────────────────────────────

    def _image_to_pdf(self, job: ConversionJob) -> str:
        """Convert a single image to a PDF page."""
        self._check_cancelled(job)
        job.report_progress(0.2, "Opening image…")

        try:
            img_doc = fitz.open(job.source_path)
        except Exception:
            # Try via Pillow fallback
            try:
                from PIL import Image
                img = Image.open(job.source_path).convert("RGB")
                tmp = Path(job.source_path).with_suffix(".tmp.png")
                img.save(str(tmp))
                img_doc = fitz.open(str(tmp))
            except Exception as exc:
                raise CorruptFileError(f"Cannot open image: {exc}", exc) from exc

        job.report_progress(0.5, "Embedding into PDF…")
        pdf_bytes = img_doc.convert_to_pdf()
        img_doc.close()

        out_path = self._resolve_output_path(job)
        out_doc = fitz.open("pdf", pdf_bytes)
        out_doc.save(str(out_path))
        out_doc.close()

        job.report_progress(1.0, "Done!")
        return str(out_path)

    # ── Text/Markdown → PDF ────────────────────────────────────────────────

    def _text_to_pdf(self, job: ConversionJob) -> str:
        """Convert plain text or Markdown to a styled PDF."""
        self._check_cancelled(job)
        job.report_progress(0.1, "Reading text…")

        try:
            text = Path(job.source_path).read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise CorruptFileError(str(exc), exc) from exc

        job.report_progress(0.4, "Creating PDF…")

        doc = fitz.open()
        page = doc.new_page()
        rect = fitz.Rect(40, 40, page.rect.width - 40, page.rect.height - 40)

        # Insert text with word-wrap
        page.insert_textbox(
            rect, text,
            fontname="helv", fontsize=11,
            color=(0.9, 0.9, 0.9),
            align=fitz.TEXT_ALIGN_LEFT,
        )

        out_path = self._resolve_output_path(job)
        doc.save(str(out_path))
        doc.close()

        job.report_progress(1.0, "Done!")
        return str(out_path)
