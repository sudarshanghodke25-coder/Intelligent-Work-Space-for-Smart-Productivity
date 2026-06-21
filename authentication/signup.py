import customtkinter as ctk
from theme import Colors, Fonts, Dims
from services.auth_service import signup_user

class SignupView(ctk.CTkFrame):
    def __init__(self, parent, on_signup_success, on_navigate_login, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._on_signup_success = on_signup_success
        self._on_navigate_login = on_navigate_login

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Wider glass card
        self.card = ctk.CTkFrame(
            self,
            fg_color=Colors.GLASS_FILL,
            corner_radius=20,
            border_width=1,
            border_color=Colors.GLASS_BORDER,
            width=550,  # Increased width for signup
            height=650, # Increased height
        )
        self.card.grid(row=0, column=0)
        self.card.grid_propagate(False)

        self.inner = ctk.CTkFrame(self.card, fg_color="transparent")
        self.inner.pack(fill="both", expand=True, padx=40, pady=20)

        self._build_header()
        self._build_form()

    def _build_header(self):
        ctk.CTkLabel(
            self.inner, text="◆ AUREX",
            font=("Segoe UI", 24, "bold"), text_color=Colors.ACCENT_GLOW,
            fg_color="transparent"
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            self.inner, text="Create Account",
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent"
        ).pack(pady=(0, 15))

    def _build_form(self):
        self.form_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.form_frame.pack(fill="x", expand=True)

        self.full_name_entry = self._create_field("Full Name", "Enter your full name")
        self.email_entry = self._create_field("Email", "Enter your email")
        self.username_entry = self._create_field("Username", "Choose a username")
        self.password_entry = self._create_field("Password", "Create a password", show="•")
        self.confirm_entry = self._create_field("Confirm Password", "Confirm your password", show="•")

        self.error_label = ctk.CTkLabel(
            self.form_frame, text="",
            font=Fonts.SMALL, text_color=Colors.ERROR,
            fg_color="transparent", anchor="w"
        )
        self.error_label.pack(fill="x", pady=(0, 5))

        signup_btn = ctk.CTkButton(
            self.form_frame,
            text="Create Account",
            font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Dims.BTN_CORNER,
            height=Dims.BTN_HEIGHT,
            command=self._handle_signup
        )
        signup_btn.pack(fill="x", pady=(0, 15))

        login_btn = ctk.CTkLabel(
            self.form_frame, text="Already have an account? Login",
            font=Fonts.SMALL, text_color=Colors.ACCENT_GLOW,
            cursor="hand2", fg_color="transparent"
        )
        login_btn.pack()
        login_btn.bind("<Button-1>", lambda e: self._on_navigate_login())
        login_btn.bind("<Enter>", lambda e: login_btn.configure(text_color=Colors.TEXT_PRIMARY))
        login_btn.bind("<Leave>", lambda e: login_btn.configure(text_color=Colors.ACCENT_GLOW))

    def _create_field(self, label, placeholder, show=None):
        ctk.CTkLabel(
            self.form_frame, text=label,
            font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(fill="x", pady=(0, 2))

        entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text=placeholder,
            placeholder_text_color=Colors.TEXT_DIM,
            font=Fonts.ENTRY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.ENTRY_BG,
            border_width=1, border_color=Colors.ENTRY_BORDER,
            corner_radius=Dims.ENTRY_CORNER,
            height=Dims.ENTRY_HEIGHT,
            show=show if show else ""
        )
        entry.pack(fill="x", pady=(0, 10))
        return entry

    def _handle_signup(self):
        full_name = self.full_name_entry.get().strip()
        email = self.email_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm = self.confirm_entry.get().strip()

        if not all([full_name, email, username, password, confirm]):
            self.error_label.configure(text="Please fill in all fields.")
            return

        if password != confirm:
            self.error_label.configure(text="Passwords do not match.")
            return

        if len(password) < 6:
            self.error_label.configure(text="Password must be at least 6 characters.")
            return

        success, message = signup_user(full_name, email, username, password)
        if success:
            self.error_label.configure(text="")
            self._on_signup_success()
        else:
            self.error_label.configure(text=message)
