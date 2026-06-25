import customtkinter as ctk
import os
import shutil
from tkinter import filedialog
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from services.api_service import aurex_api
from services.image_service import image_service
from services.event_bus import bus
from ui.components.image_canvas import ImageCanvas
from ui.components.history_card import HistoryCard

class ImageStudioView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = self.winfo_toplevel()
        
        # Expand Right panel width by 15%. Previous: 30/45/25. New: 25/45/30
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=30)
        self.grid_columnconfigure(1, weight=50)
        self.grid_columnconfigure(2, weight=20)
        
        # State Variables
        self.current_mode = ctk.StringVar(value="Generate")
        self.prompt_var = ctk.StringVar()
        self.selected_style = ctk.StringVar(value="Realistic")
        self.selected_aspect = ctk.StringVar(value="1:1")
        self.advanced_model = ctk.StringVar(value="black-forest-labs/flux1-dev")
        self.advanced_quality = ctk.StringVar(value="High")
        self.advanced_num = ctk.StringVar(value="1")
        self.is_generating = False
        self.active_image_id = None
        self.active_image_path = None
        
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

    # ==========================================
    # HEADER
    # ==========================================
    def _build_top_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=(10, 5))
        
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left")
        
        ctk.CTkLabel(left_header, text="IMAGE STUDIO ✨", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(left_header, text="Generate, edit and enhance images with AI", font=Fonts.BODY, text_color=Colors.TEXT_DIM).pack(side="left", padx=15, pady=(5, 0))
        
        right_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_header.pack(side="right")
        
        provider = aurex_api.provider if aurex_api.provider != "Unknown" else "System"
        status_color = Colors.SUCCESS if aurex_api.client else Colors.ERROR
        status_icon = "🟢" if aurex_api.client else "🔴"
        
        self.status_badge = ctk.CTkLabel(right_header, text=f"{status_icon} {provider}", font=Fonts.SMALL_BOLD, fg_color=Colors.GLASS_FILL_LIGHT, text_color=status_color, corner_radius=10, width=120, height=36)
        self.status_badge.pack(side="left", padx=(0, 15))
        
        ctk.CTkButton(right_header, text="+ New Project", font=Fonts.BODY_BOLD, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, width=130, height=36, command=self._handle_new_project).pack(side="left")

    # ==========================================
    # LEFT PANEL
    # ==========================================
    def _build_left_panel(self):
        self.left_panel = GlassCard(self, title="")
        self.left_panel.grid(row=1, column=0, sticky="nsew", padx=(16, 6), pady=(0, 16))
        self.left_panel.pack_propagate(False)
        
        container = ctk.CTkFrame(self.left_panel.content, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        # Mode Segment
        self.mode_segment = ctk.CTkSegmentedButton(container, values=["Generate", "Edit Image"], variable=self.current_mode, font=Fonts.BODY_BOLD, selected_color=Colors.ACCENT_PRIMARY, unselected_color=Colors.GLASS_FILL_LIGHT, selected_hover_color=Colors.ACCENT_HOVER, unselected_hover_color=Colors.GLASS_FILL_HOVER, command=self._on_mode_change)
        self.mode_segment.pack(fill="x", pady=(0, 12))
        
        # Generation Controls Frame
        self.gen_frame = ctk.CTkScrollableFrame(container, fg_color="transparent", bg_color="transparent")
        self.gen_frame.pack(fill="both", expand=True)
        
        # Prompt
        ctk.CTkLabel(self.gen_frame, text="1. Prompt", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        self.prompt_box = ctk.CTkTextbox(self.gen_frame, height=80, font=Fonts.BODY, fg_color=Colors.GLASS_FILL_LIGHT, border_width=1, border_color=Colors.GLASS_BORDER, corner_radius=8, wrap="word")
        self.prompt_box.pack(fill="x", pady=(2, 8))
        
        # Multimodal Upload
        from ui.components.reference_uploader import ReferenceUploader
        self.reference_uploader = ReferenceUploader(self.gen_frame, max_images=4)
        self.reference_uploader.pack(fill="x", pady=(2, 12))
        
        # Style
        ctk.CTkLabel(self.gen_frame, text="2. Style", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        style_grid = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        style_grid.pack(fill="x", pady=(2, 12))
        style_grid.grid_columnconfigure((0, 1), weight=1)
        
        styles = [("None", "✨"), ("Realistic", "📸"), ("Anime", "🌸"), ("3D Render", "🧊"), ("Cyberpunk", "🌆"), ("Sketch", "✏️")]
        self.style_buttons = {}
        for i, (name, icon) in enumerate(styles):
            btn = ctk.CTkButton(style_grid, text=f"{icon} {name}", font=Fonts.SMALL_BOLD, fg_color=Colors.GLASS_FILL_LIGHT if self.selected_style.get() != name else Colors.ACCENT_PRIMARY, hover_color=Colors.GLASS_FILL_HOVER, height=40, corner_radius=6, command=lambda n=name: self._set_style(n))
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
            self.style_buttons[name] = btn
            
        # Aspect Ratio
        ctk.CTkLabel(self.gen_frame, text="3. Aspect Ratio", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ar_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        ar_frame.pack(fill="x", pady=(2, 12))
        ar_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        aspects = ["1:1", "16:9", "9:16", "4:3", "3:4"]
        self.ar_buttons = {}
        for i, ar in enumerate(aspects):
            btn = ctk.CTkButton(ar_frame, text=ar, font=Fonts.SMALL_BOLD, fg_color=Colors.GLASS_FILL_LIGHT if self.selected_aspect.get() != ar else Colors.ACCENT_PRIMARY, hover_color=Colors.GLASS_FILL_HOVER, width=0, height=40, corner_radius=6, command=lambda a=ar: self._set_aspect(a))
            btn.grid(row=0, column=i, padx=2, sticky="ew")
            self.ar_buttons[ar] = btn
            
        # Advanced
        ctk.CTkLabel(self.gen_frame, text="4. Advanced Options", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(2,0))
        adv_frame = ctk.CTkFrame(self.gen_frame, fg_color=Colors.GLASS_FILL_LIGHT, corner_radius=8)
        adv_frame.pack(fill="x", pady=(2, 12))
        
        self._add_setting_row(adv_frame, "Model", self.advanced_model, ["black-forest-labs/flux1-dev", "stabilityai/stable-diffusion-xl", "stabilityai/sdxl-turbo"])
        self._add_setting_row(adv_frame, "Quality", self.advanced_quality, ["Standard", "High", "Ultra"])
        
        # Primary Action
        self.generate_btn = ctk.CTkButton(container, text="✨ Generate Image", font=Fonts.BUTTON, height=40, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, command=self._handle_generate)
        self.generate_btn.pack(fill="x", side="bottom", pady=(10, 0))

    def _add_setting_row(self, parent, label, variable, options):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        row.pack(fill="x", padx=10, pady=2)
        row.pack_propagate(False)
        ctk.CTkLabel(row, text=label, font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY).pack(side="left")
        menu = ctk.CTkOptionMenu(row, values=options, variable=variable, font=Fonts.SMALL, fg_color=Colors.GLASS_FILL_LIGHT, button_color=Colors.GLASS_FILL_LIGHT, button_hover_color=Colors.GLASS_FILL_HOVER, text_color=Colors.TEXT_PRIMARY, anchor="e", width=160)
        menu.pack(side="right")

    def _set_style(self, style_name):
        self.selected_style.set(style_name)
        for name, btn in self.style_buttons.items():
            btn.configure(fg_color=Colors.ACCENT_PRIMARY if name == style_name else Colors.GLASS_FILL_LIGHT)

    def _set_aspect(self, aspect):
        self.selected_aspect.set(aspect)
        for ar, btn in self.ar_buttons.items():
            btn.configure(fg_color=Colors.ACCENT_PRIMARY if ar == aspect else Colors.GLASS_FILL_LIGHT)

    def _on_mode_change(self, mode):
        if mode == "Generate":
            self.generate_btn.configure(text="✨ Generate Image")
            self.canvas.set_generation_mode()
        else:
            self.generate_btn.configure(text="🪄 Apply Edits")
            self.canvas.set_upload_mode()

    # ==========================================
    # CENTER PANEL
    # ==========================================
    def _build_center_panel(self):
        self.center_panel = GlassCard(self, title="")
        self.center_panel.grid(row=1, column=1, sticky="nsew", padx=6, pady=(0, 16))
        self.center_panel.pack_propagate(False)
        
        container = ctk.CTkFrame(self.center_panel.content, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        # Meta Toolbar
        meta_bar = ctk.CTkFrame(container, fg_color="transparent")
        meta_bar.pack(fill="x", pady=(0, 12))
        
        self.meta_title = ctk.CTkLabel(meta_bar, text="Generated Image", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY)
        self.meta_title.pack(side="left")
        
        self.meta_mode = ctk.CTkLabel(meta_bar, text="Mode: Auto", font=Fonts.CAPTION, text_color=Colors.TEXT_DIM, fg_color=Colors.GLASS_FILL_LIGHT, corner_radius=6, padx=8)
        self.meta_mode.pack(side="left", padx=(10, 5))
        
        self.meta_status = ctk.CTkLabel(meta_bar, text="Ready", font=Fonts.CAPTION, text_color=Colors.SUCCESS, fg_color=Colors.GLASS_FILL_LIGHT, corner_radius=6, padx=8)
        self.meta_status.pack(side="left", padx=5)
        
        # Toolbar
        tools = ctk.CTkFrame(meta_bar, fg_color="transparent")
        tools.pack(side="right")
        for icon in ["🔍+", "🔍-", "📐", "1:1"]:
            ctk.CTkButton(tools, text=icon, width=40, height=36, fg_color=Colors.GLASS_FILL_LIGHT, hover_color=Colors.GLASS_FILL_HOVER, font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=2)
        
        # Image Canvas
        self.canvas = ImageCanvas(container, on_image_dropped=self._handle_image_dropped)
        self.canvas.pack(fill="both", expand=True)
        
        # Quick Actions
        quick_frame = ctk.CTkFrame(container, fg_color="transparent")
        quick_frame.pack(fill="x", pady=12)
        quick_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        actions = [("🪄", "Enhance"), ("🔍", "Upscale"), ("✂️", "Remove BG"), ("🔄", "Vary"), ("🎲", "Reimagine")]
        for i, (icon, text) in enumerate(actions):
            btn = ctk.CTkButton(quick_frame, text=f"{icon} {text}", font=Fonts.SMALL_BOLD, fg_color=Colors.GLASS_FILL_LIGHT, hover_color=Colors.GLASS_FILL_HOVER, text_color=Colors.TEXT_PRIMARY, height=40, corner_radius=8, command=lambda t=text: self._handle_quick_action(t))
            btn.grid(row=0, column=i, padx=4, sticky="ew")
            
        # Download Bar
        dl_frame = ctk.CTkFrame(container, fg_color=Colors.GLASS_FILL_LIGHT, corner_radius=8, height=60)
        dl_frame.pack(fill="x")
        dl_frame.pack_propagate(False)
        
        ctk.CTkLabel(dl_frame, text="Save As:", font=Fonts.SMALL_BOLD).pack(side="left", padx=(15, 10))
        self.dl_filename = ctk.CTkEntry(dl_frame, width=150, font=Fonts.BODY, border_width=1, border_color=Colors.GLASS_BORDER, height=36)
        self.dl_filename.pack(side="left", padx=5)
        self.dl_filename.insert(0, "Aurex_Image")
        ctk.CTkLabel(dl_frame, text=".png", font=Fonts.BODY, text_color=Colors.TEXT_DIM).pack(side="left")
        
        self.dl_btn = ctk.CTkButton(dl_frame, text="📥 Download Image", font=Fonts.BODY_BOLD, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, width=160, height=40, command=self._handle_save)
        self.dl_btn.pack(side="right", padx=15)
        
    def _handle_image_dropped(self, file_path):
        self.canvas.load_image(file_path)
        self.current_mode.set("Edit Image")
        self._on_mode_change("Edit Image")
        self.active_image_path = file_path
        if getattr(self, 'reference_uploader', None):
            self.reference_uploader.add_image(file_path)
        
    def _handle_quick_action(self, action):
        if not self.active_image_path: return
        self.prompt_box.delete("0.0", "end")
        self.prompt_box.insert("0.0", f"Please {action.lower()} this image.")
        self.current_mode.set("Edit Image")
        self._on_mode_change("Edit Image")

    # ==========================================
    # RIGHT PANEL
    # ==========================================
    def _build_right_panel(self):
        self.right_panel = GlassCard(self, title="")
        self.right_panel.grid(row=1, column=2, sticky="nsew", padx=(6, 16), pady=(0, 16))
        self.right_panel.pack_propagate(False)
        
        container = ctk.CTkFrame(self.right_panel.content, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(header, text="History", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(header, text="Clear All", font=Fonts.CAPTION, width=60, height=24, fg_color=Colors.GLASS_FILL_LIGHT, hover_color=Colors.ERROR, text_color=Colors.TEXT_SECONDARY).pack(side="right")
        
        self.history_scroll = ctk.CTkScrollableFrame(container, fg_color="transparent", bg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True)
        
        ctk.CTkButton(container, text="View All History", font=Fonts.BODY_BOLD, fg_color=Colors.GLASS_FILL_LIGHT, hover_color=Colors.GLASS_FILL_HOVER, text_color=Colors.TEXT_PRIMARY, height=40).pack(fill="x", side="bottom", pady=(10, 0))

    # ==========================================
    # LOGIC
    # ==========================================
    def _handle_generate(self):
        prompt = self.prompt_box.get("0.0", "end").strip()
        ref_images = getattr(self, 'reference_uploader', None)
        references = ref_images.get_images() if ref_images else []
        
        if not prompt and not references: 
            return
        
        style = self.selected_style.get()
        aspect = self.selected_aspect.get()
        model = self.advanced_model.get()
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
        self.generate_btn.configure(state="normal", text="✨ Generate Image")
        self.meta_status.configure(text="Ready", text_color=Colors.SUCCESS)
        
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
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
            
        rows = image_service.get_history(limit=20)
        for row in rows:
            HistoryCard(
                self.history_scroll,
                history_id=row['id'],
                title=row['prompt'][:25] + "...",
                model=row['model'],
                meta_text=f"{row['style']} • {row['aspect_ratio']}",
                image_path=row['local_path'],
                on_click=self._restore_history,
                on_delete=self._delete_history,
                on_download=self._download_history
            ).pack(fill="x", pady=4)

    def _restore_history(self, history_id):
        rows = image_service.get_history(limit=100)
        row = next((r for r in rows if r['id'] == history_id), None)
        if not row: return
        
        self.prompt_box.delete("0.0", "end")
        self.prompt_box.insert("0.0", row['prompt'])
        self._set_style(row['style'])
        self._set_aspect(row['aspect_ratio'])
        self.advanced_model.set(row['model'])
        
        if getattr(self, 'reference_uploader', None):
            self.reference_uploader.clear()
            import json
            ref_imgs = row.get('reference_images')
            if ref_imgs:
                try:
                    paths = json.loads(ref_imgs)
                    for p in paths:
                        self.reference_uploader.add_image(p)
                except:
                    pass
        
        self.active_image_id = history_id
        self.active_image_path = row['local_path']
        self.canvas.load_image(self.active_image_path)
        self.current_mode.set("Edit Image")
        self._on_mode_change("Edit Image")

    def _delete_history(self, history_id):
        image_service.delete_history_item(history_id)
        
    def _download_history(self, history_id, path):
        if not os.path.exists(path): return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")],
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
        self.current_mode.set("Generate")
        self._on_mode_change("Generate")
