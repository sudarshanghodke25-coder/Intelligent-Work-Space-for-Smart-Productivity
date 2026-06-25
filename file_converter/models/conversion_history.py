"""
file_converter/models/conversion_history.py
Immutable record written to the DB after job completion.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class HistoryEntry:
    """Represents one completed (or failed) conversion stored in SQLite."""
    id:             int
    user_id:        int
    job_id:         str
    source_name:    str
    source_ext:     str
    target_ext:     str
    source_size:    int           # bytes
    output_path:    str
    status:         str           # "COMPLETED" | "FAILED" | "CANCELLED"
    error_message:  str
    duration_ms:    int
    quality:        str
    ai_suggestion:  str
    created_at:     datetime
    completed_at:   Optional[datetime] = None

    @property
    def source_size_human(self) -> str:
        if self.source_size < 1_024:
            return f"{self.source_size} B"
        elif self.source_size < 1_048_576:
            return f"{self.source_size / 1024:.1f} KB"
        else:
            return f"{self.source_size / 1_048_576:.1f} MB"

    @property
    def duration_human(self) -> str:
        if self.duration_ms < 1_000:
            return f"{self.duration_ms} ms"
        elif self.duration_ms < 60_000:
            return f"{self.duration_ms / 1000:.1f}s"
        else:
            return f"{self.duration_ms // 60_000}m {(self.duration_ms % 60_000) // 1000}s"

    @classmethod
    def from_row(cls, row) -> "HistoryEntry":
        """Construct from a sqlite3.Row."""
        def parse_dt(s):
            if not s:
                return None
            try:
                return datetime.fromisoformat(s)
            except ValueError:
                return None

        return cls(
            id=row["id"],
            user_id=row["user_id"],
            job_id=row["job_id"],
            source_name=row["source_name"],
            source_ext=row["source_ext"],
            target_ext=row["target_ext"],
            source_size=row["source_size"] or 0,
            output_path=row["output_path"] or "",
            status=row["status"],
            error_message=row["error_message"] or "",
            duration_ms=row["duration_ms"] or 0,
            quality=row["quality"] or "High",
            ai_suggestion=row["ai_suggestion"] or "",
            created_at=parse_dt(row["created_at"]) or datetime.now(),
            completed_at=parse_dt(row["completed_at"]),
        )


@dataclass
class ConverterStats:
    """Aggregated statistics shown in the right sidebar."""
    total_conversions: int = 0
    successful: int = 0
    failed: int = 0
    total_bytes_processed: int = 0
    avg_duration_ms: float = 0.0
    most_used_format: str = ""
    today_count: int = 0

    @property
    def total_size_human(self) -> str:
        b = self.total_bytes_processed
        if b < 1_048_576:
            return f"{b / 1024:.1f} KB"
        elif b < 1_073_741_824:
            return f"{b / 1_048_576:.1f} MB"
        else:
            return f"{b / 1_073_741_824:.2f} GB"

    @property
    def success_rate(self) -> float:
        if self.total_conversions == 0:
            return 0.0
        return self.successful / self.total_conversions * 100
