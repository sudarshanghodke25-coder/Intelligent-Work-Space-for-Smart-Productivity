import customtkinter as ctk
import json
import os
from PIL import Image, ImageDraw
from pathlib import Path
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"

def create_circle_image(color, size=24):
    if isinstance(color, (tuple, list)):
        light_c, dark_c = color[0], color[1]
    else:
        light_c = dark_c = color
        
    img_light = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(img_light).ellipse((0, 0, size-1, size-1), fill=light_c)
    
    img_dark = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(img_dark).ellipse((0, 0, size-1, size-1), fill=dark_c)
    
    return ctk.CTkImage(light_image=img_light, dark_image=img_dark, size=(size, size))

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.settings = self._load_settings()
        
        # Main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._build_header()
        
        # Content Area - Full Width Now
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        self._build_panel(self.content_frame)

    def _load_settings(self):
        default = {
            "theme": "Dark",
            "font_color": Colors.TEXT_PRIMARY,
            "font_size": "Medium"
        }
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    return {**default, **json.load(f)}
            except:
                pass
        return default
        
    def _save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f)
            
    def _build_header(self):
        header_container = ctk.CTkFrame(self, fg_color="transparent")
        header_container.grid(row=0, column=0, sticky="ew", padx=4, pady=(8, 16))
        
        # Title area
        title_frame = ctk.CTkFrame(header_container, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 16))
        
        icon_frame = ctk.CTkFrame(title_frame, fg_color=Colors.CARD_BG, corner_radius=12, width=40, height=40)
        icon_frame.pack(side="left", padx=(0, 12))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="⚙️", font=("Segoe UI Emoji", 18)).pack(expand=True)
        
        text_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        text_frame.pack(side="left")
        ctk.CTkLabel(text_frame, text="Settings", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(text_frame, text="Manage your workspace appearance and account preferences.", font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY).pack(anchor="w")
        
        # Tabs area
        tabs_frame = ctk.CTkFrame(header_container, fg_color="transparent")
        tabs_frame.pack(fill="x")
        
        tabs = [
            ("⬡ Appearance", True), ("□ Workspace", False), ("👤 Account", False), 
            ("🔔 Notifications", False), ("🔒 Security", False), ("ℹ️ About", False)
        ]
        
        for text, active in tabs:
            color = Colors.ACCENT_PRIMARY if active else Colors.TEXT_MUTED
            font = Fonts.BODY_BOLD if active else Fonts.BODY
            tab = ctk.CTkLabel(tabs_frame, text=text, font=font, text_color=color, cursor="hand2")
            tab.pack(side="left", padx=(0, 24))
            
            if active:
                indicator = ctk.CTkFrame(tab, fg_color=Colors.ACCENT_PRIMARY, height=2)
                indicator.place(relx=0, rely=0.9, relwidth=1)

    def _build_panel(self, parent):
        left_container = ctk.CTkFrame(parent, fg_color="transparent")
        left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_container.grid_rowconfigure(0, weight=1)
        left_container.grid_columnconfigure(0, weight=1)
        
        scroll = ctk.CTkScrollableFrame(left_container, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        
        app_card = GlassCard(scroll, title="")
        app_card.pack(fill="x", pady=(0, 16))
        
        # Appearance Header
        ctk.CTkLabel(app_card.content, text="Appearance", font=("Sora", 14, "bold"), text_color=Colors.ACCENT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(app_card.content, text="Customize the look and feel of your workspace.", font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(0, 24))
        
        # Theme (Dark/Light)
        ctk.CTkLabel(app_card.content, text="Theme", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(app_card.content, text="Choose your preferred visual theme", font=("Inter", 11), text_color=Colors.TEXT_MUTED).pack(anchor="w", pady=(0, 12))
        
        themes_frame = ctk.CTkFrame(app_card.content, fg_color="transparent")
        themes_frame.pack(fill="x", pady=(0, 24))
        
        themes = ["Light", "Dark"]
        self.theme_boxes = {}
        for theme in themes:
            is_active = self.settings["theme"] == theme
            t_box = ctk.CTkFrame(themes_frame, width=90, height=60, corner_radius=8, 
                                 fg_color=Colors.CARD_FLOATING if is_active else Colors.CARD_BG,
                                 border_width=1 if is_active else 0,
                                 border_color=Colors.ACCENT_PRIMARY)
            t_box.pack(side="left", padx=(0, 12))
            t_box.pack_propagate(False)
            t_box.bind("<Button-1>", lambda e, t=theme: self._set_theme(t))
            
            lbl = ctk.CTkLabel(t_box, text=theme, font=("Inter", 10), text_color=Colors.TEXT_PRIMARY)
            lbl.pack(side="bottom", pady=4)
            lbl.bind("<Button-1>", lambda e, t=theme: self._set_theme(t))
            
            if is_active:
                check = ctk.CTkLabel(t_box, text="✓", font=("Inter", 10, "bold"), text_color="white", fg_color=Colors.ACCENT_PRIMARY, corner_radius=4)
                check.place(relx=0.8, rely=0.1, anchor="n")
                
            self.theme_boxes[theme] = t_box
                
        # Font Color
        color_frame = ctk.CTkFrame(app_card.content, fg_color="transparent")
        color_frame.pack(fill="x", pady=(16, 24))
        
        info_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        info_frame.pack(side="left")
        ctk.CTkLabel(info_frame, text="Font Color", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="Choose your preferred font color", font=("Inter", 11), text_color=Colors.TEXT_MUTED).pack(anchor="w")
        
        self.palette_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        self.palette_frame.pack(side="right")
        
        self._build_font_colors()
                
        # Font Size
        font_frame = ctk.CTkFrame(app_card.content, fg_color="transparent")
        font_frame.pack(fill="x", pady=(0, 8))
        f_info = ctk.CTkFrame(font_frame, fg_color="transparent")
        f_info.pack(side="left")
        ctk.CTkLabel(f_info, text="Font Size", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(f_info, text="Adjust the interface font size", font=("Inter", 11), text_color=Colors.TEXT_MUTED).pack(anchor="w")
        
        self.font_size_menu = ctk.CTkOptionMenu(font_frame, values=["Small", "Medium", "Large"], width=120, fg_color=Colors.INPUT_BG, 
                          button_color=Colors.ACCENT_PRIMARY, button_hover_color=Colors.ACCENT_HOVER, command=self._set_font_size)
        self.font_size_menu.set(self.settings["font_size"])
        self.font_size_menu.pack(side="right")
        
        # Bottom Actions Bar
        actions_bar = ctk.CTkFrame(left_container, fg_color=Colors.CARD_BG, corner_radius=16, height=60, border_width=1, border_color=Colors.BORDER_SUBTLE)
        actions_bar.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        actions_bar.pack_propagate(False)
        
        info = ctk.CTkFrame(actions_bar, fg_color="transparent")
        info.pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(info, text="Quick Actions", font=("Sora", 12, "bold"), text_color=Colors.ACCENT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(info, text="Reset or synchronize your settings", font=("Inter", 10), text_color=Colors.TEXT_MUTED).pack(anchor="w")
        
        save_btn = ctk.CTkButton(actions_bar, text="✓ Save Changes", fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, width=120, command=self._on_save)
        save_btn.pack(side="right", padx=16, pady=16)
        
        reset_btn = ctk.CTkButton(actions_bar, text="↺ Reset to Defaults", fg_color="transparent", border_width=1, border_color=Colors.BORDER_SUBTLE, hover_color=Colors.CARD_HOVER, text_color=Colors.TEXT_PRIMARY, width=130, command=self._on_reset)
        reset_btn.pack(side="right", padx=(0, 8), pady=16)

    def _build_font_colors(self):
        for widget in self.palette_frame.winfo_children():
            widget.destroy()
            
        colors = [Colors.TEXT_PRIMARY, "#3B82F6", "#06B6D4", "#10B981", "#F59E0B", "#EF4444", "#EC4899", "#8B5CF6"]
        for c in colors:
            btn = ctk.CTkButton(self.palette_frame, text="", image=create_circle_image(c, 18), 
                                width=24, height=24, fg_color="transparent", hover_color=Colors.CARD_HOVER,
                                command=lambda col=c: self._set_font_color(col))
            btn.pack(side="left", padx=2)
            if c == self.settings["font_color"]:
                btn.configure(text="✓", text_color="white", font=("Inter", 10, "bold"))

    def _set_theme(self, theme):
        self.settings["theme"] = theme
        if theme == "Dark":
            ctk.set_appearance_mode("dark")
        elif theme == "Light":
            ctk.set_appearance_mode("light")

            
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Rebuild layout to show checkmark on the correct theme box
        self._build_panel(self.content_frame)

    def _set_font_color(self, color):
        self.settings["font_color"] = color
        self._build_font_colors()
        
        def update_widgets(widget):
            # Only update elements that likely hold standard text
            if isinstance(widget, ctk.CTkLabel):
                try:
                    widget.configure(text_color=color)
                except:
                    pass
            for child in widget.winfo_children():
                update_widgets(child)
                
        update_widgets(self.winfo_toplevel())

    def _set_font_size(self, size):
        self.settings["font_size"] = size
        size_map = {"Small": 10, "Medium": 12, "Large": 16}
        font_size = size_map.get(size, 12)
        
        def update_widgets(widget):
            if hasattr(widget, "cget") and hasattr(widget, "configure"):
                try:
                    font = widget.cget("font")
                    if isinstance(font, tuple) and len(font) >= 2:
                        # Create new font tuple with updated size
                        new_font = (font[0], font_size) + font[2:]
                        widget.configure(font=new_font)
                except:
                    pass
            for child in widget.winfo_children():
                update_widgets(child)
                
        update_widgets(self.winfo_toplevel())

    def _on_save(self):
        # Save settings and enforce environment
        self._save_settings()
        self._set_theme(self.settings["theme"])
        self._set_font_color(self.settings["font_color"])
        self._set_font_size(self.settings["font_size"])

    def _on_reset(self):
        self.settings = {
            "theme": "Dark",
            "font_color": Colors.TEXT_PRIMARY,
            "font_size": "Medium"
        }
        self._on_save()
