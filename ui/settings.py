import customtkinter as ctk
import json
from pathlib import Path
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from authentication.session import current_session

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.GLASS_FILL_LIGHT,
            scrollbar_button_hover_color=Colors.GLASS_FILL_HOVER,
        )
        self.scroll.pack(fill="both", expand=True)
        
        self.settings = self._load_settings()

        self._build_header()
        self._build_content()

    def _load_settings(self):
        default = {
            "theme": "Cosmic Dark",
            "bg_intensity": 50,
            "glass_transparency": 50,
            "card_brightness": 50,
            "accent_color": "Purple"
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
        header = ctk.CTkFrame(self.scroll, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="⚙️ Settings",
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

        ctk.CTkLabel(
            header, text="Manage your workspace appearance and account preferences.",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

    def _build_content(self):
        # Appearance Section
        app_card = GlassCard(self.scroll, title="Appearance")
        app_card.pack(fill="x", padx=4, pady=10)
        
        # Theme Selector
        ctk.CTkLabel(app_card.content, text="Theme", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0,5))
        self.theme_var = ctk.StringVar(value=self.settings["theme"])
        theme_menu = ctk.CTkOptionMenu(
            app_card.content, values=["Cosmic Dark", "Midnight Glass", "Aurora"],
            variable=self.theme_var, command=self._on_setting_change,
            fg_color=Colors.ENTRY_BG, button_color=Colors.ACCENT_PRIMARY, button_hover_color=Colors.ACCENT_HOVER
        )
        theme_menu.pack(fill="x", pady=(0, 15))
        
        # Sliders
        self._add_slider(app_card.content, "Background Intensity", "bg_intensity")
        self._add_slider(app_card.content, "Glass Transparency", "glass_transparency")
        self._add_slider(app_card.content, "Card Brightness", "card_brightness")
        
        # Accent Color
        ctk.CTkLabel(app_card.content, text="Accent Color", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(10,5))
        self.accent_var = ctk.StringVar(value=self.settings["accent_color"])
        accent_menu = ctk.CTkOptionMenu(
            app_card.content, values=["Purple", "Blue", "Green", "Red", "Gold"],
            variable=self.accent_var, command=self._on_setting_change,
            fg_color=Colors.ENTRY_BG, button_color=Colors.ACCENT_PRIMARY, button_hover_color=Colors.ACCENT_HOVER
        )
        accent_menu.pack(fill="x", pady=(0, 5))

        # Account Section
        acc_card = GlassCard(self.scroll, title="Account Settings")
        acc_card.pack(fill="x", padx=4, pady=10)
        
        info_frame = ctk.CTkFrame(acc_card.content, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0,15))
        
        ctk.CTkLabel(info_frame, text=f"Username: {current_session.username}", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"Email: {current_session.email}", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x")
        
        btns_frame = ctk.CTkFrame(acc_card.content, fg_color="transparent")
        btns_frame.pack(fill="x")
        
        ctk.CTkButton(btns_frame, text="Update Profile", fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, state="disabled").pack(side="left", padx=(0,10))
        # ctk.CTkButton(btns_frame, text="Change Password", fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER).pack(side="left", padx=(0,10))
        # ctk.CTkButton(btns_frame, text="Delete Account", fg_color=Colors.ERROR, hover_color="#dc2626").pack(side="left")

    def _add_slider(self, parent, label_text, setting_key):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame, text=label_text, font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left")
        slider = ctk.CTkSlider(
            frame, from_=0, to=100, number_of_steps=100,
            button_color=Colors.ACCENT_PRIMARY, button_hover_color=Colors.ACCENT_HOVER,
            command=lambda v, k=setting_key: self._on_slider_change(k, v)
        )
        slider.set(self.settings[setting_key])
        slider.pack(side="right", fill="x", expand=True, padx=(15,0))
        
    def _on_slider_change(self, key, value):
        self.settings[key] = int(value)
        self._save_settings()
        
    def _on_setting_change(self, choice):
        self.settings["theme"] = self.theme_var.get()
        self.settings["accent_color"] = self.accent_var.get()
        self._save_settings()
        
        # Add feedback if it doesn't exist
        if not hasattr(self, 'restart_lbl'):
            self.restart_lbl = ctk.CTkLabel(self.scroll, text="A restart is required to fully apply appearance changes.", font=Fonts.SMALL_BOLD, text_color=Colors.WARNING)
            self.restart_lbl.pack(pady=10)
