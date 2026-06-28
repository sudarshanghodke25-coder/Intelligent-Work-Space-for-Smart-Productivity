import customtkinter as ctk
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from authentication.session import current_session
from services.auth_service import logout_user
from services.event_bus import bus

class AccountsView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.CARD_FLOATING,
            scrollbar_button_hover_color=Colors.CARD_HOVER,
        )
        self.scroll.pack(fill="both", expand=True)
        
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self.scroll, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="👤 Accounts",
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

        ctk.CTkLabel(
            header, text="Manage your account details and information.",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(side="top", fill="x")

    def _build_content(self):
        # Account Section
        acc_card = GlassCard(self.scroll, title="Account Information")
        acc_card.pack(fill="x", padx=4, pady=10)
        
        info_frame = ctk.CTkFrame(acc_card.content, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 24))
        
        # User details grid
        ctk.CTkLabel(info_frame, text="Full Name", font=("Inter", 11, "bold"), text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"{current_session.full_name}", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(info_frame, text="Username", font=("Inter", 11, "bold"), text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"@{current_session.username}", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(info_frame, text="Email Address", font=("Inter", 11, "bold"), text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"{current_session.email}", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(info_frame, text="Date of Birth", font=("Inter", 11, "bold"), text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"{current_session.dob or 'Not provided'}", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(info_frame, text="Age", font=("Inter", 11, "bold"), text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text=f"{current_session.age or '--'}", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(info_frame, text="Password", font=("Inter", 11, "bold"), text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x")
        ctk.CTkLabel(info_frame, text="********", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x")
        
        # Action Buttons
        btns_frame = ctk.CTkFrame(acc_card.content, fg_color="transparent")
        btns_frame.pack(fill="x")
        
        ctk.CTkButton(btns_frame, text="Update Profile", fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, state="disabled", height=Dims.BTN_HEIGHT, corner_radius=Dims.BTN_CORNER).pack(side="left", padx=(0,10))
        
        logout_btn = ctk.CTkButton(btns_frame, text="Logout", fg_color="transparent", border_width=1, border_color=Colors.ERROR, text_color=Colors.ERROR, hover_color=Colors.ERROR_HOVER, height=Dims.BTN_HEIGHT, corner_radius=Dims.BTN_CORNER, command=self._on_logout)
        logout_btn.pack(side="left")
        
    def _on_logout(self):
        """Logs the user out and triggers the application transition to AuthView."""
        logout_user()
        bus.publish("LOGOUT")
