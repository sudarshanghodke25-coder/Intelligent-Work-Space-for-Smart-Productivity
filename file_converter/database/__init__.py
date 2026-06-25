"""file_converter/database/__init__.py"""
from .converter_db import (
    init_converter_tables, insert_history, get_history, delete_history_entry,
    get_stats, save_setting, load_setting, load_all_settings,
    get_favorite_tools, toggle_favorite_tool,
    pin_file, unpin_file, get_pinned_files, append_log,
)
