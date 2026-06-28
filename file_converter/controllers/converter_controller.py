"""
file_converter/controllers/converter_controller.py
Main MVC controller for the File Converter module.
Mediates between the view (UI widgets), the job manager (workers),
and the database (persistence).  Uses the AUREX EventBus throughout.
"""


import os
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Dict, List, Optional

from services.event_bus import bus

from file_converter.models.conversion_job import ConversionJob, JobStatus
from file_converter.workers.job_worker import JobManager
from file_converter.events.converter_events import ConverterEvents
from file_converter.constants.formats import get_format, is_supported
from file_converter.constants.quick_tools import QUICK_TOOLS_BY_ID
from file_converter.database.converter_db import (
    init_converter_tables, load_all_settings, save_setting,
    get_history, get_stats, toggle_favorite_tool, get_favorite_tools,
    pin_file, unpin_file, get_pinned_files,
)
from file_converter.exceptions.converter_errors import (
    UnsupportedFormatError, FileSizeExceededError,
)
from authentication.session import current_session


class ConverterController:
    """
    Central controller for the File Converter module.

    Responsibilities:
    - Validates file paths and format support
    - Creates ConversionJob objects from UI settings
    - Delegates execution to JobManager (background)
    - Routes events from workers back to the UI via EventBus
    - Manages settings persistence
    """

    MAX_FILE_SIZE_MB = 2048  # 2 GB hard limit

    def __init__(self):
        # ── Infrastructure ────────────────────────────────────────────────
        self._publisher: Callable = self._publish_event
        self._job_manager = JobManager(event_publisher=self._publisher)
        self._job_manager.start()

        # ── State ─────────────────────────────────────────────────────────
        self._jobs: Dict[str, ConversionJob] = {}  # job_id → ConversionJob
        self._settings: dict = {}
        self._output_folder: str = str(Path.home() / "Downloads")

        # ── Init DB tables and load user settings ─────────────────────────
        init_converter_tables()
        self._load_settings()

        # ── Subscribe to worker events and forward to UI ──────────────────
        for event in [
            ConverterEvents.JOB_QUEUED, ConverterEvents.JOB_STARTED,
            ConverterEvents.JOB_PROGRESS, ConverterEvents.JOB_COMPLETED,
            ConverterEvents.JOB_FAILED, ConverterEvents.JOB_CANCELLED,
            ConverterEvents.JOB_PAUSED, ConverterEvents.JOB_RESUMED,
            ConverterEvents.BATCH_STARTED, ConverterEvents.BATCH_COMPLETED,
            ConverterEvents.BATCH_CANCELLED, ConverterEvents.HISTORY_UPDATED,
            ConverterEvents.AI_SUGGESTION_READY,
            ConverterEvents.NOTIFY_SUCCESS, ConverterEvents.NOTIFY_ERROR,
            ConverterEvents.NOTIFY_INFO, ConverterEvents.OPEN_FILE,
            ConverterEvents.OPEN_FOLDER,
        ]:
            bus.subscribe(event, lambda data, e=event: None)  # pass-through

    # ── Event publishing ───────────────────────────────────────────────────

    def _publish_event(self, event_type: str, data=None) -> None:
        """Thread-safe event publishing via the AUREX EventBus."""
        bus.publish(event_type, data)

    # ── File validation & job creation ────────────────────────────────────

    def add_files(self, paths: List[str]) -> List[ConversionJob]:
        """
        Validate each path and create a ConversionJob.
        Returns the list of successfully created jobs.
        Publishes FILES_ADDED with the accepted jobs.
        """
        accepted: List[ConversionJob] = []
        errors: List[str] = []

        for path in paths:
            try:
                job = self._create_job_from_path(path)
                self._jobs[job.job_id] = job
                accepted.append(job)
            except (UnsupportedFormatError, FileSizeExceededError, OSError) as exc:
                errors.append(str(exc))

        if accepted:
            self._publish_event(ConverterEvents.FILES_ADDED, accepted)

        if errors:
            combined = "\n".join(errors)
            self._publish_event(ConverterEvents.NOTIFY_ERROR,
                                f"Some files were skipped:\n{combined}")
        return accepted

    def _create_job_from_path(self, path: str) -> ConversionJob:
        """Build a ConversionJob from a file path, applying current settings."""
        p = Path(path)

        if not p.exists():
            raise OSError(f"File not found: {path}")

        ext = p.suffix.lower()
        if not is_supported(ext):
            raise UnsupportedFormatError(
                f"'{p.name}' — format '{ext}' is not supported."
            )

        size = p.stat().st_size
        if size > self.MAX_FILE_SIZE_MB * 1_048_576:
            raise FileSizeExceededError(
                f"'{p.name}' exceeds the {self.MAX_FILE_SIZE_MB} MB limit."
            )

        fmt = get_format(ext)
        default_target = fmt.can_convert_to[0] if fmt and fmt.can_convert_to else ext

        job = ConversionJob(
            source_path=str(p.resolve()),
            source_name=p.name,
            source_ext=ext,
            source_size=size,
            target_ext=default_target,
            output_folder=self._output_folder,
            quality=self._settings.get("quality", "High"),
            compression=self._settings.get("compression", "Medium"),
            enable_ocr=self._settings.get("enable_ocr", "0") == "1",
            keep_formatting=self._settings.get("keep_formatting", "1") == "1",
            auto_rename=self._settings.get("auto_rename", "1") == "1",
            overwrite=self._settings.get("overwrite", "0") == "1",
            open_after=self._settings.get("open_after", "0") == "1",
        )
        return job

    # ── Job control ────────────────────────────────────────────────────────

    def update_job_target(self, job_id: str, target_ext: str) -> None:
        """Change the target format for a queued job."""
        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.PENDING:
            job.target_ext = target_ext

    def remove_job(self, job_id: str) -> None:
        """Remove a job from the queue (cancel if running)."""
        job = self._jobs.pop(job_id, None)
        if job:
            job.cancel()
            self._job_manager.remove_job(job_id)
            self._publish_event(ConverterEvents.FILE_REMOVED, job_id)

    def start_conversion(self) -> None:
        """Submit all PENDING jobs to the job manager."""
        pending = [j for j in self._jobs.values() if j.status == JobStatus.PENDING]
        if not pending:
            self._publish_event(ConverterEvents.NOTIFY_INFO,
                                "No files in queue. Add files first.")
            return

        # Validate output folder
        try:
            Path(self._output_folder).mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self._publish_event(ConverterEvents.NOTIFY_ERROR,
                                f"Cannot create output folder: {exc}")
            return

        self._job_manager.submit_batch(pending)

    def cancel_all(self) -> None:
        self._job_manager.cancel_all()

    def pause_job(self, job_id: str) -> None:
        self._job_manager.pause_job(job_id)

    def resume_job(self, job_id: str) -> None:
        self._job_manager.resume_job(job_id)

    def cancel_job(self, job_id: str) -> None:
        self._job_manager.cancel_job(job_id)

    def retry_job(self, job_id: str) -> None:
        """Reset a failed job and resubmit it."""
        old_job = self._jobs.get(job_id)
        if not old_job:
            return
        # Create a fresh job from same source
        try:
            new_job = self._create_job_from_path(old_job.source_path)
            new_job.target_ext = old_job.target_ext
            self._jobs[new_job.job_id] = new_job
            # Remove old
            del self._jobs[job_id]
            self._job_manager.submit(new_job)
            self._publish_event(ConverterEvents.JOB_RETRIED, new_job.job_id)
        except Exception as exc:
            self._publish_event(ConverterEvents.NOTIFY_ERROR, str(exc))

    def clear_queue(self) -> None:
        """Cancel all jobs and clear the queue list."""
        self.cancel_all()
        self._jobs.clear()
        self._publish_event(ConverterEvents.QUEUE_CLEARED, None)

    # ── Quick tools ────────────────────────────────────────────────────────

    def apply_quick_tool(self, tool_id: str, job_id: Optional[str] = None) -> None:
        """
        Apply a quick tool preset to the currently selected job
        or open a file dialog if no job is selected.
        """
        tool = QUICK_TOOLS_BY_ID.get(tool_id)
        if not tool:
            return
        self._publish_event(ConverterEvents.QUICK_TOOL_SELECTED, tool)

        if not job_id:
            # Prompt user to select a file
            exts = ";".join(f"*{e}" for e in tool.input_formats if e != "*")
            file_types = [("Supported files", exts)]
            path = filedialog.askopenfilename(filetypes=file_types)
            if not path:
                return
            jobs = self.add_files([path])
            if not jobs:
                return
            job_id = jobs[0].job_id

        job = self._jobs.get(job_id)
        if job:
            job.target_ext = tool.output_format
            if tool.requires_ocr:
                job.enable_ocr = True
            self._publish_event(ConverterEvents.QUICK_TOOL_APPLY, tool_id)

    # ── Settings management ────────────────────────────────────────────────

    def _load_settings(self) -> None:
        """Load persisted settings from DB."""
        uid = current_session.user_id or 1
        self._settings = load_all_settings(uid)
        self._output_folder = self._settings.get(
            "output_folder", str(Path.home() / "Downloads")
        )

    def save_settings(self, new_settings: dict) -> None:
        """Persist settings to DB and update internal state."""
        uid = current_session.user_id or 1
        for key, value in new_settings.items():
            save_setting(uid, key, str(value))
            self._settings[key] = str(value)
        if "output_folder" in new_settings:
            self._output_folder = new_settings["output_folder"]
        self._publish_event(ConverterEvents.SETTINGS_CHANGED, self._settings)

    def set_output_folder(self, folder: str) -> None:
        self._output_folder = folder
        self.save_settings({"output_folder": folder})
        self._publish_event(ConverterEvents.OUTPUT_FOLDER_SET, folder)

    def choose_output_folder(self) -> Optional[str]:
        """Open a folder picker and update the output folder setting."""
        folder = filedialog.askdirectory(
            title="Choose Output Folder",
            initialdir=self._output_folder,
        )
        if folder:
            self.set_output_folder(folder)
            return folder
        return None

    def get_setting(self, key: str, default: str = "") -> str:
        return self._settings.get(key, default)

    # ── History & stats ────────────────────────────────────────────────────

    def get_history(self, limit: int = 50, status_filter: str = "All",
                    search: str = "") -> list:
        uid = current_session.user_id or 1
        return get_history(uid, limit=limit, status_filter=status_filter,
                           search_query=search)

    def get_stats(self):
        uid = current_session.user_id or 1
        return get_stats(uid)

    # ── Favorites ──────────────────────────────────────────────────────────

    def toggle_favorite_tool(self, tool_id: str) -> bool:
        uid = current_session.user_id or 1
        return toggle_favorite_tool(uid, tool_id)

    def get_favorite_tools(self) -> list:
        uid = current_session.user_id or 1
        return get_favorite_tools(uid)

    # ── Pinned files ───────────────────────────────────────────────────────

    def pin_file(self, file_path: str) -> None:
        uid = current_session.user_id or 1
        pin_file(uid, file_path)

    def unpin_file(self, file_path: str) -> None:
        uid = current_session.user_id or 1
        unpin_file(uid, file_path)

    def get_pinned_files(self) -> list:
        uid = current_session.user_id or 1
        return get_pinned_files(uid)

    # ── OS operations ──────────────────────────────────────────────────────

    def open_file(self, path: str) -> None:
        """Open a file with the default system application."""
        try:
            os.startfile(path)
        except Exception as exc:
            self._publish_event(ConverterEvents.NOTIFY_ERROR,
                                f"Cannot open file: {exc}")

    def open_folder(self, path: str) -> None:
        """Reveal a file or open a folder in Explorer."""
        try:
            folder = str(Path(path).parent) if Path(path).is_file() else path
            os.startfile(folder)
        except Exception as exc:
            self._publish_event(ConverterEvents.NOTIFY_ERROR,
                                f"Cannot open folder: {exc}")

    # ── Computed state ─────────────────────────────────────────────────────

    @property
    def output_folder(self) -> str:
        return self._output_folder

    @property
    def all_jobs(self) -> List[ConversionJob]:
        return list(self._jobs.values())

    @property
    def pending_jobs(self) -> List[ConversionJob]:
        return [j for j in self._jobs.values() if j.status == JobStatus.PENDING]

    @property
    def active_count(self) -> int:
        return self._job_manager.active_count
