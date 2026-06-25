"""file_converter/exceptions/__init__.py"""
from .converter_errors import (
    ConverterError, UnsupportedFormatError, CorruptFileError,
    PermissionDeniedError, OutputFolderError, OCRFailureError,
    ConversionFailureError, DiskFullError, JobCancelledError,
    JobPausedError, PasswordRequiredError, FileSizeExceededError,
    AdapterNotFoundError, InvalidPageRangeError, classify_exception,
)
__all__ = [
    "ConverterError", "UnsupportedFormatError", "CorruptFileError",
    "PermissionDeniedError", "OutputFolderError", "OCRFailureError",
    "ConversionFailureError", "DiskFullError", "JobCancelledError",
    "JobPausedError", "PasswordRequiredError", "FileSizeExceededError",
    "AdapterNotFoundError", "InvalidPageRangeError", "classify_exception",
]
