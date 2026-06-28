"""
file_converter/workers/job_worker.py
Background worker that processes ConversionJobs from a thread-safe queue.
Supports pause, resume, cancel, retry, and priority ordering.
Uses the existing AUREX EventBus for UI notifications.
"""


import queue
import threading
from typing import Callable, Optional

from file_converter.models.conversion_job import ConversionJob, JobStatus
from file_converter.services.conversion_engine import engine
from file_converter.services.ai_suggestion_service import ai_suggestion_service
from file_converter.exceptions.converter_errors import (
    JobCancelledError, ConverterError,
)
from file_converter.events.converter_events import ConverterEvents
from file_converter.database.converter_db import insert_history, append_log
from services.history_service import log_activity
from authentication.session import current_session


class JobWorker:
    """
    Single background thread that processes one job at a time from the queue.
    Multiple JobWorkers can run concurrently for parallel batch processing.
    """

    def __init__(
        self,
        job_queue: "PriorityJobQueue",
        event_publisher: Callable[[str, object], None],
        worker_id: int = 0,
    ):
        self._queue = job_queue
        self._publish = event_publisher
        self._worker_id = worker_id
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_job: Optional[ConversionJob] = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop,
            name=f"ConverterWorker-{self._worker_id}",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._current_job:
            self._current_job.cancel()

    def _run_loop(self) -> None:
        """Main worker loop — dequeues and processes jobs."""
        while self._running:
            try:
                job: ConversionJob = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if job.status == JobStatus.CANCELLED:
                self._queue.task_done()
                continue

            self._process(job)
            self._queue.task_done()

    def _process(self, job: ConversionJob) -> None:
        """Execute one job, handle all outcomes, persist result, publish events."""
        self._current_job = job

        # Generate AI suggestion (quick, before conversion)
        try:
            suggestion = ai_suggestion_service.generate_suggestion(job)
            job.ai_suggestion = suggestion
            if suggestion:
                self._publish(ConverterEvents.AI_SUGGESTION_READY, {
                    "job_id": job.job_id, "suggestion": suggestion,
                })
        except Exception:
            pass

        # Wire progress callback → event bus
        def progress_cb(job_id: str, fraction: float, message: str) -> None:
            self._publish(ConverterEvents.JOB_PROGRESS, {
                "job_id": job_id, "fraction": fraction, "message": message,
            })

        job._progress_callback = progress_cb
        self._publish(ConverterEvents.JOB_STARTED, job.job_id)

        try:
            output_path = engine.execute(job)
            self._publish(ConverterEvents.JOB_COMPLETED, job)
            self._publish(ConverterEvents.NOTIFY_SUCCESS,
                          f"✓ {job.source_name} converted successfully!")
            self._persist(job)

        except JobCancelledError:
            self._publish(ConverterEvents.JOB_CANCELLED, job.job_id)
            self._persist(job)

        except ConverterError as exc:
            self._publish(ConverterEvents.JOB_FAILED, {
                "job_id": job.job_id, "error": exc.user_message,
            })
            self._publish(ConverterEvents.NOTIFY_ERROR,
                          f"✗ Failed: {job.source_name} — {exc.user_message}")
            self._persist(job)

        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            self._publish(ConverterEvents.JOB_FAILED, {
                "job_id": job.job_id, "error": str(exc),
            })
            self._persist(job)

        finally:
            self._current_job = None
            self._publish(ConverterEvents.HISTORY_UPDATED, None)

    def _persist(self, job: ConversionJob) -> None:
        """Write job result to converter_history table."""
        try:
            user_id = current_session.user_id or 1
            insert_history(
                user_id=user_id,
                job_id=job.job_id,
                source_name=job.source_name,
                source_ext=job.source_ext,
                target_ext=job.target_ext,
                source_size=job.source_size,
                output_path=job.output_path,
                status=job.status.name,
                error_message=job.error_message,
                duration_ms=job.duration_ms,
                quality=job.quality,
                ai_suggestion=job.ai_suggestion,
            )
            
            # Log successful conversions into global dashboard activities
            if job.status.name == "COMPLETED":
                log_activity(
                    user_id=user_id,
                    activity_type="file_converted",
                    description=f"Converted file '{job.source_name}' to {job.target_ext}",
                    action_type="CONVERT",
                    entity_type="File",
                    entity_id=None
                )
        except Exception as exc:
            append_log(job.job_id, "WARN", f"Failed to persist history: {exc}")


class PriorityJobQueue:
    """
    Thread-safe job queue with priority ordering.
    Lower priority integer = higher precedence.
    """

    def __init__(self):
        self._queue: queue.PriorityQueue = queue.PriorityQueue()
        self._counter = 0
        self._lock = threading.Lock()

    def put(self, job: ConversionJob) -> None:
        with self._lock:
            # Use (priority, counter) for stable FIFO within same priority
            self._queue.put((job.priority, self._counter, job))
            self._counter += 1

    def get(self, timeout: float = 0.5) -> ConversionJob:
        priority, _, job = self._queue.get(timeout=timeout)
        return job

    def task_done(self) -> None:
        self._queue.task_done()

    def qsize(self) -> int:
        return self._queue.qsize()

    def clear(self) -> None:
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    break


class JobManager:
    """
    Manages a pool of JobWorkers and the shared PriorityJobQueue.
    This is the public API used by the controller.
    """

    MAX_WORKERS = 2  # Convert up to 2 files in parallel

    def __init__(self, event_publisher: Callable[[str, object], None]):
        self._publish = event_publisher
        self._job_queue = PriorityJobQueue()
        self._workers: list[JobWorker] = []
        self._all_jobs: dict[str, ConversionJob] = {}  # job_id → job
        self._lock = threading.Lock()
        self._started = False

    def start(self) -> None:
        """Spin up worker threads."""
        if self._started:
            return
        for i in range(self.MAX_WORKERS):
            w = JobWorker(self._job_queue, self._publish, worker_id=i)
            w.start()
            self._workers.append(w)
        self._started = True

    def stop(self) -> None:
        """Gracefully stop all workers."""
        for w in self._workers:
            w.stop()
        self._started = False

    def submit(self, job: ConversionJob) -> None:
        """Queue a job for execution."""
        with self._lock:
            job.status = JobStatus.QUEUED
            job.queue_position = self._job_queue.qsize() + 1
            self._all_jobs[job.job_id] = job
        self._job_queue.put(job)
        self._publish(ConverterEvents.JOB_QUEUED, job)

    def submit_batch(self, jobs: list[ConversionJob]) -> None:
        """Submit multiple jobs at once."""
        for job in jobs:
            self.submit(job)
        self._publish(ConverterEvents.BATCH_STARTED, len(jobs))

    def cancel_job(self, job_id: str) -> None:
        """Cancel a specific job by ID."""
        job = self._all_jobs.get(job_id)
        if job:
            job.cancel()

    def pause_job(self, job_id: str) -> None:
        """Pause a running job."""
        job = self._all_jobs.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.pause()
            self._publish(ConverterEvents.JOB_PAUSED, job_id)

    def resume_job(self, job_id: str) -> None:
        """Resume a paused job."""
        job = self._all_jobs.get(job_id)
        if job and job.status == JobStatus.PAUSED:
            job.resume()
            self._publish(ConverterEvents.JOB_RESUMED, job_id)

    def cancel_all(self) -> None:
        """Cancel all queued and running jobs."""
        with self._lock:
            for job in self._all_jobs.values():
                job.cancel()
        self._job_queue.clear()
        self._publish(ConverterEvents.BATCH_CANCELLED, None)

    def get_job(self, job_id: str) -> Optional[ConversionJob]:
        return self._all_jobs.get(job_id)

    def get_all_jobs(self) -> list[ConversionJob]:
        with self._lock:
            return list(self._all_jobs.values())

    def remove_job(self, job_id: str) -> None:
        """Remove a job from the tracking dict (does not cancel if running)."""
        with self._lock:
            self._all_jobs.pop(job_id, None)

    def clear_completed(self) -> None:
        """Remove COMPLETED/FAILED/CANCELLED jobs from tracking dict."""
        terminal = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
        with self._lock:
            to_remove = [
                jid for jid, job in self._all_jobs.items()
                if job.status in terminal
            ]
            for jid in to_remove:
                del self._all_jobs[jid]

    @property
    def active_count(self) -> int:
        active = {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.PAUSED}
        return sum(1 for j in self._all_jobs.values() if j.status in active)

    @property
    def queue_size(self) -> int:
        return self._job_queue.qsize()
