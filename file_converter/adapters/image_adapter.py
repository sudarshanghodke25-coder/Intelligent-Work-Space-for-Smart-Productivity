"""
file_converter/adapters/image_adapter.py
Image conversion adapter using Pillow (PIL).
Handles format conversion, resize, compression, and WebP optimisation.
"""



from file_converter.adapters.base_adapter import BaseAdapter
from file_converter.models.conversion_job import ConversionJob
from file_converter.exceptions.converter_errors import (
    CorruptFileError, ConversionFailureError,
)


class ImageAdapter(BaseAdapter):
    """
    Convert between image formats using Pillow.
    Supports quality control, resize, and compression.
    """

    adapter_name = "ImageAdapter"
    supported_input_formats = [
        ".png", ".jpg", ".jpeg", ".webp", ".bmp",
        ".gif", ".tiff", ".ico", ".svg",
    ]
    supported_output_formats = [
        ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".ico",
    ]

    # Quality map: our label → Pillow integer (JPEG/WebP)
    _QUALITY_MAP = {
        "Maximum": 98, "High": 88, "Medium": 72, "Low": 55, "Minimum": 35,
    }

    def convert(self, job: ConversionJob) -> str:
        self._check_cancelled(job)
        job.report_progress(0.05, "Opening image…")

        try:
            from PIL import Image
        except ImportError:
            raise ConversionFailureError("Pillow is not installed (pip install pillow).")

        src_ext = job.source_ext.lower()
        tgt_ext = job.target_ext.lower()

        # SVG needs special handling via cairosvg / Inkscape
        if src_ext == ".svg":
            return self._convert_svg(job)

        try:
            img = Image.open(job.source_path)
        except Exception as exc:
            raise CorruptFileError(f"Cannot open image '{job.source_name}': {exc}", exc) from exc

        self._check_cancelled(job)
        job.report_progress(0.3, "Processing image…")

        # Preserve transparency for PNG/GIF output; convert to RGB for JPEG
        if tgt_ext in (".jpg", ".jpeg", ".bmp"):
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            else:
                img = img.convert("RGB")
        elif tgt_ext == ".png":
            if img.mode not in ("RGBA", "RGB", "L", "P"):
                img = img.convert("RGBA")

        # Optional resize from extra_settings
        resize = job.extra_settings.get("resize")
        if resize:
            try:
                w, h = int(resize["width"]), int(resize["height"])
                img = img.resize((w, h), Image.LANCZOS)
            except (KeyError, ValueError, TypeError):
                pass

        self._check_cancelled(job)
        job.report_progress(0.7, "Saving output…")

        out_path = self._resolve_output_path(job)
        quality = self._QUALITY_MAP.get(job.quality, 88)

        save_kwargs: dict = {}
        if tgt_ext in (".jpg", ".jpeg"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif tgt_ext == ".webp":
            save_kwargs["quality"] = quality
            save_kwargs["method"] = 6  # slowest / best compression
        elif tgt_ext == ".png":
            # PNG compression: 0=none, 9=maximum; inverse of our quality scale
            level_map = {"Maximum": 1, "High": 3, "Medium": 5, "Low": 7, "Minimum": 9}
            save_kwargs["compress_level"] = level_map.get(job.compression, 5)
        elif tgt_ext == ".gif":
            save_kwargs["optimize"] = True

        try:
            img.save(str(out_path), **save_kwargs)
        except Exception as exc:
            raise ConversionFailureError(f"Failed to save image: {exc}", exc) from exc

        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _convert_svg(self, job: ConversionJob) -> str:
        """Convert SVG to raster via cairosvg (optional) or raise."""
        try:
            import cairosvg
        except ImportError:
            raise ConversionFailureError(
                "cairosvg is required for SVG conversion (pip install cairosvg)."
            )
        self._check_cancelled(job)
        job.report_progress(0.5, "Rendering SVG…")
        out_path = self._resolve_output_path(job)
        tgt_ext = job.target_ext.lower()
        if tgt_ext == ".png":
            cairosvg.svg2png(url=job.source_path, write_to=str(out_path))
        elif tgt_ext in (".jpg", ".jpeg"):
            cairosvg.svg2png(url=job.source_path, write_to=str(out_path))
        else:
            raise ConversionFailureError(f"SVG → {tgt_ext} not supported.")
        job.report_progress(1.0, "Done!")
        return str(out_path)
