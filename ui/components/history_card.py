import customtkinter as ctk
import tkinter as tk
from PIL import Image
import os
from theme import Colors, Fonts

class HistoryCard(ctk.CTkFrame):
    def __init__(self, parent, history_id, title, model, meta_text, image_path, on_click=None, on_delete=None, on_download=None, **kwargs):
        super().__init__(parent, fg_color="transparent", height=70, cursor="hand2", **kwargs)
        self.pack_propagate(False)
        
        self.history_id = history_id
        self.image_path = image_path
        self._on_click = on_click
        self._on_delete = on_delete
        self._on_download = on_download
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._handle_click)
        self.bind("<Button-3>", self._show_context_menu)
        
        # Thumbnail
        self.thumb_label = ctk.CTkLabel(self, text="", width=60, height=60, corner_radius=8, fg_color=Colors.GLASS_FILL_LIGHT)
        self.thumb_label.pack(side="left", padx=(0, 10))
        
        # Info
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        info.bind("<Button-1>", self._handle_click)
        info.bind("<Button-3>", self._show_context_menu)
        
        self.title_lbl = ctk.CTkLabel(info, text=title, font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w")
        self.title_lbl.pack(fill="x")
        self.title_lbl.bind("<Button-1>", self._handle_click)
        self.title_lbl.bind("<Button-3>", self._show_context_menu)
        
        self.model_lbl = ctk.CTkLabel(info, text=model, font=Fonts.CAPTION, text_color=Colors.TEXT_SECONDARY, anchor="w")
        self.model_lbl.pack(fill="x")
        self.model_lbl.bind("<Button-1>", self._handle_click)
        self.model_lbl.bind("<Button-3>", self._show_context_menu)
        
        self.meta_lbl = ctk.CTkLabel(info, text=meta_text, font=Fonts.CAPTION, text_color=Colors.TEXT_DIM, anchor="w")
        self.meta_lbl.pack(fill="x")
        self.meta_lbl.bind("<Button-1>", self._handle_click)
        self.meta_lbl.bind("<Button-3>", self._show_context_menu)
        
        # Quick Download Button
        self.dl_btn = ctk.CTkButton(self, text="📥", width=30, height=30, font=Fonts.BODY, fg_color="transparent", hover_color=Colors.GLASS_FILL_HOVER, text_color=Colors.ACCENT_PRIMARY, command=self._handle_download)
        self.dl_btn.pack(side="right")
        
        # Load thumbnail safely
        self._load_thumbnail()

        # Context Menu
        self.menu = tk.Menu(self, tearoff=0, bg=Colors.BG_SIDEBAR, fg=Colors.TEXT_PRIMARY, activebackground=Colors.ACCENT_PRIMARY)
        self.menu.add_command(label="Load Prompts", command=self._handle_click)
        self.menu.add_command(label="Download", command=self._handle_download)
        self.menu.add_separator()
        self.menu.add_command(label="Delete", command=self._handle_delete)

    def _load_thumbnail(self):
        if not os.path.exists(self.image_path):
            self.thumb_label.configure(text="❌")
            return
            
        try:
            # Note: doing this synchronously for now, if it lags we can thread it
            img = Image.open(self.image_path)
            # Crop to square
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim)/2
            top = (h - min_dim)/2
            img = img.crop((left, top, left+min_dim, top+min_dim))
            img.thumbnail((120, 120), Image.Resampling.LANCZOS)
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(60, 60))
            self.thumb_label.configure(image=ctk_img, text="")
        except Exception as e:
            self.thumb_label.configure(text="ERR")

    def _on_enter(self, event=None):
        self.configure(fg_color=Colors.GLASS_FILL_LIGHT)

    def _on_leave(self, event=None):
        self.configure(fg_color="transparent")

    def _handle_click(self, event=None):
        if self._on_click:
            self._on_click(self.history_id)
            
    def _handle_download(self):
        if self._on_download:
            self._on_download(self.history_id, self.image_path)
            
    def _handle_delete(self):
        if self._on_delete:
            self._on_delete(self.history_id)
            
    def _show_context_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
