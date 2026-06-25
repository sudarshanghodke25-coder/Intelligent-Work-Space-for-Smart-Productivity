"""
file_converter/adapters/base_adapter.py
Abstract base class for all format conversion adapters.
Every concrete adapter must implement convert() and can_handle().
The ConversionEngine selects adapters via the plugin registry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from file_converter.models.conversion_job import ConversionJob
from file_converter.exceptions.converter_errors import (
    JobCancelledError, classify_exception,
)


class BaseAdapter(ABC):
    """
    Contract for all file-format adapters.
    
    Lifecycle:
        engine selects adapter → engine calls convert(job) →
        adapter calls job.report_progress() periodically →
        adapter returns output_path on success or raises ConverterError.
    """

    # Subclasses declare these at class level
    supported_input_formats:  List[str] = []   # e.g. [".pdf", ".doc"]
    supported_output_formats: List[str] = []   # e.g. [".docx", ".txt"]
    adapter_name: str = "BaseAdapter"

    # ── Registry hook ──────────────────────────────────────────────────────
    _registry: dict[str, type["BaseAdapter"]] = {}

    def __init_subclass__(cls, **kwargs):
        """Auto-register every subclass in the adapter registry."""
        super().__init_subclass__(**kwargs)
        if cls.adapter_name and cls.adapter_name != "BaseAdapter":
            BaseAdapter._registry[cls.adapter_name] = cls

    @classmethod
    def find_adapter(
        cls, source_ext: str, target_ext: str
    ) -> Optional[type["BaseAdapter"]]:
        """
        Locate the best registered adapter for a given conversion pair.
        Returns None if no adapter can handle the pair.
        """
        src = source_ext.lower()
        tgt = target_ext.lower()
        for adapter_cls in cls._registry.values():
            if src in adapter_cls.supported_input_formats and \
               tgt in adapter_cls.supported_output_formats:
                return adapter_cls
        return None

    # ── Public API ─────────────────────────────────────────────────────────

    @abstractmethod
    def convert(self, job: ConversionJob) -> str:
        """
        Execute the conversion described by `job`.

        Args:
            job: Fully populated ConversionJob with all settings.

        Returns:
            Absolute path to the output file on success.

        Raises:
            ConverterError subclass on any failure.
            JobCancelledError if job.is_cancelled() during processing.
        """
        ...

    def can_handle(self, source_ext: str, target_ext: str) -> bool:
        """Return True if this adapter can convert source → target."""
        return (
            source_ext.lower() in self.supported_input_formats
            and target_ext.lower() in self.supported_output_formats
        )

    # ── Helper utilities shared by all adapters ────────────────────────────

    def _resolve_output_path(self, job: ConversionJob) -> Path:
        """
        Determine the output file path from job settings.
        Handles auto-rename and overwrite logic.
        """
        source = Path(job.source_path)
        stem = source.stem

        folder = Path(job.output_folder) if job.output_folder else source.parent
        folder.mkdir(parents=True, exist_ok=True)

        target = folder / (stem + job.target_ext)

        if target.exists() and not job.overwrite:
            if job.auto_rename:
                counter = 1
                while target.exists():
                    target = folder / f"{stem}_{counter}{job.target_ext}"
                    counter += 1
            # else: overwrite silently (caller already confirmed)

        return target

    def _check_cancelled(self, job: ConversionJob) -> None:
        """Raise JobCancelledError if the job has been cancelled."""
        if job.is_cancelled():
            raise JobCancelledError("Job was cancelled by user.")

    def _check_paused(self, job: ConversionJob) -> None:
        """Block until the job is resumed (or raise if cancelled during wait)."""
        job.wait_if_paused()
        self._check_cancelled(job)

    def _safe_convert(self, job: ConversionJob) -> str:
        """
        Wrapper that converts raw exceptions to ConverterError subclasses.
        Adapters should call super()._safe_convert(job) in their convert() if
        they want automatic exception wrapping, or handle it themselves.
        """
        try:
            return self.convert(job)
        except JobCancelledError:
            raise
        except Exception as exc:
            raise classify_exception(exc) from exc
