import customtkinter as ctk
from theme import Colors, Fonts, Dims
from services.auth_service import login_user

class LoginView(ctk.CTkFrame):
    def __init__(self, parent, on_login_success, on_navigate_signup, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_login_success = on_login_success
        self._on_navigate_signup = on_navigate_signup

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Wider glass card
        self.card = ctk.CTkFrame(
            self,
            fg_color=Colors.CARD_BG,
            corner_radius=20,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            width=500,  # Increased width
            height=550,
        )
        self.card.grid(row=0, column=0)
        self.card.grid_propagate(False)

        self.inner = ctk.CTkFrame(self.card, fg_color="transparent")
        self.inner.pack(fill="both", expand=True, padx=40, pady=40)

        self._build_header()
        self._build_form()

    def _build_header(self):
        ctk.CTkLabel(
            self.inner, text="◆",
            font=("Segoe UI", 36, "bold"), text_color=Colors.ACCENT_PRIMARY,
            fg_color="transparent"
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            self.inner, text="FLOWSPACE",
            font=("Segoe UI", 28, "bold"), text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent"
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            self.inner, text="Welcome Back",
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent"
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            self.inner, text="Sign in to your workspace",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY,
            fg_color="transparent"
        ).pack(pady=(0, 25))

    def _build_form(self):
        self.form_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.form_frame.pack(fill="x", expand=True)

        ctk.CTkLabel(
            self.form_frame, text="Email",
            font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(fill="x", pady=(0, 5))

        self.email_entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text="Enter your email",
            placeholder_text_color=Colors.TEXT_DIM,
            font=Fonts.ENTRY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.INPUT_BG,
            border_width=1, border_color=Colors.INPUT_BORDER,
            corner_radius=Dims.ENTRY_CORNER,
            height=Dims.ENTRY_HEIGHT
        )
        self.email_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            self.form_frame, text="Password",
            font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(fill="x", pady=(0, 5))

        self.password_entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text="Enter your password",
            placeholder_text_color=Colors.TEXT_DIM,
            font=Fonts.ENTRY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.INPUT_BG,
            border_width=1, border_color=Colors.INPUT_BORDER,
            corner_radius=Dims.ENTRY_CORNER,
            height=Dims.ENTRY_HEIGHT,
            show="•"
        )
        self.password_entry.pack(fill="x", pady=(0, 10))

        self.error_label = ctk.CTkLabel(
            self.form_frame, text="",
            font=Fonts.SMALL, text_color=Colors.ERROR,
            fg_color="transparent", anchor="w"
        )
        self.error_label.pack(fill="x", pady=(0, 10))

        login_btn = ctk.CTkButton(
            self.form_frame,
            text="Login",
            font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Dims.BTN_CORNER,
            height=Dims.BTN_HEIGHT,
            command=self._handle_login
        )
        login_btn.pack(fill="x", pady=(0, 15))

        # Links
        links_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        links_frame.pack(fill="x")

        forgot_btn = ctk.CTkLabel(
            links_frame, text="Forgot Password?",
            font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY,
            cursor="hand2", fg_color="transparent"
        )
        forgot_btn.pack(side="left")
        forgot_btn.bind("<Enter>", lambda e: forgot_btn.configure(text_color=Colors.TEXT_PRIMARY))
        forgot_btn.bind("<Leave>", lambda e: forgot_btn.configure(text_color=Colors.TEXT_SECONDARY))

        create_btn = ctk.CTkLabel(
            links_frame, text="Create Account",
            font=Fonts.SMALL, text_color=Colors.ACCENT_PRIMARY,
            cursor="hand2", fg_color="transparent"
        )
        create_btn.pack(side="right")
        create_btn.bind("<Button-1>", lambda e: self._on_navigate_signup())
        create_btn.bind("<Enter>", lambda e: create_btn.configure(text_color=Colors.TEXT_PRIMARY))
        create_btn.bind("<Leave>", lambda e: create_btn.configure(text_color=Colors.ACCENT_PRIMARY))

    def _handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            self.error_label.configure(text="Please enter both email and password.")
            return

        success, message = login_user(email, password)
        if success:
            self.error_label.configure(text="")
            self._on_login_success()
        else:
            self.error_label.configure(text=message)
