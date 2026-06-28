"""
file_converter/adapters/video_adapter.py
Video format conversion using moviepy (which wraps ffmpeg).
"""

from __future__ import annotations

from pathlib import Path

from file_converter.adapters.base_adapter import BaseAdapter
from file_converter.models.conversion_job import ConversionJob
from file_converter.exceptions.converter_errors import (
    CorruptFileError, ConversionFailureError, JobCancelledError,
)

class VideoAdapter(BaseAdapter):
    """Convert between video formats using moviepy/ffmpeg."""

    adapter_name = "VideoAdapter"
    supported_input_formats  = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    supported_output_formats = [".mp4", ".mov", ".avi", ".mkv", ".gif", ".mp3", ".wav"]

    def convert(self, job: ConversionJob) -> str:
        self._check_cancelled(job)
        job.report_progress(0.1, "Loading video file…")
        
        try:
            from moviepy.editor import VideoFileClip
        except ImportError:
            raise ConversionFailureError("moviepy not installed (pip install moviepy).")

        src_ext = job.source_ext.lower()
        tgt_ext = job.target_ext.lower()

        try:
            clip = VideoFileClip(job.source_path)
        except Exception as exc:
            raise CorruptFileError(f"Cannot open video '{job.source_name}': {exc}", exc) from exc

        self._check_cancelled(job)
        job.report_progress(0.3, "Encoding video… (This may take a while)")

        out_path = self._resolve_output_path(job)

        try:
            if tgt_ext in [".mp3", ".wav"]:
                # Extract Audio only
                if clip.audio is None:
                    raise ConversionFailureError("Video has no audio track to extract.")
                clip.audio.write_audiofile(str(out_path), logger=None)
            elif tgt_ext == ".gif":
                # Convert to GIF (optimized)
                clip.write_gif(str(out_path), fps=min(clip.fps or 15, 15), logger=None)
            else:
                # Video to Video
                codec_map = {
                    ".mp4": "libx264",
                    ".mov": "libx264",
                    ".avi": "mpeg4",
                    ".mkv": "libx264"
                }
                codec = codec_map.get(tgt_ext, "libx264")
                clip.write_videofile(str(out_path), codec=codec, audio_codec="aac", logger=None)
        except Exception as exc:
            raise ConversionFailureError(f"Video encoding failed: {exc}", exc) from exc
        finally:
            try:
                clip.close()
            except Exception:
                pass

        job.report_progress(1.0, "Done!")
        return str(out_path)
