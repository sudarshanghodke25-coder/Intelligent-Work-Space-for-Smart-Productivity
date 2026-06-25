"""
file_converter/adapters/audio_adapter.py
Audio format conversion using pydub.
"""

from __future__ import annotations

from file_converter.adapters.base_adapter import BaseAdapter
from file_converter.models.conversion_job import ConversionJob
from file_converter.exceptions.converter_errors import (
    CorruptFileError, ConversionFailureError, JobCancelledError,
)

_BITRATE_MAP = {
    "Maximum": "320k", "High": "192k", "Medium": "128k",
    "Low": "96k", "Minimum": "64k",
}


class AudioAdapter(BaseAdapter):
    """Convert between audio formats using pydub."""

    adapter_name = "AudioAdapter"
    supported_input_formats  = [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"]
    supported_output_formats = [".mp3", ".wav", ".ogg", ".flac", ".m4a"]

    def convert(self, job: ConversionJob) -> str:
        self._check_cancelled(job)
        job.report_progress(0.05, "Loading audio…")
        try:
            from pydub import AudioSegment
        except ImportError:
            raise ConversionFailureError("pydub not installed (pip install pydub).")

        try:
            src_ext = job.source_ext.lower().lstrip(".")
            audio = AudioSegment.from_file(job.source_path, format=src_ext)
        except Exception as exc:
            raise CorruptFileError(f"Cannot open audio '{job.source_name}': {exc}", exc) from exc

        self._check_cancelled(job)
        job.report_progress(0.5, "Encoding output…")

        tgt_ext = job.target_ext.lower().lstrip(".")
        out_path = self._resolve_output_path(job)
        bitrate = _BITRATE_MAP.get(job.quality, "192k")

        try:
            export_kwargs: dict = {}
            if tgt_ext in ("mp3",):
                export_kwargs["bitrate"] = bitrate
            audio.export(str(out_path), format=tgt_ext, **export_kwargs)
        except Exception as exc:
            raise ConversionFailureError(f"Audio export failed: {exc}", exc) from exc

        job.report_progress(1.0, "Done!")
        return str(out_path)


class VideoToAudioAdapter(BaseAdapter):
    """Extract or convert audio from video files using pydub/moviepy."""

    adapter_name = "VideoToAudioAdapter"
    supported_input_formats  = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    supported_output_formats = [".mp3", ".wav", ".ogg", ".flac"]

    def convert(self, job: ConversionJob) -> str:
        self._check_cancelled(job)
        job.report_progress(0.1, "Extracting audio track…")
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(job.source_path)
        except Exception as exc:
            raise CorruptFileError(f"Cannot extract audio: {exc}", exc) from exc

        self._check_cancelled(job)
        job.report_progress(0.6, "Encoding audio…")
        tgt_ext = job.target_ext.lower().lstrip(".")
        out_path = self._resolve_output_path(job)
        bitrate = _BITRATE_MAP.get(job.quality, "192k")

        try:
            audio.export(str(out_path), format=tgt_ext, bitrate=bitrate)
        except Exception as exc:
            raise ConversionFailureError(str(exc), exc) from exc

        job.report_progress(1.0, "Done!")
        return str(out_path)
