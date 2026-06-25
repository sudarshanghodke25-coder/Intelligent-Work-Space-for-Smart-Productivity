"""
file_converter/widgets/file_card.py
Individual file card widget shown in the conversion queue.
Displays file icon, name, size, target format selector,
progress bar, status label, and control buttons.
"""

from __future__ import annotations

from typing import Callable, List, Optional

import customtkinter as ctk

from theme import Colors, Fonts, Dims
from file_converter.models.conversion_job import ConversionJob, JobStatus
from file_converter.constants.formats import get_format, FORMATS


def _status_color(status: JobStatus) -> str:
    mapping = {
        JobStatus.PENDING:   Colors.TEXT_MUTED,
        JobStatus.QUEUED:    Colors.INFO,
        JobStatus.RUNNING:   Colors.ACCENT_GLOW,
        JobStatus.PAUSED:    Colors.WARNING,
        JobStatus.COMPLETED: Colors.SUCCESS,
        JobStatus.FAILED:    Colors.ERROR,
        JobStatus.CANCELLED: Colors.TEXT_DIM,
    }
    return mapping.get(status, Colors.TEXT_MUTED)


def _status_text(status: JobStatus, message: str = "") -> str:
    if message:
        return message
    mapping = {
        JobStatus.PENDING:   "Ready",
        JobStatus.QUEUED:    "Queued…",
        JobStatus.RUNNING:   "Converting…",
        JobStatus.PAUSED:    "Paused",
        JobStatus.COMPLETED: "Completed ✓",
        JobStatus.FAILED:    "Failed ✗",
        JobStatus.CANCELLED: "Cancelled",
    }
    return mapping.get(status, "—")


class FileCard(ctk.CTkFrame):
    """
    One row in the file queue.  Entirely self-contained;
    communicates back to the panel only via callbacks.
    """

    def __init__(
        self,
        parent,
        job: ConversionJob,
        on_remove: Optional[Callable[[str], None]] = None,
        on_target_change: Optional[Callable[[str, str], None]] = None,
        on_pause: Optional[Callable[[str], None]] = None,
        on_resume: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[str], None]] = None,
        on_retry: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=Colors.GLASS_FILL,
            corner_radius=14,
            border_width=1,
            border_color=Colors.GLASS_BORDER,
            **kwargs,
        )

        self._job = job
        self._on_remove = on_remove
        self._on_target_change = on_target_change
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_cancel = on_cancel
        self._on_retry = on_retry

        self._build()

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="x", padx=14, pady=10)

        # ── Row 1: icon + name + size + format selector + remove ──────────
        row1 = ctk.CTkFrame(main, fg_color="transparent")
        row1.pack(fill="x")

        # File type icon
        fmt = get_format(self._job.source_ext)
        icon = fmt.icon if fmt else "📁"
        ctk.CTkLabel(
            row1, text=icon,
            font=("Segoe UI", 22),
            text_color=Colors.ACCENT_GLOW,
            fg_color="transparent",
            width=36,
        ).pack(side="left")

        # Name + size block
        name_block = ctk.CTkFrame(row1, fg_color="transparent")
        name_block.pack(side="left", fill="x", expand=True, padx=(8, 12))

        ctk.CTkLabel(
            name_block,
            text=self._job.display_name,
            font=Fonts.BODY_BOLD,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
            fg_color="transparent",
        ).pack(fill="x")

        ctk.CTkLabel(
            name_block,
            text=f"{self._job.source_ext.upper().lstrip('.')}  ·  {self._job.source_size_human}",
            font=Fonts.CAPTION,
            text_color=Colors.TEXT_MUTED,
            anchor="w",
            fg_color="transparent",
        ).pack(fill="x")

        # "Convert to" label
        ctk.CTkLabel(
            row1,
            text="Convert to",
            font=("Segoe UI", 11),
            text_color=Colors.TEXT_MUTED,
            fg_color="transparent",
        ).pack(side="left", padx=(10, 8))

        # Target format dropdown
        fmt_info = get_format(self._job.source_ext)
        targets = fmt_info.can_convert_to if fmt_info else []
        target_options = [e.upper().lstrip(".") for e in targets]

        if target_options:
            self._fmt_var = ctk.StringVar(
                value=self._job.target_ext.upper().lstrip(".")
            )
            fmt_menu = ctk.CTkOptionMenu(
                row1,
                variable=self._fmt_var,
                values=target_options,
                width=110,
                height=32,
                corner_radius=8,
                fg_color=Colors.GLASS_FILL_LIGHT,
                button_color=Colors.ACCENT_MUTED,
                button_hover_color=Colors.ACCENT_HOVER,
                text_color=Colors.TEXT_PRIMARY,
                font=Fonts.SMALL_BOLD,
                command=self._on_format_change,
            )
            fmt_menu.pack(side="left", padx=(0, 16))
        else:
            ctk.CTkLabel(
                row1,
                text=self._job.target_ext.upper().lstrip("."),
                font=Fonts.SMALL_BOLD,
                text_color=Colors.ACCENT_GLOW,
                fg_color="transparent",
            ).pack(side="left", padx=(0, 16))

        # Settings gear button
        gear_btn = ctk.CTkButton(
            row1,
            text="⚙",
            font=("Segoe UI", 16),
            width=32, height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=Colors.GLASS_FILL_HOVER,
            text_color=Colors.TEXT_MUTED,
            command=lambda: None, # Placeholder for individual file settings
        )
        gear_btn.pack(side="left", padx=(0, 4))

        # Remove button
        remove_btn = ctk.CTkButton(
            row1,
            text="✕",
            font=("Segoe UI", 14),
            width=32, height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=Colors.ERROR,
            text_color=Colors.TEXT_MUTED,
            command=self._on_remove_click,
        )
        remove_btn.pack(side="left", padx=(0, 4))

        # ── Row 2: progress bar ────────────────────────────────────────────
        self._progress_bar = ctk.CTkProgressBar(
            main,
            height=4,
            corner_radius=2,
            fg_color=Colors.GLASS_FILL_LIGHT,
            progress_color=Colors.ACCENT_GLOW,
        )
        self._progress_bar.set(self._job.progress)
        self._progress_bar.pack(fill="x", pady=(8, 4))

        # ── Row 3: status + ETA + controls ────────────────────────────────
        row3 = ctk.CTkFrame(main, fg_color="transparent")
        row3.pack(fill="x")

        self._status_lbl = ctk.CTkLabel(
            row3,
            text=_status_text(self._job.status, self._job.status_message),
            font=Fonts.CAPTION,
            text_color=_status_color(self._job.status),
            anchor="w",
            fg_color="transparent",
        )
        self._status_lbl.pack(side="left")

        # Control buttons (pause/resume/cancel/retry)
        self._ctrl_frame = ctk.CTkFrame(row3, fg_color="transparent")
        self._ctrl_frame.pack(side="right")
        self._render_controls()

        # AI suggestion (optional)
        if self._job.ai_suggestion:
            self._render_ai_suggestion()

    def _render_controls(self):
        for w in self._ctrl_frame.winfo_children():
            w.destroy()

        status = self._job.status
        btn_kwargs = dict(
            width=26, height=26, corner_radius=7,
            fg_color=Colors.GLASS_FILL_LIGHT,
            hover_color=Colors.GLASS_FILL_HOVER,
            text_color=Colors.TEXT_SECONDARY,
            font=("Segoe UI", 11),
        )

        if status == JobStatus.RUNNING:
            ctk.CTkButton(
                self._ctrl_frame, text="⏸", command=self._on_pause_click,
                **btn_kwargs
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                self._ctrl_frame, text="✕", command=self._on_cancel_click,
                hover_color=Colors.ERROR, **btn_kwargs
            ).pack(side="left", padx=2)

        elif status == JobStatus.PAUSED:
            ctk.CTkButton(
                self._ctrl_frame, text="▶", command=self._on_resume_click,
                **btn_kwargs
            ).pack(side="left", padx=2)
            ctk.CTkButton(
                self._ctrl_frame, text="✕", command=self._on_cancel_click,
                hover_color=Colors.ERROR, **btn_kwargs
            ).pack(side="left", padx=2)

        elif status == JobStatus.FAILED:
            ctk.CTkButton(
                self._ctrl_frame, text="↺", command=self._on_retry_click,
                hover_color=Colors.SUCCESS, **btn_kwargs
            ).pack(side="left", padx=2)

    def _render_ai_suggestion(self):
        sug = ctk.CTkFrame(
            self,
            fg_color=Colors.ACCENT_SUBTLE,
            corner_radius=8,
            border_width=1,
            border_color=Colors.ACCENT_MUTED,
        )
        sug.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(
            sug,
            text=f"💡  {self._job.ai_suggestion}",
            font=Fonts.CAPTION,
            text_color=Colors.ACCENT_GLOW,
            anchor="w",
            wraplength=500,
            fg_color="transparent",
        ).pack(padx=10, pady=6, fill="x")

    # ── Public update API (called by controller via event) ─────────────────

    def update_progress(self, fraction: float, message: str = "") -> None:
        """Thread-safe update must be called from the main thread."""
        self._job.progress = fraction
        self._progress_bar.set(fraction)
        if message:
            self._job.status_message = message
        self._status_lbl.configure(
            text=_status_text(self._job.status, self._job.status_message),
            text_color=_status_color(self._job.status),
        )

    def update_status(self, status: JobStatus) -> None:
        self._job.status = status
        self._status_lbl.configure(
            text=_status_text(status, self._job.status_message),
            text_color=_status_color(status),
        )
        # Change card border on completion
        if status == JobStatus.COMPLETED:
            self.configure(border_color=Colors.SUCCESS)
        elif status == JobStatus.FAILED:
            self.configure(border_color=Colors.ERROR)
        elif status == JobStatus.PAUSED:
            self.configure(border_color=Colors.WARNING)
        else:
            self.configure(border_color=Colors.GLASS_BORDER)
        self._render_controls()

    def show_ai_suggestion(self, suggestion: str) -> None:
        self._job.ai_suggestion = suggestion
        self._render_ai_suggestion()

    # ── Callbacks ──────────────────────────────────────────────────────────

    def _on_format_change(self, value: str):
        ext = "." + value.lower()
        if self._on_target_change:
            self._on_target_change(self._job.job_id, ext)

    def _on_remove_click(self):
        if self._on_remove:
            self._on_remove(self._job.job_id)

    def _on_pause_click(self):
        if self._on_pause:
            self._on_pause(self._job.job_id)

    def _on_resume_click(self):
        if self._on_resume:
            self._on_resume(self._job.job_id)

    def _on_cancel_click(self):
        if self._on_cancel:
            self._on_cancel(self._job.job_id)

    def _on_retry_click(self):
        if self._on_retry:
            self._on_retry(self._job.job_id)
