import customtkinter as ctk
from theme import Colors, Fonts, Dims
from authentication.session import current_session
from services.auth_service import logout_user
from utils.animations import apply_hover_animation, animate_color
from services.event_bus import bus

MENU_ITEMS = [
    ("📊", "Dashboard"),
    ("🤖", "Aurex AI"),
    ("📋", "AI Planner")
]

TOOL_ITEMS = [
    ("📝", "Summarizer"),
    ("🎨", "Image Studio"),
    ("🔄", "File Converter"),
    ("⚙️", "Settings")
]

class SidebarMenuItem(ctk.CTkFrame):
    def __init__(self, parent, icon: str, label: str, is_active: bool = False, on_click=None, **kwargs):
        super().__init__(parent, fg_color="transparent", height=Dims.BTN_HEIGHT, corner_radius=Dims.RADIUS_PILL, **kwargs)
        self.pack_propagate(False)

        self._label_text = label
        self._on_click = on_click
        self._is_active = False

        self._container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=Dims.RADIUS_PILL, height=Dims.BTN_HEIGHT)
        self._container.pack(fill="both", expand=True)
        self._container.pack_propagate(False)

        # Icon
        self._icon_label = ctk.CTkLabel(
            self._container, text=icon, font=("Segoe UI Emoji", 16),
            text_color=Colors.TEXT_MUTED, width=28, fg_color="transparent"
        )
        self._icon_label.pack(side="left", padx=(16, 12))

        # Text
        self._text_label = ctk.CTkLabel(
            self._container, text=label, font=Fonts.MENU_ITEM,
            text_color=Colors.TEXT_SECONDARY, anchor="w", fg_color="transparent"
        )
        self._text_label.pack(side="left", fill="x", expand=True)

        # Active indicator (hidden by default)
        self._active_indicator = ctk.CTkFrame(self._container, fg_color="transparent", width=6, corner_radius=3)
        self._active_indicator.pack(side="right", fill="y", pady=6, padx=(0, 6))

        for widget in [self, self._container, self._icon_label, self._text_label]:
            widget.bind("<Button-1>", self._handle_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.configure(cursor="hand2")

        if is_active:
            self.set_active(True)

    def _handle_click(self, event=None):
        if self._on_click:
            self._on_click(self._label_text)

    def _on_enter(self, event=None):
        if not self._is_active:
            self._container.configure(fg_color=Colors.CARD_HOVER)
            animate_color(self._text_label, 'text_color', Colors.TEXT_SECONDARY, Colors.TEXT_PRIMARY)

    def _on_leave(self, event=None):
        if not self._is_active:
            self._container.configure(fg_color="transparent")
            animate_color(self._text_label, 'text_color', Colors.TEXT_PRIMARY, Colors.TEXT_SECONDARY)

    def set_active(self, active: bool):
        self._is_active = active
        if active:
            self._container.configure(fg_color=Colors.ACCENT_SUBTLE)
            self._text_label.configure(text_color=Colors.ACCENT_PRIMARY, font=Fonts.MENU_ITEM_ACTIVE)
            self._icon_label.configure(text_color=Colors.ACCENT_PRIMARY)
            self._active_indicator.configure(fg_color=Colors.ACCENT_PRIMARY)
        else:
            self._container.configure(fg_color="transparent")
            self._text_label.configure(text_color=Colors.TEXT_SECONDARY, font=Fonts.MENU_ITEM)
            self._icon_label.configure(text_color=Colors.TEXT_MUTED)
            self._active_indicator.configure(fg_color="transparent")

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, navigate_callback=None, logout_callback=None, **kwargs):
        super().__init__(
            parent, 
            fg_color="transparent", 
            width=Dims.SIDEBAR_WIDTH, 
            corner_radius=22,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            **kwargs
        )
        self.pack_propagate(False)

        self._navigate = navigate_callback
        self._logout = logout_callback
        self._menu_items = {}
        self._active_page = "Dashboard"

        self._build()

    def _build(self):
        # Brand Header
        brand_frame = ctk.CTkFrame(self, fg_color="transparent", height=70)
        brand_frame.pack(fill="x", padx=Dims.MAIN_PAD_X, pady=(24, 16))
        brand_frame.pack_propagate(False)

        try:
            import os
            from PIL import Image
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "backgrounds", "logo.png")
            logo_img = ctk.CTkImage(Image.open(logo_path), size=(32, 32))
            ctk.CTkLabel(brand_frame, image=logo_img, text="").pack(side="left", padx=(0, 12))
        except Exception:
            ctk.CTkLabel(brand_frame, text="◆", font=("Segoe UI", 24, "bold"), text_color=Colors.ACCENT_PRIMARY).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(brand_frame, text="AUREX", font=Fonts.BRAND, text_color=Colors.TEXT_PRIMARY).pack(side="left")

        # Separator
        sep = ctk.CTkFrame(self, fg_color=Colors.BORDER_SUBTLE, height=1)
        sep.pack(fill="x", padx=Dims.MAIN_PAD_X, pady=(0, 24))

        # Scrollable area for menu items to prevent overflow on smaller heights
        scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=4, pady=4)

        # Main Menu
        ctk.CTkLabel(scroll_container, text="MAIN MENU", font=Fonts.CAPTION, text_color=Colors.TEXT_DISABLED, anchor="w").pack(fill="x", padx=16, pady=(0, 8))
        for icon, label in MENU_ITEMS:
            item = SidebarMenuItem(scroll_container, icon=icon, label=label, is_active=(label == "Dashboard"), on_click=self._on_menu_click)
            item.pack(fill="x", padx=8, pady=2)
            self._menu_items[label] = item

        # Tools Menu
        ctk.CTkLabel(scroll_container, text="TOOLS", font=Fonts.CAPTION, text_color=Colors.TEXT_DISABLED, anchor="w").pack(fill="x", padx=16, pady=(24, 8))
        for icon, label in TOOL_ITEMS:
            item = SidebarMenuItem(scroll_container, icon=icon, label=label, on_click=self._on_menu_click)
            item.pack(fill="x", padx=8, pady=2)
            self._menu_items[label] = item

        # Upgrade Card
        upgrade_card = ctk.CTkFrame(
            self, fg_color=Colors.CARD_FLOATING, corner_radius=16, 
            border_width=1, border_color=Colors.BORDER_SUBTLE, height=155
        )
        upgrade_card.pack(fill="x", padx=16, pady=(8, 12))
        upgrade_card.pack_propagate(False)

        # Content for upgrade card
        planet_lbl = ctk.CTkLabel(upgrade_card, text="🪐", font=("Segoe UI Emoji", 26))
        planet_lbl.pack(anchor="w", padx=15, pady=(12, 2))

        title_lbl = ctk.CTkLabel(upgrade_card, text="Upgrade to Aurex Pro", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY)
        title_lbl.pack(anchor="w", padx=15)

        desc_lbl = ctk.CTkLabel(
            upgrade_card, 
            text="Unlock unlimited AI, premium features and cloud sync.", 
            font=Fonts.CAPTION, 
            text_color=Colors.TEXT_MUTED, 
            wraplength=200, 
            justify="left"
        )
        desc_lbl.pack(anchor="w", padx=15, pady=(2, 8))

        btn = ctk.CTkButton(
            upgrade_card, text="Upgrade Now  →", font=Fonts.CAPTION, 
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, 
            height=28, corner_radius=8,
            command=lambda: bus.publish("NAVIGATE_TO", "Upgrade")
        )
        btn.pack(fill="x", padx=15, pady=(0, 10))

        # Profile Card
        profile_card = ctk.CTkFrame(
            self, fg_color=Colors.CARD_BG, corner_radius=Dims.RADIUS_CARD, 
            border_width=Dims.BORDER_WIDTH, border_color=Colors.BORDER_SUBTLE, height=72
        )
        profile_card.pack(fill="x", padx=16, pady=(8, 24))
        profile_card.pack_propagate(False)
        apply_hover_animation(profile_card, 'border_color', Colors.BORDER_SUBTLE, Colors.ACCENT_SUBTLE)

        profile_inner = ctk.CTkFrame(profile_card, fg_color="transparent")
        profile_inner.pack(fill="both", expand=True, padx=12, pady=10)

        avatar = ctk.CTkFrame(profile_inner, width=40, height=40, corner_radius=20, fg_color=Colors.ACCENT_PRIMARY)
        avatar.pack(side="left", padx=(0, 12))
        avatar.pack_propagate(False)
        
        initials = "U"
        if current_session.full_name:
            parts = current_session.full_name.split()
            initials = parts[0][0].upper() + (parts[-1][0].upper() if len(parts) > 1 else "")

        ctk.CTkLabel(avatar, text=initials, font=("Segoe UI", 14, "bold"), text_color=Colors.TEXT_PRIMARY).place(relx=0.5, rely=0.5, anchor="center")

        info_frame = ctk.CTkFrame(profile_inner, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        name_lbl = ctk.CTkLabel(info_frame, text=current_session.full_name or current_session.username or "User", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w")
        name_lbl.pack(fill="x")
        email_lbl = ctk.CTkLabel(info_frame, text=current_session.email or "Premium Plan", font=Fonts.CAPTION, text_color=Colors.ACCENT_PRIMARY, anchor="w")
        email_lbl.pack(fill="x")
        
        # Bind clicks to navigate to Accounts
        for w in (profile_card, profile_inner, avatar, info_frame, name_lbl, email_lbl):
            try:
                w.bind("<Button-1>", lambda e: self._on_menu_click("Accounts"))
                # If they have children (like the initial label inside avatar), bind those too
                for child in w.winfo_children():
                    child.bind("<Button-1>", lambda e: self._on_menu_click("Accounts"))
            except Exception:
                pass

        logout_btn = ctk.CTkButton(
            profile_inner, text="↪", font=("Segoe UI", 16), 
            text_color=Colors.TEXT_MUTED, fg_color="transparent", 
            hover_color=Colors.CARD_HOVER, width=32, height=32, corner_radius=8, 
            command=self._on_logout
        )
        logout_btn.pack(side="right")

    def _on_menu_click(self, page_name: str):
        if page_name == self._active_page: return
        if self._active_page in self._menu_items:
            self._menu_items[self._active_page].set_active(False)
        self._active_page = page_name
        if page_name in self._menu_items:
            self._menu_items[page_name].set_active(True)
        if self._navigate:
            self._navigate(page_name)

    def _on_logout(self):
        logout_user()
        if self._logout:
            self._logout()

    def set_active(self, page_name: str):
        """Update highlight only — does not trigger navigation."""
        if page_name == self._active_page:
            return
        if self._active_page in self._menu_items:
            self._menu_items[self._active_page].set_active(False)
        self._active_page = page_name
        if page_name in self._menu_items:
            self._menu_items[page_name].set_active(True)
