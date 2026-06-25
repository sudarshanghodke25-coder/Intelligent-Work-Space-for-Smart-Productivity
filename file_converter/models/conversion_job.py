"""
file_converter/models/conversion_job.py
Mutable ConversionJob model representing a single file in the queue.
Uses threading.Event for cancellation signalling.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional, Callable


class JobStatus(Enum):
    """Lifecycle states for a conversion job."""
    PENDING    = auto()
    QUEUED     = auto()
    RUNNING    = auto()
    PAUSED     = auto()
    COMPLETED  = auto()
    FAILED     = auto()
    CANCELLED  = auto()


@dataclass
class ConversionJob:
    """
    Represents a single file-conversion task in the job queue.
    All mutable fields are updated by the worker thread and read by the UI.
    """

    # Identity
    job_id:          str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at:      datetime = field(default_factory=datetime.now)

    # Source
    source_path:     str = ""
    source_name:     str = ""
    source_ext:      str = ""
    source_size:     int = 0          # bytes

    # Target
    target_ext:      str = ""
    output_path:     str = ""         # resolved after job completes
    output_folder:   str = ""         # user-chosen directory

    # Settings snapshot (copied at submission time)
    quality:         str = "High"
    compression:     str = "Medium"
    enable_ocr:      bool = False
    keep_formatting: bool = True
    auto_rename:     bool = True
    overwrite:       bool = False
    open_after:      bool = False
    page_range:      str = ""         # e.g. "1-3,5"
    password:        str = ""
    extra_settings:  dict = field(default_factory=dict)

    # Runtime
    status:          JobStatus = JobStatus.PENDING
    progress:        float = 0.0      # 0.0 – 1.0
    status_message:  str = "Waiting…"
    error_message:   str = ""
    started_at:      Optional[datetime] = None
    completed_at:    Optional[datetime] = None
    duration_ms:     int = 0

    # Priority (lower = higher priority)
    priority:        int = 5
    queue_position:  int = 0

    # AI suggestion text
    ai_suggestion:   str = ""

    # Threading controls (not serialized)
    _cancel_event:   threading.Event = field(default_factory=threading.Event, repr=False)
    _pause_event:    threading.Event = field(default_factory=threading.Event, repr=False)

    # UI callback (set by controller, called from worker)
    _progress_callback: Optional[Callable[[str, float, str], None]] = field(
        default=None, repr=False
    )

    def __post_init__(self):
        # pause_event is set by default (not paused)
        self._pause_event.set()

    # ── Control API ────────────────────────────────────────────────────────

    def cancel(self) -> None:
        """Signal the worker thread to cancel this job."""
        self._cancel_event.set()
        self.status = JobStatus.CANCELLED

    def pause(self) -> None:
        """Signal the worker thread to pause this job."""
        self._pause_event.clear()
        self.status = JobStatus.PAUSED

    def resume(self) -> None:
        """Signal the worker thread to resume a paused job."""
        self._pause_event.set()
        self.status = JobStatus.RUNNING

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def wait_if_paused(self) -> None:
        """Block worker until unpaused or cancelled."""
        self._pause_event.wait()

    # ── Progress reporting ─────────────────────────────────────────────────

    def report_progress(self, fraction: float, message: str = "") -> None:
        """Update progress fraction and notify UI callback."""
        self.progress = max(0.0, min(1.0, fraction))
        if message:
            self.status_message = message
        if self._progress_callback:
            try:
                self._progress_callback(self.job_id, self.progress, self.status_message)
            except Exception:
                pass

    # ── Human-readable helpers ─────────────────────────────────────────────

    @property
    def source_size_human(self) -> str:
        """Return file size as human-readable string."""
        if self.source_size < 1_024:
            return f"{self.source_size} B"
        elif self.source_size < 1_048_576:
            return f"{self.source_size / 1024:.1f} KB"
        elif self.source_size < 1_073_741_824:
            return f"{self.source_size / 1_048_576:.1f} MB"
        else:
            return f"{self.source_size / 1_073_741_824:.2f} GB"

    @property
    def display_name(self) -> str:
        """Truncated filename for narrow UI display."""
        if len(self.source_name) <= 28:
            return self.source_name
        stem = self.source_name[: self.source_name.rfind(".")]
        ext = self.source_ext
        return stem[:22] + "…" + ext

    @property
    def estimated_seconds(self) -> Optional[float]:
        """Rough ETA based on progress and elapsed time."""
        if self.started_at and self.progress > 0.01:
            elapsed = (datetime.now() - self.started_at).total_seconds()
            remaining = elapsed / self.progress - elapsed
            return max(0.0, remaining)
        return None

    def to_dict(self) -> dict:
        """Serialize to plain dict for database storage."""
        return {
            "job_id": self.job_id,
            "source_path": self.source_path,
            "source_name": self.source_name,
            "source_ext": self.source_ext,
            "source_size": self.source_size,
            "target_ext": self.target_ext,
            "output_path": self.output_path,
            "quality": self.quality,
            "compression": self.compression,
            "enable_ocr": int(self.enable_ocr),
            "status": self.status.name,
            "progress": self.progress,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
