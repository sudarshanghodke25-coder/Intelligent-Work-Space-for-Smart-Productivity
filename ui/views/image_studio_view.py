import customtkinter as ctk
import os
import shutil
from tkinter import filedialog, messagebox
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from services.api_service import aurex_api
from services.image_service import image_service
from services.event_bus import bus
from ui.components.image_canvas import ImageCanvas
from ui.components.history_card import HistoryCard

from utils.ui_helpers import destroy_tracked

class ImageStudioView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = self.winfo_toplevel()
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=30)
        self.grid_columnconfigure(1, weight=50)
        self.grid_columnconfigure(2, weight=20)
        
        # State Variables
        self.selected_style = ctk.StringVar(value="Realistic")
        self.selected_aspect = ctk.StringVar(value="1:1")
        self.advanced_quality = ctk.StringVar(value="High")
        self.advanced_num = ctk.StringVar(value="1")
        self.is_generating = False
        self.active_image_id = None
        self.active_image_path = None
        self.reference_images = []   # stores file paths added via inline uploader
        self._history_widgets = []
        
        # Setup UI Regions
        self._build_top_header()
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()
        
        # Subscribe to Events
        bus.subscribe("IMAGE_GEN_START", self._on_gen_start)
        bus.subscribe("IMAGE_GEN_PROGRESS", self._on_gen_progress)
        bus.subscribe("IMAGE_GEN_SUCCESS", self._on_gen_success)
        bus.subscribe("IMAGE_GEN_ERROR", self._on_gen_error)
        bus.subscribe("HISTORY_UPDATED", self._load_history)
        
        # Initial Load
        self._load_history()

    def on_show(self):
        import threading
        threading.Thread(target=self._load_history_async, daemon=True).start()

    def _load_history_async(self):
        rows = image_service.get_history(limit=20)
        self.after(0, lambda: self._render_history(rows))

    # ==========================================
    # HEADER
    # ==========================================
    def _build_top_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=(10, 5))
        
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left")
        
        ctk.CTkLabel(left_header, text="IMAGE STUDIO ✨", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(left_header, text="Generate stunning images with AI", font=Fonts.BODY, text_color=Colors.TEXT_DIM).pack(side="left", padx=15, pady=(5, 0))
        
        right_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_header.pack(side="right")
        
        provider = aurex_api.provider if aurex_api.provider != "Unknown" else "System"
        status_color = Colors.SUCCESS if aurex_api.client else Colors.ERROR
        status_icon = "🟢" if aurex_api.client else "🔴"
        
        self.status_badge = ctk.CTkLabel(right_header, text=f"{status_icon} {provider}", font=Fonts.SMALL_BOLD, fg_color=Colors.CARD_FLOATING, text_color=status_color, corner_radius=10, width=120, height=36)
        self.status_badge.pack(side="left", padx=(0, 15))
        
        ctk.CTkButton(right_header, text="+ New Project", font=Fonts.BODY_BOLD, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, width=130, height=36, command=self._handle_new_project).pack(side="left")

    # ==========================================
    # LEFT PANEL — Generate only
    # ==========================================
    def _build_left_panel(self):
        self.left_panel = GlassCard(self, title="")
        self.left_panel.grid(row=1, column=0, sticky="nsew", padx=(16, 6), pady=(0, 16))
        self.left_panel.pack_propagate(False)
        
        container = ctk.CTkFrame(self.left_panel.content, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        # Scrollable controls
        self.gen_frame = ctk.CTkScrollableFrame(container, fg_color="transparent", bg_color="transparent")
        self.gen_frame.pack(fill="both", expand=True)
        
        # ── 1. Prompt + Images (unified input) ──────
        prompt_header_row = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        prompt_header_row.pack(fill="x", pady=(0, 3))
        ctk.CTkLabel(prompt_header_row, text="1. Prompt", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left")

        # Single outer container — acts as both text input and drop zone
        self.prompt_container = ctk.CTkFrame(
            self.gen_frame,
            fg_color=Colors.CARD_FLOATING,
            border_width=1, border_color=Colors.BORDER_SUBTLE,
            corner_radius=10
        )
        self.prompt_container.pack(fill="x", pady=(0, 10))

        # Text area row
        text_row = ctk.CTkFrame(self.prompt_container, fg_color="transparent")
        text_row.pack(fill="x", padx=4, pady=(6, 0))

        self.prompt_box = ctk.CTkTextbox(
            text_row, height=88, font=Fonts.BODY,
            fg_color="transparent", border_width=0,
            corner_radius=0, wrap="word"
        )
        self.prompt_box.pack(fill="both", expand=True, side="left")

        # Paperclip attach button — sits at bottom-right of text area
        ctk.CTkButton(
            text_row, text="📎", width=32, height=32, font=("Segoe UI", 16),
            fg_color="transparent", hover_color=Colors.CARD_HOVER,
            text_color=Colors.TEXT_DIM, corner_radius=6,
            command=self._browse_reference
        ).pack(side="right", anchor="s", padx=(2, 4), pady=(0, 4))

        # Divider line
        divider = ctk.CTkFrame(self.prompt_container, fg_color=Colors.BORDER_SUBTLE, height=1)
        divider.pack(fill="x", padx=8)

        # Image thumbnail strip — shows images added/dropped
        self.ref_strip = ctk.CTkFrame(self.prompt_container, fg_color="transparent")
        self.ref_strip.pack(fill="x", padx=8, pady=(4, 6))

        self.ref_hint = ctk.CTkLabel(
            self.ref_strip,
            text="📎 Attach images or drag & drop here",
            font=Fonts.CAPTION, text_color=Colors.TEXT_DIM
        )
        self.ref_hint.pack(side="left", pady=2)

        # Drag & drop binding — whole container and text box
        try:
            from tkinterdnd2 import DND_FILES
            for widget in [self.prompt_container, self.prompt_box]:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_ref_drop)
        except Exception:
            pass
        
        # ── 2. Style ────────────────────────────────
        ctk.CTkLabel(self.gen_frame, text="2. Style", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        style_grid = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        style_grid.pack(fill="x", pady=(2, 12))
        style_grid.grid_columnconfigure((0, 1), weight=1)
        
        styles = [("None", "✨"), ("Realistic", "📸"), ("Anime", "🌸"), ("3D Render", "🧊"), ("Cyberpunk", "🌆"), ("Sketch", "✏️")]
        self.style_buttons = {}
        for i, (name, icon) in enumerate(styles):
            btn = ctk.CTkButton(
                style_grid, text=f"{icon} {name}", font=Fonts.SMALL_BOLD,
                fg_color=Colors.ACCENT_PRIMARY if self.selected_style.get() == name else Colors.CARD_FLOATING,
                hover_color=Colors.CARD_HOVER, height=40, corner_radius=6,
                command=lambda n=name: self._set_style(n)
            )
            btn.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")
            self.style_buttons[name] = btn
            
        # ── 3. Aspect Ratio ─────────────────────────
        ctk.CTkLabel(self.gen_frame, text="3. Aspect Ratio", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ar_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        ar_frame.pack(fill="x", pady=(2, 12))
        ar_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        
        aspects = ["1:1", "16:9", "9:16", "4:3", "3:4"]
        self.ar_buttons = {}
        for i, ar in enumerate(aspects):
            btn = ctk.CTkButton(
                ar_frame, text=ar, font=Fonts.SMALL_BOLD,
                fg_color=Colors.ACCENT_PRIMARY if self.selected_aspect.get() == ar else Colors.CARD_FLOATING,
                hover_color=Colors.CARD_HOVER, width=0, height=40, corner_radius=6,
                command=lambda a=ar: self._set_aspect(a)
            )
            btn.grid(row=0, column=i, padx=2, sticky="ew")
            self.ar_buttons[ar] = btn
            
        # ── 4. Advanced Options ─────────────────────
        ctk.CTkLabel(self.gen_frame, text="4. Advanced Options", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(2, 0))
        adv_frame = ctk.CTkFrame(self.gen_frame, fg_color=Colors.CARD_FLOATING, corner_radius=8)
        adv_frame.pack(fill="x", pady=(2, 12))
        self._add_setting_row(adv_frame, "Quality", self.advanced_quality, ["Standard", "High", "Ultra"])
        
        # ── Primary Action ───────────────────────────
        self.generate_btn = ctk.CTkButton(
            container, text="✨ Generate Image", font=Fonts.BUTTON, height=44,
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
            command=self._handle_generate
        )
        self.generate_btn.pack(fill="x", side="bottom", pady=(10, 0))

    # ── Reference image helpers ──────────────────────
    def _browse_reference(self):
        paths = filedialog.askopenfilenames(
            title="Select Reference Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")]
        )
        for p in paths:
            self._add_reference_image(p)

    def _on_ref_drop(self, event):
        raw = event.data
        # tkinterdnd2 wraps paths with spaces in braces
        import re
        paths = re.findall(r'\{([^}]+)\}|(\S+)', raw)
        for match in paths:
            p = match[0] or match[1]
            if p.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                self._add_reference_image(p)

    def _add_reference_image(self, path):
        if path in self.reference_images or len(self.reference_images) >= 4:
            return
        self.reference_images.append(path)
        self._refresh_ref_strip()

    def _remove_reference_image(self, path):
        if path in self.reference_images:
            self.reference_images.remove(path)
        self._refresh_ref_strip()

    def _refresh_ref_strip(self):
        for w in self.ref_strip.winfo_children():
            w.destroy()

        if not self.reference_images:
            self.ref_hint = ctk.CTkLabel(self.ref_strip, text="Drag & drop or click Add →", font=Fonts.CAPTION, text_color=Colors.TEXT_DIM)
            self.ref_hint.pack(side="left", pady=8)
            return

        from PIL import Image
        for path in self.reference_images:
            thumb_frame = ctk.CTkFrame(self.ref_strip, fg_color=Colors.BG_DEEPSPACE, corner_radius=6, width=60, height=60)
            thumb_frame.pack(side="left", padx=3, pady=2)
            thumb_frame.pack_propagate(False)
            try:
                img = Image.open(path)
                img.thumbnail((56, 56))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                lbl = ctk.CTkLabel(thumb_frame, image=ctk_img, text="")
                lbl.pack(expand=True)
            except Exception:
                ctk.CTkLabel(thumb_frame, text="🖼", font=("Segoe UI", 20)).pack(expand=True)
            # ✕ remove button
            p = path
            ctk.CTkButton(thumb_frame, text="✕", width=18, height=18, font=Fonts.CAPTION,
                          fg_color=Colors.ERROR, hover_color="#cc0000", text_color="white",
                          command=lambda pp=p: self._remove_reference_image(pp)).place(relx=1.0, rely=0.0, anchor="ne")

    def _add_setting_row(self, parent, label, variable, options):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        row.pack(fill="x", padx=10, pady=2)
        row.pack_propagate(False)
        ctk.CTkLabel(row, text=label, font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY).pack(side="left")
        menu = ctk.CTkOptionMenu(row, values=options, variable=variable, font=Fonts.SMALL,
                                  fg_color=Colors.CARD_FLOATING, button_color=Colors.CARD_FLOATING,
                                  button_hover_color=Colors.CARD_HOVER, text_color=Colors.TEXT_PRIMARY,
                                  anchor="e", width=160)
        menu.pack(side="right")

    def _set_style(self, style_name):
        self.selected_style.set(style_name)
        for name, btn in self.style_buttons.items():
            btn.configure(fg_color=Colors.ACCENT_PRIMARY if name == style_name else Colors.CARD_FLOATING)

    def _set_aspect(self, aspect):
        self.selected_aspect.set(aspect)
        for ar, btn in self.ar_buttons.items():
            btn.configure(fg_color=Colors.ACCENT_PRIMARY if ar == aspect else Colors.CARD_FLOATING)

    # ==========================================
    # CENTER PANEL — Canvas + Save As only
    # ==========================================
    def _build_center_panel(self):
        self.center_panel = GlassCard(self, title="")
        self.center_panel.grid(row=1, column=1, sticky="nsew", padx=6, pady=(0, 16))
        self.center_panel.pack_propagate(False)
        
        outer = ctk.CTkFrame(self.center_panel.content, fg_color="transparent")
        outer.pack(fill="both", expand=True)
        
        # Meta Toolbar
        meta_bar = ctk.CTkFrame(outer, fg_color="transparent")
        meta_bar.pack(fill="x", pady=(0, 8))
        
        self.meta_title = ctk.CTkLabel(meta_bar, text="Generated Image", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY)
        self.meta_title.pack(side="left")
        
        self.meta_mode = ctk.CTkLabel(meta_bar, text="Mode: Auto", font=Fonts.CAPTION, text_color=Colors.TEXT_DIM, fg_color=Colors.CARD_FLOATING, corner_radius=6, padx=8)
        self.meta_mode.pack(side="left", padx=(10, 5))
        
        self.meta_status = ctk.CTkLabel(meta_bar, text="Ready", font=Fonts.CAPTION, text_color=Colors.SUCCESS, fg_color=Colors.CARD_FLOATING, corner_radius=6, padx=8)
        self.meta_status.pack(side="left", padx=5)
        
        # Image Canvas — takes all available space
        self.canvas = ImageCanvas(outer, on_image_dropped=None)
        self.canvas.pack(fill="both", expand=True, pady=(0, 8))
        
        # Save As bar — only remaining control
        dl_frame = ctk.CTkFrame(outer, fg_color=Colors.CARD_FLOATING, corner_radius=8, height=56)
        dl_frame.pack(fill="x")
        dl_frame.pack_propagate(False)
        
        ctk.CTkLabel(dl_frame, text="Save As:", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY).pack(side="left", padx=(15, 8))
        self.dl_filename = ctk.CTkEntry(dl_frame, width=150, font=Fonts.BODY, border_width=1, border_color=Colors.BORDER_SUBTLE, height=36)
        self.dl_filename.pack(side="left", padx=4)
        self.dl_filename.insert(0, "Aurex_Image")
        ctk.CTkLabel(dl_frame, text=".png", font=Fonts.BODY, text_color=Colors.TEXT_DIM).pack(side="left")
        
        self.dl_btn = ctk.CTkButton(dl_frame, text="📥 Download Image", font=Fonts.BODY_BOLD,
                                     fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
                                     width=160, height=38, command=self._handle_save)
        self.dl_btn.pack(side="right", padx=15)

    # ==========================================
    # RIGHT PANEL — History
    # ==========================================
    def _build_right_panel(self):
        self.right_panel = GlassCard(self, title="")
        self.right_panel.grid(row=1, column=2, sticky="nsew", padx=(6, 16), pady=(0, 16))
        self.right_panel.pack_propagate(False)
        
        container = ctk.CTkFrame(self.right_panel.content, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="History", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(header, text="Clear All", font=Fonts.CAPTION, width=64, height=26,
                      fg_color=Colors.CARD_FLOATING, hover_color=Colors.ERROR,
                      text_color=Colors.TEXT_SECONDARY, command=self._handle_clear_all).pack(side="right")
        
        self.history_scroll = ctk.CTkScrollableFrame(container, fg_color="transparent", bg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True)
        
        ctk.CTkButton(container, text="View All History", font=Fonts.BODY_BOLD,
                      fg_color=Colors.CARD_FLOATING, hover_color=Colors.CARD_HOVER,
                      text_color=Colors.TEXT_PRIMARY, height=40,
                      command=self._handle_view_all_history).pack(fill="x", side="bottom", pady=(10, 0))

    # ==========================================
    # LOGIC
    # ==========================================
    def _handle_generate(self):
        prompt = self.prompt_box.get("0.0", "end").strip()
        references = list(self.reference_images)
        
        if not prompt and not references:
            return
        
        style = self.selected_style.get()
        aspect = self.selected_aspect.get()
        model = "black-forest-labs/flux1-dev"
        quality = self.advanced_quality.get()
        num = self.advanced_num.get()
        
        image_service.generate(prompt, style, aspect, model, quality, n=num, reference_images=references)

    def _on_gen_start(self, data):
        self.generate_btn.configure(state="disabled", text="Generating...")
        self.meta_status.configure(text="Generating", text_color=Colors.WARNING)
        self.canvas.clear()
        self.canvas.title_lbl.configure(text="Generating image...")
        self.canvas.sub_lbl.configure(text="0%")
        self.canvas.empty_frame.place(relx=0.5, rely=0.5, anchor="center")

    def _on_gen_progress(self, data):
        self.canvas.title_lbl.configure(text=data.get("status", "Processing..."))
        self.canvas.sub_lbl.configure(text=f"{data.get('progress', 0)}%")

    def _on_gen_success(self, data):
        gen_time = data.get("generation_time", 0)
        self.generate_btn.configure(state="normal", text="✨ Generate Image")
        self.meta_status.configure(text=f"Done  ⏱ {gen_time}s", text_color=Colors.SUCCESS)
        
        mode_text = data.get("generation_mode", "text_to_image").replace("_", " ").title()
        self.meta_mode.configure(text=f"Mode: {mode_text}")
        
        filepath = data.get("filepath")
        self.active_image_id = data.get("id")
        self.active_image_path = filepath
        self.canvas.load_image(filepath)
        
    def _on_gen_error(self, data):
        self.generate_btn.configure(state="normal", text="✨ Generate Image")
        self.meta_status.configure(text="Error", text_color=Colors.ERROR)
        self.canvas.title_lbl.configure(text="Generation Failed")
        self.canvas.sub_lbl.configure(text=data.get("message", "Unknown error"))

    def _load_history(self, event=None):
        self._render_history(image_service.get_history(limit=20))

    def _render_history(self, rows):
        destroy_tracked(self._history_widgets)
            
        for row in rows:
            card = HistoryCard(
                self.history_scroll,
                history_id=row['id'],
                title=row['prompt'][:28] + ("..." if len(row['prompt']) > 28 else ""),
                model=row['model'],
                meta_text=f"{row['style']} • {row['aspect_ratio']}",
                image_path=row['local_path'],
                on_click=self._restore_history,
                on_delete=self._delete_history,
                on_download=self._download_history
            )
            card.pack(fill="x", pady=4)
            self._history_widgets.append(card)

    def _restore_history(self, history_id):
        rows = image_service.get_history(limit=100)
        row = next((r for r in rows if r['id'] == history_id), None)
        if not row: return
        
        self.prompt_box.delete("0.0", "end")
        self.prompt_box.insert("0.0", row['prompt'])
        self._set_style(row['style'])
        self._set_aspect(row['aspect_ratio'])
        
        # Restore reference images if any
        self.reference_images.clear()
        import json
        ref_imgs = row.get('reference_images')
        if ref_imgs:
            try:
                paths = json.loads(ref_imgs)
                for p in paths:
                    if os.path.exists(p):
                        self.reference_images.append(p)
            except Exception:
                pass
        self._refresh_ref_strip()
        
        self.active_image_id = history_id
        self.active_image_path = row['local_path']
        if row['local_path'] and os.path.exists(row['local_path']):
            self.canvas.load_image(self.active_image_path)

    def _delete_history(self, history_id):
        image_service.delete_history_item(history_id)

    def _handle_clear_all(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to delete ALL image history? This cannot be undone."):
            image_service.delete_all_history()
            self.canvas.clear()
            self.active_image_id = None
            self.active_image_path = None

    def _handle_view_all_history(self):
        """Open History view in the main app navigation."""
        try:
            self.app.navigate("History")
        except Exception:
            pass

    def _download_history(self, history_id, path):
        if not path or not os.path.exists(path): return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG", "*.jpg"), ("WebP", "*.webp")],
            title="Save Image As"
        )
        if save_path:
            shutil.copy2(path, save_path)

    def _handle_save(self):
        if not self.active_image_path or not os.path.exists(self.active_image_path):
            return
            
        fname = self.dl_filename.get().strip()
        if not fname: fname = "Aurex_Image"
        
        save_path = filedialog.asksaveasfilename(
            initialfile=fname,
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG", "*.jpg"), ("WebP", "*.webp")],
            title="Download Image"
        )
        if save_path:
            shutil.copy2(self.active_image_path, save_path)

    def _handle_new_project(self):
        self.canvas.clear()
        self.active_image_id = None
        self.active_image_path = None
        self.prompt_box.delete("0.0", "end")
        self.reference_images.clear()
        self._refresh_ref_strip()
