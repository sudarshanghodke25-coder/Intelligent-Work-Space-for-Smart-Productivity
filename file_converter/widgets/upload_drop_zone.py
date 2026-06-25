"""
file_converter/widgets/upload_drop_zone.py
Large drag-and-drop upload area with animated glow border,
format badges, and file-dialog fallback.
Uses tkinterdnd2 for native drag-and-drop if available.
"""

from __future__ import annotations

import math
from pathlib import Path
from tkinter import filedialog
from typing import Callable, List

import customtkinter as ctk

from theme import Colors, Fonts, Dims


# ── Format category display groups ────────────────────────────────────────
FORMAT_GROUPS = [
    ("📄", "PDF  DOCX  DOC  XLSX  PPTX"),
    ("🖼️", "PNG  JPG  WEBP  SVG  GIF  BMP"),
    ("🎵", "MP3  WAV  FLAC  OGG"),
    ("🎬", "MP4  MOV  AVI  MKV"),
    ("💻", "TXT  MD  HTML  JSON  XML  CSV"),
    ("🗜️", "ZIP  TAR  PY  JS  JAVA"),
]


class UploadDropZone(ctk.CTkFrame):
    """
    Large glassmorphic drag-and-drop panel.
    Glows purple when a drag enters the zone.
    Falls back to a file dialog on click.
    """

    def __init__(
        self,
        parent,
        on_files_dropped: Callable[[List[str]], None] = None,
        **kwargs,
    ):
        super().__init__(
            parent,
            fg_color=Colors.GLASS_FILL,
            corner_radius=20,
            border_width=2,
            border_color=Colors.GLASS_BORDER,
            **kwargs,
        )
        self._on_files = on_files_dropped
        self._is_dragging = False
        self._glow_step = 0
        self._glow_after = None

        self._build()
        self._start_idle_animation()
        self._setup_drag_drop()

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build(self):
        # Central content column
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.place(relx=0.5, rely=0.45, anchor="center")

        # Large upload icon
        self._icon_lbl = ctk.CTkLabel(
            content, text="☁️",
            font=("Segoe UI", 64),
            text_color=Colors.TEXT_MUTED,
            fg_color="transparent",
        )
        self._icon_lbl.pack(pady=(0, 10))

        # Primary instruction
        ctk.CTkLabel(
            content,
            text="Drop files here",
            font=("Segoe UI", 22, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent",
        ).pack()

        ctk.CTkLabel(
            content,
            text="or click to browse files",
            font=Fonts.BODY,
            text_color=Colors.TEXT_SECONDARY,
            fg_color="transparent",
        ).pack(pady=(4, 18))

        # Browse button
        browse_btn = ctk.CTkButton(
            content,
            text="  Browse Files",
            font=("Segoe UI", 13, "bold"),
            fg_color=Colors.GLASS_FILL_LIGHT,
            hover_color=Colors.GLASS_FILL_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            border_width=1,
            border_color=Colors.GLASS_BORDER_BRIGHT,
            corner_radius=12,
            height=40,
            width=160,
            command=self._open_file_dialog,
        )
        browse_btn.pack(pady=(0, 24))

        # Format badge strip at the bottom
        badge_frame = ctk.CTkFrame(self, fg_color="transparent")
        badge_frame.place(relx=0.5, rely=0.9, anchor="center")

        for icon, label in FORMAT_GROUPS:
            chip = ctk.CTkFrame(
                badge_frame,
                fg_color=Colors.GLASS_FILL_LIGHT,
                corner_radius=20,
                border_width=1,
                border_color=Colors.GLASS_BORDER,
            )
            chip.pack(side="left", padx=4)
            ctk.CTkLabel(
                chip, text=f"{icon}  {label}",
                font=("Segoe UI", 9),
                text_color=Colors.TEXT_MUTED,
                fg_color="transparent",
            ).pack(padx=10, pady=5)

        # Bind click on the whole zone → file dialog
        self.bind("<Button-1>", self._on_click)

    # ── Idle glow animation (subtle border pulse) ──────────────────────────

    def _start_idle_animation(self):
        self._animate_idle()

    def _animate_idle(self):
        if self._is_dragging:
            return
        t = (math.sin(self._glow_step * 0.04) + 1) / 2  # 0.0 – 1.0
        # Blend between GLASS_BORDER and a slightly brighter purple
        r1, g1, b1 = 0x3a, 0x3a, 0x4a
        r2, g2, b2 = 0x5a, 0x3a, 0x7a
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        try:
            self.configure(border_color=f"#{r:02x}{g:02x}{b:02x}")
        except Exception:
            return
        self._glow_step += 1
        self._glow_after = self.after(60, self._animate_idle)

    def _enter_drag_mode(self):
        self._is_dragging = True
        self.configure(
            fg_color=Colors.ACCENT_SUBTLE,
            border_color=Colors.ACCENT_GLOW,
            border_width=3,
        )
        self._icon_lbl.configure(text_color=Colors.ACCENT_GLOW)

    def _exit_drag_mode(self):
        self._is_dragging = False
        self.configure(
            fg_color=Colors.GLASS_FILL,
            border_color=Colors.GLASS_BORDER,
            border_width=2,
        )
        self._icon_lbl.configure(text_color=Colors.TEXT_MUTED)
        self._start_idle_animation()

    # ── Drag-and-drop setup ────────────────────────────────────────────────

    def _setup_drag_drop(self):
        """Register tkinterdnd2 events if available."""
        try:
            self.drop_target_register("DND_Files")
            self.dnd_bind("<<DropEnter>>", self._on_drag_enter)
            self.dnd_bind("<<DropLeave>>", self._on_drag_leave)
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            # tkinterdnd2 not available or not initialized — click fallback only
            pass

    def _on_drag_enter(self, event=None):
        self._enter_drag_mode()

    def _on_drag_leave(self, event=None):
        self._exit_drag_mode()

    def _on_drop(self, event=None):
        self._exit_drag_mode()
        if event and hasattr(event, "data"):
            paths = self._parse_drop_data(event.data)
            if paths and self._on_files:
                self._on_files(paths)

    @staticmethod
    def _parse_drop_data(data: str) -> List[str]:
        """Parse tkinterdnd2 drop data into a list of file paths."""
        # Handle braces-wrapped paths with spaces: {/path/to file.pdf} /another.docx
        paths = []
        data = data.strip()
        while data:
            if data.startswith("{"):
                end = data.index("}")
                paths.append(data[1:end])
                data = data[end + 1:].strip()
            else:
                parts = data.split(" ", 1)
                paths.append(parts[0])
                data = parts[1].strip() if len(parts) > 1 else ""
        return [p for p in paths if Path(p).exists()]

    # ── Click / dialog ─────────────────────────────────────────────────────

    def _on_click(self, event=None):
        # Only open dialog if clicking on the background, not a child button
        self._open_file_dialog()

    def _open_file_dialog(self):
        paths = filedialog.askopenfilenames(
            title="Select Files to Convert",
            filetypes=[
                ("All Supported Files",
                 "*.pdf *.docx *.doc *.xlsx *.xls *.csv *.pptx *.ppt "
                 "*.txt *.md *.html *.htm *.json *.xml *.yaml "
                 "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.svg *.tiff *.ico "
                 "*.mp3 *.wav *.ogg *.flac *.m4a "
                 "*.mp4 *.mov *.avi *.mkv "
                 "*.zip *.tar *.gz "
                 "*.py *.js *.java *.cpp"),
                ("All Files", "*.*"),
            ],
        )
        if paths and self._on_files:
            self._on_files(list(paths))
