"""
file_converter/widgets/file_queue_panel.py
Scrollable file queue panel that holds all FileCard widgets.
Subscribes to FC_* events and updates cards in a thread-safe way.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

import customtkinter as ctk
from services.event_bus import bus
from theme import Colors, Fonts

from file_converter.models.conversion_job import ConversionJob, JobStatus
from file_converter.events.converter_events import ConverterEvents
from file_converter.widgets.file_card import FileCard


class FileQueuePanel(ctk.CTkFrame):
    """
    Scrollable list of FileCard widgets.
    Managed by the ConverterController via the event bus.
    """

    def __init__(
        self,
        parent,
        on_remove: Callable[[str], None] = None,
        on_target_change: Callable[[str, str], None] = None,
        on_pause: Callable[[str], None] = None,
        on_resume: Callable[[str], None] = None,
        on_cancel: Callable[[str], None] = None,
        on_retry: Callable[[str], None] = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._on_remove = on_remove
        self._on_target_change = on_target_change
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_cancel = on_cancel
        self._on_retry = on_retry

        self._cards: Dict[str, FileCard] = {}  # job_id → FileCard

        self._build()
        self._subscribe()

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build(self):
        # Section header
        header = ctk.CTkFrame(self, fg_color="transparent", height=32)
        header.pack(fill="x", pady=(0, 6))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="CONVERSION QUEUE",
            font=Fonts.CAPTION,
            text_color=Colors.TEXT_DIM,
            anchor="w",
            fg_color="transparent",
        ).pack(side="left")

        self._count_lbl = ctk.CTkLabel(
            header,
            text="0 files",
            font=Fonts.CAPTION,
            text_color=Colors.TEXT_MUTED,
            fg_color="transparent",
        )
        self._count_lbl.pack(side="right")

        # Scrollable container
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=Colors.GLASS_FILL_LIGHT,
            scrollbar_button_hover_color=Colors.GLASS_FILL_HOVER,
        )
        self._scroll.pack(fill="both", expand=True)

        # Empty state placeholder
        self._empty_lbl = ctk.CTkLabel(
            self._scroll,
            text="No files added yet.\nDrop files above or click Browse.",
            font=Fonts.BODY,
            text_color=Colors.TEXT_DIM,
            fg_color="transparent",
            justify="center",
        )
        self._empty_lbl.pack(expand=True, pady=40)

    # ── Event subscriptions ─────────────────────────────────────────────────

    def _subscribe(self):
        bus.subscribe(ConverterEvents.FILES_ADDED,   self._on_files_added)
        bus.subscribe(ConverterEvents.FILE_REMOVED,  self._on_file_removed)
        bus.subscribe(ConverterEvents.QUEUE_CLEARED, self._on_queue_cleared)
        bus.subscribe(ConverterEvents.JOB_PROGRESS,  self._on_job_progress)
        bus.subscribe(ConverterEvents.JOB_STARTED,   self._on_job_started)
        bus.subscribe(ConverterEvents.JOB_COMPLETED, self._on_job_completed)
        bus.subscribe(ConverterEvents.JOB_FAILED,    self._on_job_failed)
        bus.subscribe(ConverterEvents.JOB_CANCELLED, self._on_job_cancelled)
        bus.subscribe(ConverterEvents.JOB_PAUSED,    self._on_job_paused)
        bus.subscribe(ConverterEvents.JOB_RESUMED,   self._on_job_resumed)
        bus.subscribe(ConverterEvents.AI_SUGGESTION_READY, self._on_ai_suggestion)

    # ── Event handlers (run on main thread via EventBus.after) ─────────────

    def _on_files_added(self, jobs: list):
        for job in (jobs or []):
            self._add_card(job)
        self._refresh_empty_state()
        self._update_count()

    def _on_file_removed(self, job_id: str):
        self._remove_card(job_id)
        self._refresh_empty_state()
        self._update_count()

    def _on_queue_cleared(self, _=None):
        for card in list(self._cards.values()):
            card.destroy()
        self._cards.clear()
        self._refresh_empty_state()
        self._update_count()

    def _on_job_progress(self, data: dict):
        if not data:
            return
        card = self._cards.get(data.get("job_id", ""))
        if card:
            card.update_progress(data.get("fraction", 0.0), data.get("message", ""))

    def _on_job_started(self, job_id: str):
        card = self._cards.get(job_id)
        if card:
            card.update_status(JobStatus.RUNNING)

    def _on_job_completed(self, job: ConversionJob):
        if not job:
            return
        card = self._cards.get(job.job_id)
        if card:
            card.update_progress(1.0, "Completed ✓")
            card.update_status(JobStatus.COMPLETED)

    def _on_job_failed(self, data: dict):
        if not data:
            return
        card = self._cards.get(data.get("job_id", ""))
        if card:
            card.update_status(JobStatus.FAILED)

    def _on_job_cancelled(self, job_id: str):
        card = self._cards.get(job_id)
        if card:
            card.update_status(JobStatus.CANCELLED)

    def _on_job_paused(self, job_id: str):
        card = self._cards.get(job_id)
        if card:
            card.update_status(JobStatus.PAUSED)

    def _on_job_resumed(self, job_id: str):
        card = self._cards.get(job_id)
        if card:
            card.update_status(JobStatus.RUNNING)

    def _on_ai_suggestion(self, data: dict):
        if not data:
            return
        card = self._cards.get(data.get("job_id", ""))
        if card and data.get("suggestion"):
            card.show_ai_suggestion(data["suggestion"])

    # ── Internal helpers ───────────────────────────────────────────────────

    def _add_card(self, job: ConversionJob) -> None:
        if job.job_id in self._cards:
            return
        card = FileCard(
            self._scroll,
            job=job,
            on_remove=self._on_remove,
            on_target_change=self._on_target_change,
            on_pause=self._on_pause,
            on_resume=self._on_resume,
            on_cancel=self._on_cancel,
            on_retry=self._on_retry,
        )
        card.pack(fill="x", pady=(0, 8))
        self._cards[job.job_id] = card

    def _remove_card(self, job_id: str) -> None:
        card = self._cards.pop(job_id, None)
        if card:
            card.destroy()

    def _refresh_empty_state(self) -> None:
        if self._cards:
            self._empty_lbl.pack_forget()
        else:
            self._empty_lbl.pack(expand=True, pady=40)

    def _update_count(self) -> None:
        n = len(self._cards)
        self._count_lbl.configure(text=f"{n} file{'s' if n != 1 else ''}")
