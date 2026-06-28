"""
file_converter/exceptions/converter_errors.py
Typed exception hierarchy for the File Converter module.
Every error category maps to a specific recovery strategy.
"""

from typing import Optional


class ConverterError(Exception):
    """Base class for all converter exceptions."""
    def __init__(self, message: str, original: Optional[Exception] = None):
        super().__init__(message)
        self.original = original
        self.user_message = message


class UnsupportedFormatError(ConverterError):
    """Raised when a file format is not in the registry."""
    pass


class CorruptFileError(ConverterError):
    """Raised when a file cannot be opened or parsed."""
    pass


class PermissionDeniedError(ConverterError):
    """Raised when read/write permissions are missing."""
    pass


class OutputFolderError(ConverterError):
    """Raised when the output folder does not exist or cannot be created."""
    pass


class OCRFailureError(ConverterError):
    """Raised when OCR processing fails."""
    pass


class ConversionFailureError(ConverterError):
    """Raised for general conversion failures."""
    pass


class DiskFullError(ConverterError):
    """Raised when disk space is exhausted during conversion."""
    pass


class JobCancelledError(ConverterError):
    """Raised when a conversion job is cancelled by the user."""
    pass


class JobPausedError(ConverterError):
    """Raised when a conversion job is paused."""
    pass


class PasswordRequiredError(ConverterError):
    """Raised when a protected file requires a password."""
    pass


class FileSizeExceededError(ConverterError):
    """Raised when a file exceeds the maximum allowed size."""
    pass


class AdapterNotFoundError(ConverterError):
    """Raised when no adapter handles the requested conversion."""
    pass


class InvalidPageRangeError(ConverterError):
    """Raised when an invalid page range is specified."""
    pass


def classify_exception(exc: Exception) -> ConverterError:
    """
    Wrap a raw exception into the appropriate ConverterError subclass.
    Enables consistent error handling across all adapters.
    """
    msg = str(exc)
    if "permission" in msg.lower() or "access" in msg.lower():
        return PermissionDeniedError(f"Permission denied: {msg}", exc)
    elif "no space" in msg.lower() or "disk full" in msg.lower():
        return DiskFullError(f"Disk full: {msg}", exc)
    elif "password" in msg.lower() or "encrypted" in msg.lower():
        return PasswordRequiredError(f"File is password-protected: {msg}", exc)
    elif "corrupt" in msg.lower() or "invalid" in msg.lower():
        return CorruptFileError(f"File appears corrupt: {msg}", exc)
    else:
        return ConversionFailureError(f"Conversion failed: {msg}", exc)
