import customtkinter as ctk
from theme import Colors, Fonts, Dims
from authentication.session import current_session
from services.auth_service import logout_user

MENU_ITEMS = [
    ("📊", "Dashboard"),
    ("🤖", "Aurex AI"),
    ("📋", "AI Planner"),
    ("✅", "Task Manager"),
    ("📝", "Notes & Docs"),
    ("📅", "Calendar"),
    ("📈", "Analytics"),
    ("🕐", "History"),
]

TOOL_ITEMS = [
    ("🎯", "Focus Mode"),
    ("🏆", "Goal Tracker"),
    ("⏱️", "Pomodoro Timer"),
    ("🔄", "Habit Tracker"),
]

class SidebarMenuItem(ctk.CTkFrame):
    def __init__(self, parent, icon: str, label: str, is_active: bool = False, on_click=None, **kwargs):
        super().__init__(parent, fg_color="transparent", height=Dims.MENU_ITEM_HEIGHT, corner_radius=10, **kwargs)
        self.pack_propagate(False)

        self._label_text = label
        self._on_click = on_click
        self._is_active = False

        self._container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=10, height=Dims.MENU_ITEM_HEIGHT)
        self._container.pack(fill="both", expand=True)
        self._container.pack_propagate(False)

        self._icon_label = ctk.CTkLabel(self._container, text=icon, font=("Segoe UI", 15), text_color=Colors.TEXT_SECONDARY, width=24, fg_color="transparent")
        self._icon_label.pack(side="left", padx=(12, 8))

        self._text_label = ctk.CTkLabel(self._container, text=label, font=Fonts.MENU_ITEM, text_color=Colors.TEXT_SECONDARY, anchor="w", fg_color="transparent")
        self._text_label.pack(side="left", fill="x", expand=True)

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
            self._container.configure(fg_color=Colors.GLASS_FILL_LIGHT)

    def _on_leave(self, event=None):
        if not self._is_active:
            self._container.configure(fg_color="transparent")

    def set_active(self, active: bool):
        self._is_active = active
        if active:
            self._container.configure(fg_color=Colors.ACCENT_SUBTLE)
            self._text_label.configure(text_color=Colors.TEXT_PRIMARY, font=Fonts.MENU_ITEM_ACTIVE)
            self._icon_label.configure(text_color=Colors.ACCENT_GLOW)
        else:
            self._container.configure(fg_color="transparent")
            self._text_label.configure(text_color=Colors.TEXT_SECONDARY, font=Fonts.MENU_ITEM)
            self._icon_label.configure(text_color=Colors.TEXT_SECONDARY)

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, navigate_callback=None, logout_callback=None, **kwargs):
        super().__init__(parent, fg_color=Colors.BG_SIDEBAR, width=Dims.SIDEBAR_WIDTH, corner_radius=0, border_width=0, **kwargs)
        self.pack_propagate(False)

        self._navigate = navigate_callback
        self._logout = logout_callback
        self._menu_items = {}
        self._active_page = "Dashboard"

        self._build()

    def _build(self):
        brand_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        brand_frame.pack(fill="x", padx=Dims.SIDEBAR_PAD_X, pady=(20, 8))
        brand_frame.pack_propagate(False)

        ctk.CTkLabel(brand_frame, text="◆", font=("Segoe UI", 22, "bold"), text_color=Colors.ACCENT_GLOW, fg_color="transparent").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(brand_frame, text="AUREX", font=Fonts.BRAND, text_color=Colors.TEXT_PRIMARY, fg_color="transparent").pack(side="left")

        sep = ctk.CTkFrame(self, fg_color=Colors.GLASS_BORDER, height=1)
        sep.pack(fill="x", padx=Dims.SIDEBAR_PAD_X, pady=(4, 12))

        ctk.CTkLabel(self, text="MENU", font=Fonts.CAPTION, text_color=Colors.TEXT_DIM, anchor="w", fg_color="transparent").pack(fill="x", padx=Dims.SIDEBAR_PAD_X + 4, pady=(0, 4))
        for icon, label in MENU_ITEMS:
            item = SidebarMenuItem(self, icon=icon, label=label, is_active=(label == "Dashboard"), on_click=self._on_menu_click)
            item.pack(fill="x", padx=8, pady=1)
            self._menu_items[label] = item

        ctk.CTkLabel(self, text="TOOLS", font=Fonts.CAPTION, text_color=Colors.TEXT_DIM, anchor="w", fg_color="transparent").pack(fill="x", padx=Dims.SIDEBAR_PAD_X + 4, pady=(16, 4))
        for icon, label in TOOL_ITEMS:
            item = SidebarMenuItem(self, icon=icon, label=label, on_click=self._on_menu_click)
            item.pack(fill="x", padx=8, pady=1)
            self._menu_items[label] = item
            
        settings_item = SidebarMenuItem(self, icon="⚙️", label="Settings", on_click=self._on_menu_click)
        settings_item.pack(fill="x", padx=8, pady=(16, 1))
        self._menu_items["Settings"] = settings_item

        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Profile Card
        profile_card = ctk.CTkFrame(self, fg_color=Colors.GLASS_FILL, corner_radius=12, border_width=1, border_color=Colors.GLASS_BORDER, height=Dims.PROFILE_CARD_H)
        profile_card.pack(fill="x", padx=12, pady=(8, 16))
        profile_card.pack_propagate(False)

        profile_inner = ctk.CTkFrame(profile_card, fg_color="transparent")
        profile_inner.pack(fill="both", expand=True, padx=10, pady=8)

        avatar = ctk.CTkFrame(profile_inner, width=38, height=38, corner_radius=19, fg_color=Colors.ACCENT_PRIMARY)
        avatar.pack(side="left", padx=(0, 10))
        avatar.pack_propagate(False)
        
        initials = "U"
        if current_session.full_name:
            parts = current_session.full_name.split()
            initials = parts[0][0].upper() + (parts[-1][0].upper() if len(parts) > 1 else "")

        ctk.CTkLabel(avatar, text=initials, font=("Segoe UI", 13, "bold"), text_color=Colors.TEXT_PRIMARY, fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")

        info_frame = ctk.CTkFrame(profile_inner, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(info_frame, text=current_session.full_name or current_session.username or "User", font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w", fg_color="transparent").pack(fill="x")
        ctk.CTkLabel(info_frame, text=current_session.email or "", font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED, anchor="w", fg_color="transparent").pack(fill="x")

        logout_btn = ctk.CTkButton(profile_inner, text="↪", font=("Segoe UI", 16), text_color=Colors.TEXT_SECONDARY, fg_color="transparent", hover_color=Colors.GLASS_FILL_HOVER, width=30, height=30, corner_radius=8, command=self._on_logout)
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
        self._on_menu_click(page_name)
