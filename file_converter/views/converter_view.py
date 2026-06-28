"""
file_converter/views/converter_view.py
Top-level view that assembles the complete File Converter layout:

 ┌─────────────────────────────────────────────────────┬──────────┐
 │ HEADER: Title + subtitle + Add Files button          │ QUICK    │
 ├─────────────────────────────────────────────────────┤ TOOLS    │
 │   UPLOAD DROP ZONE                                   ├──────────┤
 ├─────────────────────────────────────────────────────┤          │
 │   FILE QUEUE PANEL                                   │ HISTORY  │
 ├─────────────────────────────────────────────────────┤ SIDEBAR  │
 │   SETTINGS PANEL (with Output Folder + Convert Now)  │          │
 └─────────────────────────────────────────────────────┴──────────┘

Pure View — delegates all actions to ConverterController.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from theme import Colors, Fonts, Dims

from file_converter.controllers.converter_controller import ConverterController
from file_converter.widgets.upload_drop_zone import UploadDropZone
from file_converter.widgets.file_queue_panel import FileQueuePanel
from file_converter.widgets.settings_panel import SettingsPanel
from file_converter.widgets.quick_tools_panel import QuickToolsPanel
from file_converter.widgets.history_sidebar import HistorySidebar
from file_converter.widgets.toast_notification import ToastManager
from file_converter.database.converter_db import delete_history_entry
from file_converter.events.converter_events import ConverterEvents
from services.event_bus import bus

class FileConverterView(ctk.CTkFrame):
    """
    Root view for the File Converter module.
    Instantiates the controller and all sub-panels.
    Wires all callbacks between controller and widgets.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._ctrl = ConverterController()

        self._build()

        self._toasts = ToastManager(self)
        self._subscribe_events()

    # ── Layout construction ─────────────────────────────────────────────────

    def _build(self):
        # ── Outer 2-column layout: [main content] [right sidebar] ─────────
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=3, minsize=600)
        outer.columnconfigure(1, weight=1, minsize=320)
        outer.rowconfigure(0, weight=1)

        # Main pane (left)
        main_pane = ctk.CTkFrame(outer, fg_color="transparent")
        main_pane.grid(row=0, column=0, sticky="nsew")

        # Right sidebar
        right_pane = ctk.CTkFrame(outer, fg_color="transparent")
        right_pane.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        # ── Build sections inside main pane ────────────────────────────
        self._build_header(main_pane)
        
        main_scroll = ctk.CTkScrollableFrame(
            main_pane, fg_color="transparent",
            scrollbar_button_color=Colors.CARD_FLOATING,
            scrollbar_button_hover_color=Colors.CARD_HOVER,
        )
        main_scroll.pack(fill="both", expand=True, padx=4)

        self._build_drop_zone(main_scroll)
        self._build_queue_panel(main_scroll)
        self._build_settings_panel(main_scroll)

        # ── Build right sidebar ────────────────────────────────────────
        self._build_quick_tools(right_pane)
        self._build_history_sidebar(right_pane)

    # ── Header ─────────────────────────────────────────────────────────────

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent", height=70)
        header.pack(fill="x", padx=4, pady=(8, 12))
        header.pack_propagate(False)

        # Left: title + subtitle
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="y")

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row, text="File Converter", font=("Segoe UI", 24, "bold"),
            text_color=Colors.TEXT_PRIMARY, fg_color="transparent",
        ).pack(side="left")

        ctk.CTkLabel(
            left, text="Convert, compress and transform your files instantly",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY, anchor="w", fg_color="transparent",
        ).pack(fill="x", pady=(2, 0))

        # Right: Add Files button
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", fill="y")

        add_btn = ctk.CTkButton(
            right, text="  + Add Files", font=Fonts.BUTTON, height=Dims.BTN_HEIGHT, width=140,
            corner_radius=Dims.BTN_CORNER, fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER, text_color=Colors.TEXT_PRIMARY,
            command=self._on_add_files_click,
        )
        add_btn.pack(side="right", padx=4)

        self.winfo_toplevel().bind("<Control-o>", lambda _: self._on_add_files_click())
        self.winfo_toplevel().bind("<Control-O>", lambda _: self._on_add_files_click())

    # ── Main Pane Components ───────────────────────────────────────────────

    def _build_drop_zone(self, parent):
        self._drop_zone = UploadDropZone(
            parent,
            on_files_dropped=self._ctrl.add_files,
            height=280,
        )
        self._drop_zone.pack(fill="x", pady=(0, 20))
        self._drop_zone.pack_propagate(False)

    def _build_queue_panel(self, parent):
        self._queue_panel = FileQueuePanel(
            parent,
            on_remove=self._ctrl.remove_job,
            on_target_change=self._ctrl.update_job_target,
            on_pause=self._ctrl.pause_job,
            on_resume=self._ctrl.resume_job,
            on_cancel=self._ctrl.cancel_job,
            on_retry=self._ctrl.retry_job,
        )
        self._queue_panel.pack(fill="x", pady=(0, 20))
        # Provide fixed height for queue if multiple items
        self._queue_panel.configure(height=260)

    def _build_settings_panel(self, parent):
        initial_settings = self._ctrl._settings.copy()
        initial_settings["output_folder"] = self._ctrl.output_folder

        self._settings_panel = SettingsPanel(
            parent,
            initial_settings=initial_settings,
            on_settings_change=self._on_settings_changed,
            on_choose_folder=self._on_choose_folder,
            on_convert=self._ctrl.start_conversion,
        )
        self._settings_panel.pack(fill="x", pady=(0, 20))

    # ── Sidebar Components ─────────────────────────────────────────────────

    def _build_quick_tools(self, parent):
        self._tools_panel = QuickToolsPanel(
            parent,
            on_tool_click=self._ctrl.apply_quick_tool,
        )
        self._tools_panel.pack(fill="x", pady=(0, 16))

    def _build_history_sidebar(self, parent):
        self._history_sidebar = HistorySidebar(
            parent,
            on_open_file=self._ctrl.open_file,
            on_open_folder=self._ctrl.open_folder,
            on_delete_entry=self._on_delete_history,
            on_clear_all=self._on_clear_history,
            on_refresh=lambda status, search: self._ctrl.get_history(
                limit=10,
                status_filter=status,
                search=search,
            ),
            on_get_stats=self._ctrl.get_stats,
        )
        self._history_sidebar.pack(fill="both", expand=True)

    # ── Events & Callbacks ─────────────────────────────────────────────────

    def _subscribe_events(self):
        bus.subscribe(ConverterEvents.BATCH_STARTED, lambda _: self._settings_panel.set_converting_state(True))
        
        def check_batch_state(_):
            if self._ctrl.active_count == 0:
                self._settings_panel.set_converting_state(False)

        bus.subscribe(ConverterEvents.JOB_COMPLETED, check_batch_state)
        bus.subscribe(ConverterEvents.JOB_FAILED, check_batch_state)
        bus.subscribe(ConverterEvents.JOB_CANCELLED, check_batch_state)
        bus.subscribe(ConverterEvents.BATCH_COMPLETED, lambda _: self._settings_panel.set_converting_state(False))
        bus.subscribe(ConverterEvents.BATCH_CANCELLED, lambda _: self._settings_panel.set_converting_state(False))

    def _on_add_files_click(self):
        paths = filedialog.askopenfilenames(
            title="Add Files to Convert",
            filetypes=[
                ("All Supported Files",
                 "*.pdf *.docx *.doc *.xlsx *.xls *.csv *.pptx *.ppt "
                 "*.txt *.md *.html *.htm *.json *.xml *.yaml "
                 "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.svg *.tiff "
                 "*.mp3 *.wav *.ogg *.flac *.m4a "
                 "*.mp4 *.mov *.avi *.mkv "
                 "*.zip *.tar *.gz "
                 "*.py *.js *.java *.cpp"),
                ("All Files", "*.*"),
            ],
        )
        if paths:
            self._ctrl.add_files(list(paths))

    def _on_settings_changed(self, settings: dict) -> None:
        self._ctrl.save_settings(settings)
        if "output_folder" in settings:
            self._settings_panel.update_folder_display(settings["output_folder"])
        # Apply global target to all pending jobs if changed
        if "global_target" in settings:
            target = settings["global_target"]
            ext = "." + target.split("(")[1].replace(")", "")
            # Since controller handles queue, we might want to update all pending jobs
            # We don't have a direct function for this, but the file cards have their own overrides.

    def _on_choose_folder(self) -> None:
        new_folder = self._ctrl.choose_output_folder()
        if new_folder:
            self._settings_panel.update_folder_display(new_folder)

    def _on_delete_history(self, entry_id: int) -> None:
        try:
            delete_history_entry(entry_id)
        except Exception:
            pass

    def _on_clear_history(self) -> None:
        try:
            from file_converter.database.converter_db import clear_history
            clear_history()
            bus.publish(ConverterEvents.HISTORY_UPDATED, None)
        except Exception as e:
            print(f"Error clearing history: {e}")
