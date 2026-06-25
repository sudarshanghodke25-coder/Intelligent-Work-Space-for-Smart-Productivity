"""
file_converter/constants/quick_tools.py
Static definitions for Quick Tool cards.
Loaded by the PluginRegistry and rendered dynamically by the UI.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class QuickToolDef:
    """Immutable descriptor for a single quick-tool card."""
    tool_id: str
    label: str
    icon: str
    description: str
    input_formats: List[str]       # accepted source extensions
    output_format: str             # target extension
    category: str                  # for grouping
    is_premium: bool = False
    requires_ocr: bool = False
    shortcut: Optional[str] = None


QUICK_TOOLS: List[QuickToolDef] = [
    # ── PDF Tools ─────────────────────────────────────────────────────────
    QuickToolDef(
        tool_id="pdf_to_word",
        label="PDF → Word",
        icon="📄➡📝",
        description="Convert PDF documents to editable Word files",
        input_formats=[".pdf"],
        output_format=".docx",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="word_to_pdf",
        label="Word → PDF",
        icon="📝➡📄",
        description="Convert Word documents to PDF",
        input_formats=[".docx", ".doc"],
        output_format=".pdf",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="excel_to_pdf",
        label="Excel → PDF",
        icon="📊➡📄",
        description="Convert Excel spreadsheets to PDF",
        input_formats=[".xlsx", ".xls"],
        output_format=".pdf",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="ppt_to_pdf",
        label="PPT → PDF",
        icon="📽️➡📄",
        description="Convert PowerPoint presentations to PDF",
        input_formats=[".pptx", ".ppt"],
        output_format=".pdf",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="pdf_to_images",
        label="PDF → Images",
        icon="📄➡🖼️",
        description="Extract each PDF page as a PNG image",
        input_formats=[".pdf"],
        output_format=".png",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="images_to_pdf",
        label="Images → PDF",
        icon="🖼️➡📄",
        description="Combine multiple images into a single PDF",
        input_formats=[".png", ".jpg", ".jpeg", ".webp", ".bmp"],
        output_format=".pdf",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="merge_pdf",
        label="Merge PDF",
        icon="📑",
        description="Merge multiple PDF files into one",
        input_formats=[".pdf"],
        output_format=".pdf",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="split_pdf",
        label="Split PDF",
        icon="✂️",
        description="Split a PDF into separate pages or ranges",
        input_formats=[".pdf"],
        output_format=".pdf",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="compress_pdf",
        label="Compress PDF",
        icon="🗜️",
        description="Reduce PDF file size while preserving quality",
        input_formats=[".pdf"],
        output_format=".pdf",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="rotate_pdf",
        label="Rotate PDF",
        icon="🔄",
        description="Rotate PDF pages 90°, 180° or 270°",
        input_formats=[".pdf"],
        output_format=".pdf",
        category="PDF",
    ),
    QuickToolDef(
        tool_id="ocr_pdf",
        label="OCR",
        icon="🔍",
        description="Extract text from scanned PDFs using OCR",
        input_formats=[".pdf", ".png", ".jpg", ".tiff"],
        output_format=".txt",
        category="PDF",
        requires_ocr=True,
    ),
    # ── Image Tools ────────────────────────────────────────────────────────
    QuickToolDef(
        tool_id="resize_image",
        label="Resize Image",
        icon="📐",
        description="Resize images to custom dimensions",
        input_formats=[".png", ".jpg", ".jpeg", ".webp", ".bmp"],
        output_format=".png",
        category="Image",
    ),
    QuickToolDef(
        tool_id="convert_image",
        label="Convert Image",
        icon="🔀",
        description="Convert between PNG, JPG, WebP, BMP, GIF",
        input_formats=[".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"],
        output_format=".png",
        category="Image",
    ),
    QuickToolDef(
        tool_id="compress_image",
        label="Compress Image",
        icon="🗜️",
        description="Reduce image file size with quality control",
        input_formats=[".png", ".jpg", ".jpeg", ".webp"],
        output_format=".jpg",
        category="Image",
    ),
    # ── Audio & Video ─────────────────────────────────────────────────────
    QuickToolDef(
        tool_id="extract_audio",
        label="Extract Audio",
        icon="🎵",
        description="Extract audio track from video files",
        input_formats=[".mp4", ".mov", ".avi", ".mkv"],
        output_format=".mp3",
        category="Media",
    ),
    QuickToolDef(
        tool_id="video_to_audio",
        label="Video → Audio",
        icon="🎬➡🎵",
        description="Convert video files to audio format",
        input_formats=[".mp4", ".mov", ".avi", ".mkv"],
        output_format=".mp3",
        category="Media",
    ),
    QuickToolDef(
        tool_id="compress_video",
        label="Compress Video",
        icon="📹",
        description="Reduce video file size and bitrate",
        input_formats=[".mp4", ".mov", ".avi"],
        output_format=".mp4",
        category="Media",
    ),
    # ── Archive ────────────────────────────────────────────────────────────
    QuickToolDef(
        tool_id="zip_extract",
        label="ZIP Extract",
        icon="📦",
        description="Extract contents of ZIP archives",
        input_formats=[".zip", ".tar", ".gz"],
        output_format="folder",
        category="Archive",
    ),
    QuickToolDef(
        tool_id="zip_create",
        label="ZIP Create",
        icon="🗜️",
        description="Create ZIP archive from files",
        input_formats=["*"],
        output_format=".zip",
        category="Archive",
    ),
    # ── Data & Code ────────────────────────────────────────────────────────
    QuickToolDef(
        tool_id="csv_to_excel",
        label="CSV → Excel",
        icon="🗃️➡📊",
        description="Convert CSV data to Excel workbook",
        input_formats=[".csv"],
        output_format=".xlsx",
        category="Data",
    ),
    QuickToolDef(
        tool_id="json_formatter",
        label="JSON Format",
        icon="📋",
        description="Pretty-print and validate JSON files",
        input_formats=[".json"],
        output_format=".json",
        category="Data",
    ),
    QuickToolDef(
        tool_id="markdown_to_pdf",
        label="Markdown → PDF",
        icon="🖊️➡📄",
        description="Render Markdown documents as styled PDF",
        input_formats=[".md"],
        output_format=".pdf",
        category="Text",
    ),
    QuickToolDef(
        tool_id="code_formatter",
        label="Code Format",
        icon="💻",
        description="Auto-format source code files",
        input_formats=[".py", ".js", ".java", ".cpp"],
        output_format=".txt",
        category="Code",
    ),
    QuickToolDef(
        tool_id="html_to_pdf",
        label="HTML → PDF",
        icon="🌐➡📄",
        description="Convert HTML pages to PDF documents",
        input_formats=[".html", ".htm"],
        output_format=".pdf",
        category="Web",
    ),
]

# Build lookup map
QUICK_TOOLS_BY_ID: dict[str, QuickToolDef] = {t.tool_id: t for t in QUICK_TOOLS}

# Categories in display order
QUICK_TOOL_CATEGORIES = ["PDF", "Image", "Media", "Archive", "Data", "Text", "Web", "Code"]
