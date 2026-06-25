"""
file_converter/adapters/spreadsheet_adapter.py
Handles CSV ↔ Excel and CSV/Excel → PDF/JSON via openpyxl and pandas.
"""

from __future__ import annotations

import json
from pathlib import Path

from file_converter.adapters.base_adapter import BaseAdapter
from file_converter.models.conversion_job import ConversionJob
from file_converter.exceptions.converter_errors import (
    CorruptFileError, ConversionFailureError, JobCancelledError,
)


class SpreadsheetAdapter(BaseAdapter):
    """Converts CSV, Excel, and JSON data files."""

    adapter_name = "SpreadsheetAdapter"
    supported_input_formats  = [".csv", ".xlsx", ".xls", ".json"]
    supported_output_formats = [".csv", ".xlsx", ".json", ".html", ".txt"]

    def convert(self, job: ConversionJob) -> str:
        self._check_cancelled(job)
        src = job.source_ext.lower()
        tgt = job.target_ext.lower()
        job.report_progress(0.05, "Loading data…")

        try:
            if src == ".csv" and tgt == ".xlsx":
                return self._csv_to_excel(job)
            elif src in (".xlsx", ".xls") and tgt == ".csv":
                return self._excel_to_csv(job)
            elif src in (".xlsx", ".xls") and tgt == ".json":
                return self._excel_to_json(job)
            elif src == ".csv" and tgt == ".json":
                return self._csv_to_json(job)
            elif src == ".json" and tgt == ".csv":
                return self._json_to_csv(job)
            elif src == ".json" and tgt == ".xlsx":
                return self._json_to_excel(job)
            elif src in (".csv", ".xlsx", ".xls") and tgt == ".html":
                return self._data_to_html(job)
            else:
                raise ConversionFailureError(
                    f"SpreadsheetAdapter cannot handle {src} → {tgt}"
                )
        except JobCancelledError:
            raise
        except ConversionFailureError:
            raise
        except Exception as exc:
            raise ConversionFailureError(str(exc), exc) from exc

    def _load_df(self, job: ConversionJob):
        """Load source file into a pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ConversionFailureError("pandas not installed.")
        src = job.source_ext.lower()
        try:
            if src == ".csv":
                return pd.read_csv(job.source_path, encoding="utf-8", errors="replace")
            elif src in (".xlsx", ".xls"):
                return pd.read_excel(job.source_path)
            elif src == ".json":
                return pd.read_json(job.source_path)
        except Exception as exc:
            raise CorruptFileError(str(exc), exc) from exc

    def _csv_to_excel(self, job: ConversionJob) -> str:
        df = self._load_df(job)
        self._check_cancelled(job)
        job.report_progress(0.5, "Writing Excel workbook…")
        out_path = self._resolve_output_path(job)
        df.to_excel(str(out_path), index=False, engine="openpyxl")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _excel_to_csv(self, job: ConversionJob) -> str:
        df = self._load_df(job)
        self._check_cancelled(job)
        job.report_progress(0.5, "Writing CSV…")
        out_path = self._resolve_output_path(job)
        df.to_csv(str(out_path), index=False, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _excel_to_json(self, job: ConversionJob) -> str:
        df = self._load_df(job)
        self._check_cancelled(job)
        job.report_progress(0.5, "Serialising to JSON…")
        out_path = self._resolve_output_path(job)
        df.to_json(str(out_path), orient="records", indent=2, force_ascii=False)
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _csv_to_json(self, job: ConversionJob) -> str:
        df = self._load_df(job)
        self._check_cancelled(job)
        job.report_progress(0.5, "Serialising to JSON…")
        out_path = self._resolve_output_path(job)
        df.to_json(str(out_path), orient="records", indent=2, force_ascii=False)
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _json_to_csv(self, job: ConversionJob) -> str:
        df = self._load_df(job)
        self._check_cancelled(job)
        job.report_progress(0.5, "Writing CSV…")
        out_path = self._resolve_output_path(job)
        df.to_csv(str(out_path), index=False, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _json_to_excel(self, job: ConversionJob) -> str:
        df = self._load_df(job)
        self._check_cancelled(job)
        job.report_progress(0.5, "Writing Excel…")
        out_path = self._resolve_output_path(job)
        df.to_excel(str(out_path), index=False, engine="openpyxl")
        job.report_progress(1.0, "Done!")
        return str(out_path)

    def _data_to_html(self, job: ConversionJob) -> str:
        df = self._load_df(job)
        self._check_cancelled(job)
        job.report_progress(0.5, "Rendering HTML table…")
        html = df.to_html(index=False, border=0, classes="data-table")
        styled = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'>
<style>
  body {{font-family: sans-serif; padding: 20px; background: #111;color:#eee;}}
  .data-table {{border-collapse: collapse; width: 100%;}}
  .data-table th {{background: #7c3aed; color: white; padding: 8px 12px;}}
  .data-table td {{padding: 6px 12px; border-bottom: 1px solid #333;}}
  .data-table tr:hover td {{background: #1a1730;}}
</style></head><body>{html}</body></html>"""
        out_path = self._resolve_output_path(job)
        out_path.write_text(styled, encoding="utf-8")
        job.report_progress(1.0, "Done!")
        return str(out_path)
