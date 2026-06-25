"""
file_converter/services/conversion_engine.py
Central conversion orchestrator.
Selects the correct adapter from the registry and executes it.
Never contains conversion logic directly — all logic lives in adapters.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

# Import adapters package to trigger auto-registration
import file_converter.adapters  # noqa: F401

from file_converter.adapters.base_adapter import BaseAdapter
from file_converter.models.conversion_job import ConversionJob, JobStatus
from file_converter.exceptions.converter_errors import (
    AdapterNotFoundError, JobCancelledError, ConverterError, classify_exception,
)
from file_converter.database.converter_db import append_log


class ConversionEngine:
    """
    Selects the correct adapter and drives the conversion lifecycle.
    Called exclusively by the JobWorker — never from the UI thread.
    """

    def execute(self, job: ConversionJob) -> str:
        """
        Run a conversion job to completion.

        Returns:
            Output file path.

        Raises:
            AdapterNotFoundError, ConverterError, JobCancelledError.
        """
        if job.is_cancelled():
            raise JobCancelledError("Job was cancelled before starting.")

        # Find adapter
        adapter_cls = BaseAdapter.find_adapter(job.source_ext, job.target_ext)
        if adapter_cls is None:
            raise AdapterNotFoundError(
                f"No adapter can convert '{job.source_ext}' → '{job.target_ext}'. "
                f"Please install the required conversion library."
            )

        adapter = adapter_cls()
        append_log(job.job_id, "INFO",
                   f"Starting conversion: {job.source_name} → {job.target_ext} "
                   f"via {adapter_cls.adapter_name}")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()

        try:
            output_path = adapter.convert(job)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.duration_ms = int(
                (job.completed_at - job.started_at).total_seconds() * 1000
            )
            job.output_path = output_path
            job.progress = 1.0
            job.status_message = "Conversion complete ✓"
            append_log(job.job_id, "INFO",
                       f"Completed in {job.duration_ms} ms → {output_path}")
            return output_path

        except JobCancelledError:
            job.status = JobStatus.CANCELLED
            job.status_message = "Cancelled"
            append_log(job.job_id, "INFO", "Job cancelled by user.")
            raise

        except ConverterError as exc:
            job.status = JobStatus.FAILED
            job.error_message = exc.user_message
            job.status_message = f"Failed: {exc.user_message}"
            append_log(job.job_id, "ERROR", str(exc))
            raise

        except Exception as exc:
            wrapped = classify_exception(exc)
            job.status = JobStatus.FAILED
            job.error_message = wrapped.user_message
            job.status_message = f"Failed: {wrapped.user_message}"
            append_log(job.job_id, "ERROR", str(wrapped))
            raise wrapped from exc


# Module-level singleton — shared across all workers
engine = ConversionEngine()
