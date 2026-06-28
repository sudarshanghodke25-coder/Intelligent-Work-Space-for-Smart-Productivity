"""
file_converter/adapters/data_adapter.py
Data format conversion using pandas.
"""



from file_converter.adapters.base_adapter import BaseAdapter
from file_converter.models.conversion_job import ConversionJob
from file_converter.exceptions.converter_errors import (
    CorruptFileError, ConversionFailureError,
)

class DataAdapter(BaseAdapter):
    """Convert between tabular/structured data formats using pandas."""

    adapter_name = "DataAdapter"
    supported_input_formats  = [".csv", ".json", ".xlsx", ".xls", ".xml"]
    supported_output_formats = [".csv", ".json", ".xlsx", ".xml", ".html", ".md", ".txt"]

    def convert(self, job: ConversionJob) -> str:
        self._check_cancelled(job)
        job.report_progress(0.1, "Loading data file…")
        
        try:
            import pandas as pd
        except ImportError:
            raise ConversionFailureError("pandas not installed (pip install pandas openpyxl tabulate).")

        src_ext = job.source_ext.lower()
        tgt_ext = job.target_ext.lower()

        try:
            if src_ext == ".csv":
                df = pd.read_csv(job.source_path)
            elif src_ext in [".xlsx", ".xls"]:
                df = pd.read_excel(job.source_path)
            elif src_ext == ".json":
                df = pd.read_json(job.source_path)
            elif src_ext == ".xml":
                df = pd.read_xml(job.source_path)
            else:
                raise ConversionFailureError(f"Unsupported source data format: {src_ext}")
        except Exception as exc:
            raise CorruptFileError(f"Cannot parse data file: {exc}", exc) from exc

        self._check_cancelled(job)
        job.report_progress(0.6, "Formatting output…")

        out_path = self._resolve_output_path(job)

        try:
            if tgt_ext == ".csv":
                df.to_csv(out_path, index=False)
            elif tgt_ext == ".json":
                df.to_json(out_path, orient="records", indent=4)
            elif tgt_ext == ".xlsx":
                df.to_excel(out_path, index=False)
            elif tgt_ext == ".xml":
                df.to_xml(out_path, index=False)
            elif tgt_ext == ".html":
                df.to_html(out_path, index=False, classes="table table-striped")
            elif tgt_ext in [".md", ".txt"]:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(df.to_markdown(index=False))
            else:
                raise ConversionFailureError(f"Unsupported target data format: {tgt_ext}")
        except Exception as exc:
            raise ConversionFailureError(f"Data export failed: {exc}", exc) from exc

        job.report_progress(1.0, "Done!")
        return str(out_path)
