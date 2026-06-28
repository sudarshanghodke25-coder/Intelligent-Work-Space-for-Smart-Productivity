"""
file_converter/adapters/__init__.py
Import all adapters here so their __init_subclass__ hooks fire,
registering them in BaseAdapter._registry automatically.
"""

from .base_adapter import BaseAdapter
from .pdf_adapter import PDFAdapter
from .image_adapter import ImageAdapter
from .document_adapter import DocumentAdapter
from .spreadsheet_adapter import SpreadsheetAdapter
from .audio_adapter import AudioAdapter, VideoToAudioAdapter
from .archive_adapter import ArchiveAdapter
from .text_adapter import TextAdapter
from .data_adapter import DataAdapter
from .video_adapter import VideoAdapter

__all__ = [
    "BaseAdapter",
    "PDFAdapter",
    "ImageAdapter",
    "DocumentAdapter",
    "SpreadsheetAdapter",
    "AudioAdapter",
    "VideoToAudioAdapter",
    "ArchiveAdapter",
    "TextAdapter",
    "DataAdapter",
    "VideoAdapter",
]
