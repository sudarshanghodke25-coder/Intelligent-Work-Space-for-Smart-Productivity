"""
file_converter/adapters/archive_adapter.py
ZIP / TAR archive extraction and creation.
"""

from __future__ import annotations

import zipfile
import tarfile
import shutil
from pathlib import Path

from file_converter.adapters.base_adapter import BaseAdapter
from file_converter.models.conversion_job import ConversionJob
from file_converter.exceptions.converter_errors import (
    CorruptFileError, ConversionFailureError, JobCancelledError,
)


class ArchiveAdapter(BaseAdapter):
    """Extract ZIP/TAR archives and create ZIP files."""

    adapter_name = "ArchiveAdapter"
    supported_input_formats  = [".zip", ".tar", ".gz", ".tar.gz", ".tgz"]
    supported_output_formats = [".zip", "folder"]  # 'folder' = extract in-place

    def convert(self, job: ConversionJob) -> str:
        self._check_cancelled(job)
        src = job.source_ext.lower()
        tgt = job.target_ext.lower()
        job.report_progress(0.05, "Opening archive…")

        try:
            if tgt in ("folder", ""):
                # Extract archive
                if src == ".zip":
                    return self._extract_zip(job)
                elif src in (".tar", ".gz", ".tgz", ".tar.gz"):
                    return self._extract_tar(job)
                else:
                    raise ConversionFailureError(f"Cannot extract {src}")
            elif tgt == ".zip":
                return self._create_zip(job)
            else:
                raise ConversionFailureError(f"ArchiveAdapter cannot handle {src} → {tgt}")
        except JobCancelledError:
            raise
        except ConversionFailureError:
            raise
        except Exception as exc:
            raise ConversionFailureError(str(exc), exc) from exc

    def _extract_zip(self, job: ConversionJob) -> str:
        out_dir = self._resolve_output_path(job).with_suffix("")
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(job.source_path, "r") as zf:
                members = zf.namelist()
                for i, member in enumerate(members):
                    self._check_cancelled(job)
                    self._check_paused(job)
                    zf.extract(member, str(out_dir))
                    job.report_progress(0.1 + 0.85 * (i + 1) / len(members),
                                        f"Extracting {member}…")
        except zipfile.BadZipFile as exc:
            raise CorruptFileError("Invalid ZIP file.", exc) from exc
        job.report_progress(1.0, "Done!")
        return str(out_dir)

    def _extract_tar(self, job: ConversionJob) -> str:
        out_dir = self._resolve_output_path(job).with_suffix("")
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            with tarfile.open(job.source_path, "r:*") as tf:
                members = tf.getmembers()
                for i, member in enumerate(members):
                    self._check_cancelled(job)
                    self._check_paused(job)
                    tf.extract(member, str(out_dir))
                    job.report_progress(0.1 + 0.85 * (i + 1) / len(members),
                                        f"Extracting {member.name}…")
        except tarfile.TarError as exc:
            raise CorruptFileError("Invalid TAR file.", exc) from exc
        job.report_progress(1.0, "Done!")
        return str(out_dir)

    def _create_zip(self, job: ConversionJob) -> str:
        """Create ZIP from source path (file or directory)."""
        out_path = self._resolve_output_path(job)
        src = Path(job.source_path)
        job.report_progress(0.2, "Creating ZIP…")
        self._check_cancelled(job)
        if src.is_dir():
            shutil.make_archive(str(out_path.with_suffix("")), "zip", str(src))
        else:
            with zipfile.ZipFile(str(out_path), "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(job.source_path, src.name)
        job.report_progress(1.0, "Done!")
        return str(out_path)
