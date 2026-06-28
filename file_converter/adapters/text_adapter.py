"""
file_converter/adapters/text_adapter.py
Text and code format adapters: JSON formatter, Markdown→HTML,
code formatter, and generic text transformations.
"""


import json
from pathlib import Path

from file_converter.adapters.base_adapter import BaseAdapter
from file_converter.models.conversion_job import ConversionJob
from file_converter.exceptions.converter_errors import (
    CorruptFileError, ConversionFailureError,
)


class TextAdapter(BaseAdapter):
    """Generic text format conversions (TXT ↔ HTML, JSON format, Markdown→HTML)."""

    adapter_name = "TextAdapter"
    supported_input_formats  = [".txt", ".md", ".html", ".htm", ".json", ".xml",
                                 ".yaml", ".py", ".js", ".java", ".cpp", ".c"]
    supported_output_formats = [".txt", ".html", ".md", ".json", ".pdf"]

    def convert(self, job: ConversionJob) -> str:
        self._check_cancelled(job)
        src = job.source_ext.lower()
        tgt = job.target_ext.lower()
        job.report_progress(0.05, "Reading file…")

        try:
            text = Path(job.source_path).read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise CorruptFileError(str(exc), exc) from exc

        self._check_cancelled(job)
        job.report_progress(0.4, "Converting…")

        if src == ".json" and tgt == ".json":
            return self._format_json(job, text)
        elif src == ".md" and tgt == ".html":
            return self._markdown_to_html(job, text)
        elif src in (".html", ".htm") and tgt == ".txt":
            return self._html_to_text(job, text)
        elif src in (".html", ".htm") and tgt == ".md":
            return self._html_to_markdown(job, text)
        elif src in (".txt", ".md") and tgt == ".html":
            return self._text_to_html(job, text)
        elif src in (".py", ".js", ".java", ".cpp", ".c") and tgt == ".txt":
            return self._pass_through(job, text, ".txt")
        elif src == ".xml" and tgt == ".json":
            return self._xml_to_json(job, text)
        else:
            # Generic: read and write as plain text
            return self._pass_through(job, text, tgt)

    def _format_json(self, job: ConversionJob, text: str) -> str:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConversionFailureError(f"Invalid JSON: {exc}", exc) from exc
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        out_path = self._resolve_output_path(job)
        out_path.write_text(formatted, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _markdown_to_html(self, job: ConversionJob, text: str) -> str:
        try:
            import markdown
            html_body = markdown.markdown(text, extensions=["tables", "fenced_code"])
        except ImportError:
            # Basic fallback without library
            lines = text.splitlines()
            html_parts = []
            for line in lines:
                if line.startswith("# "):
                    html_parts.append(f"<h1>{line[2:]}</h1>")
                elif line.startswith("## "):
                    html_parts.append(f"<h2>{line[3:]}</h2>")
                elif line.startswith("### "):
                    html_parts.append(f"<h3>{line[4:]}</h3>")
                elif line.startswith("- "):
                    html_parts.append(f"<li>{line[2:]}</li>")
                elif line.strip():
                    html_parts.append(f"<p>{line}</p>")
            html_body = "\n".join(html_parts)

        full_html = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'>
<style>
  body {{font-family: 'Segoe UI', sans-serif; max-width: 800px;
         margin: 40px auto; color: #eee; background: #111; line-height: 1.7;}}
  h1,h2,h3 {{color: #a855f7;}} code {{background: #2a2a3d; padding: 2px 6px; border-radius: 4px;}}
  pre {{background: #1a1730; padding: 16px; border-radius: 8px; overflow-x: auto;}}
</style></head><body>{html_body}</body></html>"""
        out_path = self._resolve_output_path(job)
        out_path.write_text(full_html, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _html_to_text(self, job: ConversionJob, text: str) -> str:
        try:
            from bs4 import BeautifulSoup
            plain = BeautifulSoup(text, "html.parser").get_text(separator="\n")
        except ImportError:
            import re
            plain = re.sub(r"<[^>]+>", "", text)
        out_path = self._resolve_output_path(job)
        out_path.write_text(plain, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _html_to_markdown(self, job: ConversionJob, text: str) -> str:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            md_lines = []
            for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
                t = tag.get_text()
                if tag.name == "h1":
                    md_lines.append(f"# {t}")
                elif tag.name == "h2":
                    md_lines.append(f"## {t}")
                elif tag.name == "h3":
                    md_lines.append(f"### {t}")
                elif tag.name == "li":
                    md_lines.append(f"- {t}")
                else:
                    md_lines.append(t)
            result = "\n".join(md_lines)
        except ImportError:
            import re
            result = re.sub(r"<[^>]+>", "", text)
        out_path = self._resolve_output_path(job)
        out_path.write_text(result, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _text_to_html(self, job: ConversionJob, text: str) -> str:
        escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = f"<pre style='font-family:monospace;white-space:pre-wrap;'>{escaped}</pre>"
        full = f"<!DOCTYPE html><html><body>{html}</body></html>"
        out_path = self._resolve_output_path(job)
        out_path.write_text(full, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _xml_to_json(self, job: ConversionJob, text: str) -> str:
        try:
            import xmltodict
            data = xmltodict.parse(text)
            result = json.dumps(data, indent=2, ensure_ascii=False)
        except ImportError:
            raise ConversionFailureError("xmltodict not installed (pip install xmltodict).")
        out_path = self._resolve_output_path(job)
        out_path.write_text(result, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _pass_through(self, job: ConversionJob, text: str, ext: str) -> str:
        """Write text to a new file with a different extension."""
        out_path = self._resolve_output_path(job)
        out_path.write_text(text, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)
