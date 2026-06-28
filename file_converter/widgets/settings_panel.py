"""
file_converter/widgets/settings_panel.py
Conversion settings panel — target format, quality, compression,
output folder, OCR toggle, page range, and Convert Now button.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from theme import Colors, Fonts, Dims
from file_converter.constants.formats import QUALITY_LEVELS, COMPRESSION_LEVELS, FORMATS
from file_converter.widgets.animated_button import AnimatedGlowButton


class SettingsPanel(ctk.CTkFrame):
    """
    Settings panel mimicking the reference UI.
    Contains grid for options, output folder, and Convert Now button.
    """

    def __init__(
        self,
        parent,
        initial_settings: dict = None,
        on_settings_change: Callable[[dict], None] = None,
        on_choose_folder: Callable[[], None] = None,
        on_convert: Callable[[], None] = None,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=Colors.CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            **kwargs,
        )
        self._on_change = on_settings_change
        self._on_folder = on_choose_folder
        self._on_convert = on_convert

        # Default settings
        self._settings = {
            "global_target": "PDF (.pdf)",
            "quality": "High",
            "compression": "Medium",
            "enable_ocr": "0",
            "keep_formatting": "1",
            "open_after": "0",
            "output_folder": str(Path.home() / "Downloads"),
        }
        if initial_settings:
            self._settings.update(initial_settings)

        self._build()

    def _build(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=24)

        # ── Row 1: Convert To, Output Quality ────────────────────────────────
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 20))
        row1.columnconfigure((0, 1), weight=1, uniform="col")

        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._global_target_var = ctk.StringVar(value=self._settings.get("global_target", "PDF (.pdf)"))
        self._add_dropdown_col(col1, "Convert To", self._global_target_var, ["PDF (.pdf)", "DOCX (.docx)", "JPG (.jpg)", "PNG (.png)"], "global_target")

        col2 = ctk.CTkFrame(row1, fg_color="transparent")
        col2.grid(row=0, column=1, sticky="nsew", padx=(10, 10))
        self._quality_var = ctk.StringVar(value=self._settings.get("quality", "High Quality"))
        self._add_dropdown_col(col2, "Output Quality", self._quality_var, ["High Quality", "Medium Quality", "Low Quality"], "quality")

        # ── Row 2: OCR, Keep Formatting, Compress ────────────────────────
        row2 = ctk.CTkFrame(container, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 24))
        row2.columnconfigure((0, 1, 2), weight=1, uniform="col")

        tcol1 = ctk.CTkFrame(row2, fg_color="transparent")
        tcol1.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._ocr_var = ctk.BooleanVar(value=self._settings.get("enable_ocr") == "1")
        self._add_toggle_col(tcol1, "OCR (Scan to Text)", "Extract text from scanned documents", self._ocr_var, "enable_ocr")

        tcol2 = ctk.CTkFrame(row2, fg_color="transparent")
        tcol2.grid(row=0, column=1, sticky="nsew", padx=(10, 10))
        self._format_var = ctk.BooleanVar(value=self._settings.get("keep_formatting") == "1")
        self._add_toggle_col(tcol2, "Keep Formatting", "Maintain original formatting", self._format_var, "keep_formatting")

        tcol3 = ctk.CTkFrame(row2, fg_color="transparent")
        tcol3.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        self._compress_var = ctk.BooleanVar(value=self._settings.get("compression") != "None")
        self._add_toggle_col(tcol3, "Compress Output", "Reduce file size", self._compress_var, "compression_toggle")

        sep = ctk.CTkFrame(container, fg_color=Colors.BORDER_SUBTLE, height=1)
        sep.pack(fill="x", pady=(0, 20))

        # ── Output Folder ─────────────────────────────────────────────────
        ctk.CTkLabel(
            container, text="Output Folder", font=Fonts.SMALL, text_color=Colors.TEXT_PRIMARY, anchor="w", fg_color="transparent"
        ).pack(fill="x", pady=(0, 8))

        folder_row = ctk.CTkFrame(container, fg_color="transparent")
        folder_row.pack(fill="x", pady=(0, 20))

        folder_input_frame = ctk.CTkFrame(folder_row, fg_color=Colors.INPUT_BG, corner_radius=8, border_width=1, border_color=Colors.INPUT_BORDER, height=40)
        folder_input_frame.pack(side="left", fill="x", expand=True)
        folder_input_frame.pack_propagate(False)
        
        ctk.CTkLabel(folder_input_frame, text="📁", font=("Segoe UI", 16), text_color=Colors.TEXT_MUTED, fg_color="transparent").pack(side="left", padx=(12, 8))
        self._folder_lbl = ctk.CTkLabel(folder_input_frame, text=self._settings["output_folder"], font=Fonts.ENTRY, text_color=Colors.TEXT_SECONDARY, anchor="w", fg_color="transparent")
        self._folder_lbl.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            folder_row, text="Change", width=80, height=40, corner_radius=8,
            fg_color=Colors.CARD_FLOATING, hover_color=Colors.CARD_HOVER,
            text_color=Colors.TEXT_PRIMARY, font=Fonts.SMALL,
            command=self._choose_folder
        ).pack(side="left", padx=(10, 20))

        self._open_var = ctk.BooleanVar(value=self._settings.get("open_after") == "1")
        open_cb = ctk.CTkCheckBox(
            folder_row, text="Open file after conversion", variable=self._open_var,
            font=Fonts.SMALL, text_color=Colors.TEXT_PRIMARY, fg_color=Colors.ACCENT_PRIMARY,
            command=lambda: self._emit({"open_after": "1" if self._open_var.get() else "0"})
        )
        open_cb.pack(side="right")

        # ── Convert Button ────────────────────────────────────────────────
        self._convert_btn = AnimatedGlowButton(
            container, text="Convert Now", width=400, height=50,
            command=self._on_convert_click
        )
        self._convert_btn.pack(pady=(10, 0))

    def _add_dropdown_col(self, parent, label: str, var: ctk.StringVar, options: list, key: str):
        ctk.CTkLabel(
            parent, text=label, font=Fonts.SMALL, text_color=Colors.TEXT_PRIMARY, anchor="w", fg_color="transparent"
        ).pack(fill="x", pady=(0, 4))
        ctk.CTkOptionMenu(
            parent, variable=var, values=options, height=36, corner_radius=8,
            fg_color=Colors.CARD_FLOATING, button_color=Colors.BORDER_ACTIVE,
            button_hover_color=Colors.ACCENT_HOVER, text_color=Colors.TEXT_PRIMARY,
            font=Fonts.SMALL, command=lambda v, k=key: self._emit({k: v})
        ).pack(fill="x")

    def _add_toggle_col(self, parent, title: str, subtitle: str, var: ctk.BooleanVar, key: str):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(
            header, text=title, font=Fonts.SMALL, text_color=Colors.TEXT_PRIMARY, anchor="w", fg_color="transparent"
        ).pack(side="left")
        ctk.CTkSwitch(
            header, text="", variable=var, onvalue=True, offvalue=False,
            fg_color=Colors.CARD_FLOATING, progress_color=Colors.ACCENT_PRIMARY,
            button_color=Colors.TEXT_PRIMARY, width=36, height=20,
            command=lambda k=key, v=var: self._emit({k: "1" if v.get() else "0"}) if k != "compression_toggle" else self._emit({"compression": "Medium" if v.get() else "None"})
        ).pack(side="right")
        ctk.CTkLabel(
            parent, text=subtitle, font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED, anchor="w", fg_color="transparent"
        ).pack(fill="x")

    def _emit(self, delta: dict) -> None:
        self._settings.update(delta)
        if self._on_change:
            self._on_change(self._settings.copy())

    def _choose_folder(self) -> None:
        if self._on_folder:
            self._on_folder()

    def update_folder_display(self, path: str) -> None:
        self._settings["output_folder"] = path
        self._folder_lbl.configure(text=path)

    def _on_convert_click(self):
        if self._on_convert:
            self._on_convert()

    def get_settings(self) -> dict:
        return self._settings.copy()
    
    # Expose for controller updates
    def set_converting_state(self, is_converting: bool):
        if is_converting:
            self._convert_btn.set_text("Converting…", "⏳")
            self._convert_btn.set_enabled(False)
        else:
            self._convert_btn.set_text("Convert Now", "⚡")
            self._convert_btn.set_enabled(True)
