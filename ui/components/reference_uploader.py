import customtkinter as ctk
import os
from PIL import Image, ImageGrab
from tkinter import filedialog, messagebox
from theme import Colors, Fonts, Dims
import threading

class ReferenceUploader(ctk.CTkFrame):
    def __init__(self, parent, max_images=4, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.max_images = max_images
        self.image_paths = []
        self.thumbnail_widgets = []
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header, text="Reference Images", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        self.count_label = ctk.CTkLabel(header, text=f"0/{max_images}", font=Fonts.CAPTION, text_color=Colors.TEXT_DIM)
        self.count_label.pack(side="right")
        
        # Upload Area
        self.upload_btn = ctk.CTkButton(
            self,
            text="📁 Click to Browse, Drag & Drop, or Ctrl+V",
            font=Fonts.SMALL_BOLD,
            fg_color=Colors.CARD_FLOATING,
            hover_color=Colors.CARD_HOVER,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            text_color=Colors.TEXT_SECONDARY,
            height=40,
            command=self._handle_browse
        )
        self.upload_btn.pack(fill="x", pady=(0, 5))
        
        # Scrollable Thumbnails Area (Hidden initially)
        self.thumb_scroll = ctk.CTkScrollableFrame(self, orientation="horizontal", height=80, fg_color="transparent", bg_color="transparent")
        
        # Bindings
        self._bind_drag_drop()
        
        # Paste binding (Requires focus on parent or app)
        try:
            self.winfo_toplevel().bind("<Control-v>", self._handle_paste)
        except Exception:
            pass

    def _bind_drag_drop(self):
        try:
            from tkinterdnd2 import DND_FILES
            # If the root is a TkinterDnD.Tk, this will work
            self.upload_btn.drop_target_register(DND_FILES)
            self.upload_btn.dnd_bind("<<Drop>>", self._on_drop)
        except ImportError:
            pass # Drag and drop not supported, fallback to browse
        except Exception:
            pass
            
    def _on_drop(self, event):
        files = self.tk.splitlist(event.data)
        for f in files:
            if self._is_valid_image(f):
                self.add_image(f)
                
    def _handle_browse(self):
        if len(self.image_paths) >= self.max_images:
            return
            
        file_paths = filedialog.askopenfilenames(
            title="Select Reference Images",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")]
        )
        for f in file_paths:
            self.add_image(f)
            
    def _handle_paste(self, event=None):
        if len(self.image_paths) >= self.max_images:
            return
            
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                # Save to a temporary location
                temp_dir = os.path.join("Aurex_Data", "temp")
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, f"pasted_{len(self.image_paths)}.png")
                img.save(temp_path, "PNG")
                self.add_image(temp_path)
        except Exception as e:
            print(f"Paste error: {e}")
            
    def _is_valid_image(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in ['.png', '.jpg', '.jpeg', '.webp']

    def add_image(self, file_path):
        if len(self.image_paths) >= self.max_images:
            return
            
        if file_path not in self.image_paths:
            self.image_paths.append(file_path)
            self._render_thumbnails()

    def remove_image(self, file_path):
        if file_path in self.image_paths:
            self.image_paths.remove(file_path)
            self._render_thumbnails()
            
    def clear(self):
        self.image_paths.clear()
        self._render_thumbnails()

    def get_images(self):
        return self.image_paths.copy()

    def _render_thumbnails(self):
        # Manage visibility of scroll area
        if not self.image_paths:
            self.thumb_scroll.pack_forget()
        elif not self.thumb_scroll.winfo_ismapped():
            self.thumb_scroll.pack(fill="x", pady=(5, 0))
            
        # Update counter
        self.count_label.configure(text=f"{len(self.image_paths)}/{self.max_images}")
        
        # Clear existing
        for widget in self.thumb_scroll.winfo_children():
            widget.destroy()
            
        # Re-render
        for path in self.image_paths:
            self._create_thumbnail(path)
            
    def _create_thumbnail(self, path):
        frame = ctk.CTkFrame(self.thumb_scroll, width=80, height=80, fg_color=Colors.CARD_FLOATING, corner_radius=8)
        frame.pack(side="left", padx=5)
        frame.pack_propagate(False)
        
        # Async load image to prevent UI freeze
        def load_img():
            try:
                img = Image.open(path)
                # Crop to square
                width, height = img.size
                min_dim = min(width, height)
                left = (width - min_dim) / 2
                top = (height - min_dim) / 2
                img = img.crop((left, top, left + min_dim, top + min_dim))
                
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
                lbl = ctk.CTkLabel(frame, text="", image=ctk_img)
                lbl.place(relx=0.5, rely=0.5, anchor="center")
                
                # Delete button overlay
                del_btn = ctk.CTkButton(
                    frame, text="✕", width=20, height=20, corner_radius=10, 
                    fg_color=Colors.ERROR, hover_color="#ff4444", font=Fonts.SMALL_BOLD,
                    command=lambda p=path: self.remove_image(p)
                )
                del_btn.place(relx=0.95, rely=0.05, anchor="ne")
            except Exception as e:
                ctk.CTkLabel(frame, text="Error", font=Fonts.CAPTION, text_color=Colors.ERROR).place(relx=0.5, rely=0.5, anchor="center")
                
        threading.Thread(target=load_img, daemon=True).start()
