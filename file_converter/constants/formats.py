"""
file_converter/constants/formats.py
Centralised registry of every supported format, its capabilities,
MIME type, icon, and category.  The UI reads from this file —
nothing is hardcoded in the widgets.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass(frozen=True)
class FormatInfo:
    """Immutable descriptor for a single file format."""
    ext: str                       # e.g. ".pdf"
    label: str                     # e.g. "PDF"
    category: str                  # e.g. "document"
    icon: str                      # emoji / unicode glyph
    mime_type: str
    can_convert_to: List[str]      # list of target extensions
    description: str = ""
    supports_ocr: bool = False
    supports_pages: bool = False
    supports_password: bool = False
    supports_compression: bool = False
    max_size_mb: int = 500


# ── Format registry ────────────────────────────────────────────────────────

FORMATS: Dict[str, FormatInfo] = {
    # ── Documents ──────────────────────────────────────────────────────────
    ".pdf": FormatInfo(
        ext=".pdf", label="PDF", category="document", icon="📄",
        mime_type="application/pdf",
        can_convert_to=[".docx", ".txt", ".png", ".jpg", ".xlsx", ".pptx", ".html", ".md"],
        description="Portable Document Format",
        supports_ocr=True, supports_pages=True,
        supports_password=True, supports_compression=True,
    ),
    ".docx": FormatInfo(
        ext=".docx", label="Word", category="document", icon="📝",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        can_convert_to=[".pdf", ".txt", ".html", ".md"],
        description="Microsoft Word Document",
        supports_compression=True,
    ),
    ".doc": FormatInfo(
        ext=".doc", label="Word (Legacy)", category="document", icon="📝",
        mime_type="application/msword",
        can_convert_to=[".pdf", ".docx", ".txt"],
        description="Microsoft Word 97-2003 Document",
    ),
    ".xlsx": FormatInfo(
        ext=".xlsx", label="Excel", category="spreadsheet", icon="📊",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        can_convert_to=[".pdf", ".csv", ".json", ".html"],
        description="Microsoft Excel Workbook",
    ),
    ".xls": FormatInfo(
        ext=".xls", label="Excel (Legacy)", category="spreadsheet", icon="📊",
        mime_type="application/vnd.ms-excel",
        can_convert_to=[".pdf", ".xlsx", ".csv"],
        description="Microsoft Excel 97-2003 Workbook",
    ),
    ".csv": FormatInfo(
        ext=".csv", label="CSV", category="spreadsheet", icon="🗃️",
        mime_type="text/csv",
        can_convert_to=[".xlsx", ".json", ".html", ".pdf"],
        description="Comma-Separated Values",
    ),
    ".pptx": FormatInfo(
        ext=".pptx", label="PowerPoint", category="presentation", icon="📽️",
        mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        can_convert_to=[".pdf", ".png", ".jpg"],
        description="Microsoft PowerPoint Presentation",
    ),
    ".ppt": FormatInfo(
        ext=".ppt", label="PowerPoint (Legacy)", category="presentation", icon="📽️",
        mime_type="application/vnd.ms-powerpoint",
        can_convert_to=[".pdf", ".pptx"],
        description="Microsoft PowerPoint 97-2003",
    ),
    # ── Text / Code ────────────────────────────────────────────────────────
    ".txt": FormatInfo(
        ext=".txt", label="Plain Text", category="text", icon="📃",
        mime_type="text/plain",
        can_convert_to=[".pdf", ".docx", ".html", ".md"],
        description="Plain Text File",
    ),
    ".md": FormatInfo(
        ext=".md", label="Markdown", category="text", icon="🖊️",
        mime_type="text/markdown",
        can_convert_to=[".pdf", ".html", ".docx", ".txt"],
        description="Markdown Document",
    ),
    ".html": FormatInfo(
        ext=".html", label="HTML", category="web", icon="🌐",
        mime_type="text/html",
        can_convert_to=[".pdf", ".txt", ".md", ".docx"],
        description="HyperText Markup Language",
    ),
    ".htm": FormatInfo(
        ext=".htm", label="HTML", category="web", icon="🌐",
        mime_type="text/html",
        can_convert_to=[".pdf", ".txt", ".md"],
        description="HyperText Markup Language",
    ),
    ".json": FormatInfo(
        ext=".json", label="JSON", category="data", icon="📋",
        mime_type="application/json",
        can_convert_to=[".csv", ".xlsx", ".txt", ".yaml"],
        description="JavaScript Object Notation",
    ),
    ".xml": FormatInfo(
        ext=".xml", label="XML", category="data", icon="🔖",
        mime_type="application/xml",
        can_convert_to=[".json", ".csv", ".txt"],
        description="Extensible Markup Language",
    ),
    ".py": FormatInfo(
        ext=".py", label="Python", category="code", icon="🐍",
        mime_type="text/x-python",
        can_convert_to=[".txt", ".html", ".pdf"],
        description="Python Source Code",
    ),
    ".js": FormatInfo(
        ext=".js", label="JavaScript", category="code", icon="⚡",
        mime_type="text/javascript",
        can_convert_to=[".txt", ".html"],
        description="JavaScript Source",
    ),
    ".java": FormatInfo(
        ext=".java", label="Java", category="code", icon="☕",
        mime_type="text/x-java",
        can_convert_to=[".txt", ".html", ".pdf"],
        description="Java Source Code",
    ),
    ".cpp": FormatInfo(
        ext=".cpp", label="C++", category="code", icon="⚙️",
        mime_type="text/x-c++src",
        can_convert_to=[".txt", ".html"],
        description="C++ Source Code",
    ),
    ".yaml": FormatInfo(
        ext=".yaml", label="YAML", category="data", icon="📋",
        mime_type="text/yaml",
        can_convert_to=[".json", ".txt"],
        description="YAML Ain't Markup Language",
    ),
    # ── Images ─────────────────────────────────────────────────────────────
    ".png": FormatInfo(
        ext=".png", label="PNG", category="image", icon="🖼️",
        mime_type="image/png",
        can_convert_to=[".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".pdf", ".ico"],
        description="Portable Network Graphics",
        supports_compression=True,
    ),
    ".jpg": FormatInfo(
        ext=".jpg", label="JPEG", category="image", icon="🖼️",
        mime_type="image/jpeg",
        can_convert_to=[".png", ".webp", ".bmp", ".gif", ".pdf"],
        description="JPEG Image",
        supports_compression=True,
    ),
    ".jpeg": FormatInfo(
        ext=".jpeg", label="JPEG", category="image", icon="🖼️",
        mime_type="image/jpeg",
        can_convert_to=[".png", ".webp", ".bmp", ".pdf"],
        description="JPEG Image",
        supports_compression=True,
    ),
    ".webp": FormatInfo(
        ext=".webp", label="WebP", category="image", icon="🖼️",
        mime_type="image/webp",
        can_convert_to=[".png", ".jpg", ".bmp"],
        description="WebP Image",
    ),
    ".bmp": FormatInfo(
        ext=".bmp", label="BMP", category="image", icon="🖼️",
        mime_type="image/bmp",
        can_convert_to=[".png", ".jpg", ".webp"],
        description="Bitmap Image",
    ),
    ".gif": FormatInfo(
        ext=".gif", label="GIF", category="image", icon="🖼️",
        mime_type="image/gif",
        can_convert_to=[".png", ".jpg", ".webp", ".mp4"],
        description="Graphics Interchange Format",
    ),
    ".svg": FormatInfo(
        ext=".svg", label="SVG", category="image", icon="🖼️",
        mime_type="image/svg+xml",
        can_convert_to=[".png", ".jpg", ".pdf"],
        description="Scalable Vector Graphics",
    ),
    ".ico": FormatInfo(
        ext=".ico", label="ICO", category="image", icon="🖼️",
        mime_type="image/x-icon",
        can_convert_to=[".png"],
        description="Icon File",
    ),
    ".tiff": FormatInfo(
        ext=".tiff", label="TIFF", category="image", icon="🖼️",
        mime_type="image/tiff",
        can_convert_to=[".png", ".jpg", ".pdf"],
        description="Tagged Image File Format",
        supports_ocr=True,
    ),
    # ── Audio ──────────────────────────────────────────────────────────────
    ".mp3": FormatInfo(
        ext=".mp3", label="MP3", category="audio", icon="🎵",
        mime_type="audio/mpeg",
        can_convert_to=[".wav", ".ogg", ".flac", ".m4a"],
        description="MPEG Audio Layer III",
        supports_compression=True,
    ),
    ".wav": FormatInfo(
        ext=".wav", label="WAV", category="audio", icon="🎵",
        mime_type="audio/wav",
        can_convert_to=[".mp3", ".ogg", ".flac"],
        description="Waveform Audio File",
    ),
    ".ogg": FormatInfo(
        ext=".ogg", label="OGG", category="audio", icon="🎵",
        mime_type="audio/ogg",
        can_convert_to=[".mp3", ".wav"],
        description="Ogg Vorbis Audio",
    ),
    ".flac": FormatInfo(
        ext=".flac", label="FLAC", category="audio", icon="🎵",
        mime_type="audio/flac",
        can_convert_to=[".mp3", ".wav"],
        description="Free Lossless Audio Codec",
    ),
    ".m4a": FormatInfo(
        ext=".m4a", label="M4A", category="audio", icon="🎵",
        mime_type="audio/m4a",
        can_convert_to=[".mp3", ".wav"],
        description="MPEG-4 Audio",
    ),
    # ── Video ──────────────────────────────────────────────────────────────
    ".mp4": FormatInfo(
        ext=".mp4", label="MP4", category="video", icon="🎬",
        mime_type="video/mp4",
        can_convert_to=[".avi", ".mov", ".mkv", ".mp3", ".wav", ".gif"],
        description="MPEG-4 Video",
        supports_compression=True,
    ),
    ".mov": FormatInfo(
        ext=".mov", label="MOV", category="video", icon="🎬",
        mime_type="video/quicktime",
        can_convert_to=[".mp4", ".avi", ".mp3"],
        description="Apple QuickTime Movie",
    ),
    ".avi": FormatInfo(
        ext=".avi", label="AVI", category="video", icon="🎬",
        mime_type="video/x-msvideo",
        can_convert_to=[".mp4", ".mov", ".mp3"],
        description="Audio Video Interleave",
    ),
    ".mkv": FormatInfo(
        ext=".mkv", label="MKV", category="video", icon="🎬",
        mime_type="video/x-matroska",
        can_convert_to=[".mp4", ".avi", ".mp3"],
        description="Matroska Video",
    ),
    # ── Archives ───────────────────────────────────────────────────────────
    ".zip": FormatInfo(
        ext=".zip", label="ZIP", category="archive", icon="🗜️",
        mime_type="application/zip",
        can_convert_to=[".tar", ".tar.gz"],
        description="ZIP Archive",
    ),
    ".tar": FormatInfo(
        ext=".tar", label="TAR", category="archive", icon="🗜️",
        mime_type="application/x-tar",
        can_convert_to=[".zip", ".tar.gz"],
        description="Tape Archive",
    ),
    ".gz": FormatInfo(
        ext=".gz", label="GZ", category="archive", icon="🗜️",
        mime_type="application/gzip",
        can_convert_to=[".zip"],
        description="GNU Zip Archive",
    ),
}

# ── Category groups (for UI display) ──────────────────────────────────────

CATEGORY_LABELS: Dict[str, str] = {
    "document":     "Documents",
    "spreadsheet":  "Spreadsheets",
    "presentation": "Presentations",
    "text":         "Text & Markup",
    "web":          "Web",
    "data":         "Data Files",
    "code":         "Source Code",
    "image":        "Images",
    "audio":        "Audio",
    "video":        "Video",
    "archive":      "Archives",
}

# ── Quality levels ─────────────────────────────────────────────────────────

QUALITY_LEVELS = ["Maximum", "High", "Medium", "Low", "Minimum"]
DEFAULT_QUALITY = "High"

# ── Compression levels ─────────────────────────────────────────────────────

COMPRESSION_LEVELS = ["None", "Light", "Medium", "Heavy", "Maximum"]
DEFAULT_COMPRESSION = "Medium"


def get_format(ext: str) -> Optional[FormatInfo]:
    """Return FormatInfo for a given extension (case-insensitive)."""
    return FORMATS.get(ext.lower())


def get_supported_extensions() -> List[str]:
    """Return list of all supported file extensions."""
    return list(FORMATS.keys())


def get_formats_by_category(category: str) -> List[FormatInfo]:
    """Return all FormatInfo objects for a given category."""
    return [f for f in FORMATS.values() if f.category == category]


def is_supported(ext: str) -> bool:
    """Return True if the extension is in the registry."""
    return ext.lower() in FORMATS
