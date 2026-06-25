import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image
from theme import Colors, Fonts

# Try to load tkinterdnd2 for Drag and Drop support
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

class ImageCanvas(ctk.CTkFrame):
    def __init__(self, parent, on_image_dropped=None, **kwargs):
        super().__init__(parent, fg_color=Colors.BG_DEEPSPACE, border_width=2, border_color=Colors.GLASS_BORDER, corner_radius=12, **kwargs)
        
        self.on_image_dropped = on_image_dropped
        self.current_image_path = None
        self.current_pil_image = None
        
        # Setup Empty State
        self.empty_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.empty_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.icon_lbl = ctk.CTkLabel(self.empty_frame, text="✨", font=("Segoe UI", 48), text_color=Colors.TEXT_DIM)
        self.icon_lbl.pack()
        
        self.title_lbl = ctk.CTkLabel(self.empty_frame, text="Your generated image will appear here", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY)
        self.title_lbl.pack(pady=(10, 5))
        
        self.sub_lbl = ctk.CTkLabel(self.empty_frame, text="Enter a prompt and click \"Generate Image\"", font=Fonts.SMALL, text_color=Colors.TEXT_DIM)
        self.sub_lbl.pack()
        
        # Setup Image View State
        self.image_label = ctk.CTkLabel(self, text="", fg_color="transparent")
        
        # Drag and Drop Setup
        if HAS_DND and hasattr(self.winfo_toplevel(), 'drop_target_register'):
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self._handle_drop)
            
    def _handle_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
            
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            if self.on_image_dropped:
                self.on_image_dropped(file_path)
            else:
                self.load_image(file_path)
                
    def set_upload_mode(self):
        self.icon_lbl.configure(text="📥")
        self.title_lbl.configure(text="Drop an image here")
        if HAS_DND:
            self.sub_lbl.configure(text="Or click to browse files")
        else:
            self.sub_lbl.configure(text="Click to browse files")
            
        self.empty_frame.bind("<Button-1>", self._browse_file)
        self.icon_lbl.bind("<Button-1>", self._browse_file)
        self.title_lbl.bind("<Button-1>", self._browse_file)
        self.sub_lbl.bind("<Button-1>", self._browse_file)
        self.bind("<Button-1>", self._browse_file)
        
    def set_generation_mode(self):
        self.icon_lbl.configure(text="✨")
        self.title_lbl.configure(text="Your generated image will appear here")
        self.sub_lbl.configure(text="Enter a prompt and click \"Generate Image\"")
        
        # Unbind
        self.empty_frame.unbind("<Button-1>")
        self.icon_lbl.unbind("<Button-1>")
        self.title_lbl.unbind("<Button-1>")
        self.sub_lbl.unbind("<Button-1>")
        self.unbind("<Button-1>")
        
    def _browse_file(self, event=None):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")]
        )
        if file_path:
            if self.on_image_dropped:
                self.on_image_dropped(file_path)
            else:
                self.load_image(file_path)

    def load_image(self, file_path):
        if not os.path.exists(file_path):
            return
            
        try:
            self.current_image_path = file_path
            self.current_pil_image = Image.open(file_path)
            
            # Hide empty state
            self.empty_frame.place_forget()
            
            # Show image
            self.image_label.pack(expand=True, fill="both", padx=10, pady=10)
            
            # Resize image to fit current frame size (responsive)
            self.update_idletasks()
            w = self.winfo_width() - 20
            h = self.winfo_height() - 20
            
            if w <= 0 or h <= 0:
                w, h = 500, 500 # fallback
                
            self._render_scaled(w, h)
            
            # Bind resize event to re-render
            self.bind("<Configure>", self._on_resize)
            
        except Exception as e:
            print(f"Failed to load image: {e}")
            
    def _on_resize(self, event):
        if self.current_pil_image:
            w = event.width - 20
            h = event.height - 20
            if w > 0 and h > 0:
                self._render_scaled(w, h)
                
    def _render_scaled(self, max_w, max_h):
        if not self.current_pil_image: return
        
        img = self.current_pil_image.copy()
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self.image_label.configure(image=ctk_img)
        
    def clear(self):
        self.current_image_path = None
        self.current_pil_image = None
        self.unbind("<Configure>")
        self.image_label.pack_forget()
        self.empty_frame.place(relx=0.5, rely=0.5, anchor="center")
