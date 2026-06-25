"""
file_converter/events/converter_events.py
All event type string constants for the File Converter event bus.
Using string constants prevents typos and makes grep-ability easy.
"""


class ConverterEvents:
    """
    Namespace for all File Converter event type strings.
    Widgets subscribe and publish using these constants only —
    they never communicate directly with each other.
    """

    # ── File management ────────────────────────────────────────────────────
    FILES_ADDED         = "FC_FILES_ADDED"          # data: List[str] (paths)
    FILE_REMOVED        = "FC_FILE_REMOVED"         # data: str (job_id)
    QUEUE_CLEARED       = "FC_QUEUE_CLEARED"        # data: None

    # ── Job lifecycle ──────────────────────────────────────────────────────
    JOB_QUEUED          = "FC_JOB_QUEUED"           # data: ConversionJob
    JOB_STARTED         = "FC_JOB_STARTED"          # data: str (job_id)
    JOB_PROGRESS        = "FC_JOB_PROGRESS"         # data: dict {job_id, fraction, message}
    JOB_COMPLETED       = "FC_JOB_COMPLETED"        # data: ConversionJob
    JOB_FAILED          = "FC_JOB_FAILED"           # data: dict {job_id, error}
    JOB_CANCELLED       = "FC_JOB_CANCELLED"        # data: str (job_id)
    JOB_PAUSED          = "FC_JOB_PAUSED"           # data: str (job_id)
    JOB_RESUMED         = "FC_JOB_RESUMED"          # data: str (job_id)
    JOB_RETRIED         = "FC_JOB_RETRIED"          # data: str (job_id)

    # ── Queue global ───────────────────────────────────────────────────────
    BATCH_STARTED       = "FC_BATCH_STARTED"        # data: int (total count)
    BATCH_COMPLETED     = "FC_BATCH_COMPLETED"      # data: dict {success, failed}
    BATCH_CANCELLED     = "FC_BATCH_CANCELLED"      # data: None

    # ── Settings ───────────────────────────────────────────────────────────
    SETTINGS_CHANGED    = "FC_SETTINGS_CHANGED"     # data: dict (settings snapshot)
    OUTPUT_FOLDER_SET   = "FC_OUTPUT_FOLDER_SET"    # data: str (path)

    # ── Quick tools ────────────────────────────────────────────────────────
    QUICK_TOOL_SELECTED = "FC_QUICK_TOOL_SELECTED"  # data: QuickToolDef
    QUICK_TOOL_APPLY    = "FC_QUICK_TOOL_APPLY"     # data: str (tool_id)

    # ── History ────────────────────────────────────────────────────────────
    HISTORY_UPDATED     = "FC_HISTORY_UPDATED"      # data: None
    HISTORY_DELETED     = "FC_HISTORY_DELETED"      # data: int (entry id)

    # ── AI suggestions ─────────────────────────────────────────────────────
    AI_SUGGESTION_READY = "FC_AI_SUGGESTION_READY"  # data: dict {job_id, suggestion}

    # ── Notifications ──────────────────────────────────────────────────────
    NOTIFY_SUCCESS      = "FC_NOTIFY_SUCCESS"       # data: str (message)
    NOTIFY_ERROR        = "FC_NOTIFY_ERROR"         # data: str (message)
    NOTIFY_INFO         = "FC_NOTIFY_INFO"          # data: str (message)

    # ── Navigation ─────────────────────────────────────────────────────────
    OPEN_FILE           = "FC_OPEN_FILE"            # data: str (path)
    OPEN_FOLDER         = "FC_OPEN_FOLDER"          # data: str (path)
    COPY_PATH           = "FC_COPY_PATH"            # data: str (path)
