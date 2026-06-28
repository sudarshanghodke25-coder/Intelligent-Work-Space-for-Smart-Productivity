"""
AuthView — Login / Signup authentication frame with glassmorphism styling.
"""
import customtkinter as ctk
import math
from theme import Colors, Fonts, Dims
from services.auth_service import seamless_auth, login_user, signup_user, check_active_session, clear_saved_profile

class AuthView(ctk.CTkFrame):
    """
    Authentication screen with login/signup toggle.
    Centered glass card over the nebula background.
    """

    def __init__(self, parent, on_auth_success=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._on_auth_success = on_auth_success
        
        has_profile, auto_login, profile_data = check_active_session()
        self._saved_profile_data = profile_data
        
        self._mode = "login"

        # Center the auth card
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Outer glass card - Dual Pane layout (wider)
        self.card = ctk.CTkFrame(
            self,
            fg_color=Colors.CARD_BG,
            corner_radius=20,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            width=960,  
            height=Dims.AUTH_CARD_H,
        )
        self.card.grid(row=0, column=0)
        self.card.grid_propagate(False)

        # Left pane (Auth Form)
        self.left_pane = ctk.CTkFrame(self.card, fg_color="transparent", width=480)
        self.left_pane.pack(side="left", fill="both", expand=True, padx=(36, 20), pady=30)
        
        # Right pane (Visual Graphic)
        self.right_pane = ctk.CTkFrame(self.card, fg_color="transparent", width=480)
        self.right_pane.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=20)

        self._build_header()
        self._build_form()
        self._build_graphic()
        
    def _trigger_success(self):
        if self._on_auth_success:
            self._on_auth_success()

    def _build_header(self):
        """Build the AUREX brand header."""
        header_frame = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        header_frame.pack(pady=(0, 20))
        
        ctk.CTkLabel(
            header_frame, text="◆",
            font=("Segoe UI", 36, "bold"), text_color=Colors.ACCENT_PRIMARY,
            fg_color="transparent"
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            header_frame, text="AUREX",
            font=("Segoe UI", 28, "bold"), text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent"
        ).pack(pady=(0, 4))

        self.subtitle = ctk.CTkLabel(
            header_frame, text="Sign in to your workspace",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY,
            fg_color="transparent"
        )
        self.subtitle.pack(pady=(0, 0))

    def _build_form(self):
        """Build the login/signup form fields."""
        self.form_frame = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        self.form_frame.pack(fill="x", expand=True)
        self._populate_form()

    def _populate_form(self):
        """Populate form fields based on current mode."""
        for widget in self.form_frame.winfo_children():
            widget.destroy()
            
        self.remember_var = ctk.BooleanVar(value=True)

        if self._mode == "signup":
            self.subtitle.configure(text="Create a new workspace account")
            self._create_input_field("Full Name", "E.g., John Doe", "name_entry")
            self._create_input_field("Username", "E.g., johndoe", "username_entry")
            self._create_input_field("Email", "E.g., johndoe@aurex.com", "email_entry")
            self._create_input_field("Date of Birth (YYYY-MM-DD)", "E.g., 2000-01-01", "dob_entry")
            
            # Age Label
            self.age_label = ctk.CTkLabel(
                self.form_frame, text="Age: --",
                font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_PRIMARY,
                fg_color="transparent", anchor="w"
            )
            self.age_label.pack(fill="x", pady=(0, 4))
            self._computed_age = None
            self.dob_entry.bind("<KeyRelease>", self._calculate_age)

            self._create_input_field("Password", "••••••••", "password_entry", show="•")
            
            btn_text = "Sign Up"
            auth_command = self._authenticate_signup
            toggle_text = "Already have an account? Log in"
        else:
            self.subtitle.configure(text="Sign in to your workspace")
            self._create_input_field("Email", "E.g., johndoe@aurex.com", "email_entry")
            self._create_input_field("Password", "••••••••", "password_entry", show="•")
            
            # Prefill if remembered
            if self._saved_profile_data and self._saved_profile_data.get("email"):
                self.email_entry.insert(0, self._saved_profile_data["email"])
            if self._saved_profile_data and self._saved_profile_data.get("password"):
                self.password_entry.insert(0, self._saved_profile_data["password"])
            
            # Remember me checkbox
            rem_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            rem_frame.pack(fill="x", pady=(0, 12))
            ctk.CTkCheckBox(
                rem_frame, text="Remember me", font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY,
                variable=self.remember_var, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
                border_color=Colors.BORDER_HOVER
            ).pack(side="left")
            
            btn_text = "Log In"
            auth_command = self._authenticate_login
            toggle_text = "Don't have an account? Sign up"

        # Error message label
        self.error_label = ctk.CTkLabel(
            self.form_frame, text="",
            font=Fonts.SMALL, text_color=Colors.ERROR,
            fg_color="transparent", anchor="center"
        )
        self.error_label.pack(fill="x", pady=(2, 4))

        # Primary button
        auth_btn = ctk.CTkButton(
            self.form_frame,
            text=btn_text,
            width=140,
            font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Dims.BTN_CORNER,
            height=Dims.BTN_HEIGHT,
            command=auth_command
        )
        auth_btn.pack(anchor="w", pady=(8, 12))

        # Toggle link
        toggle_btn = ctk.CTkLabel(
            self.form_frame, text=toggle_text,
            font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY,
            cursor="hand2", fg_color="transparent"
        )
        toggle_btn.pack(anchor="w")
        toggle_btn.bind("<Button-1>", self._toggle_mode)
        toggle_btn.bind("<Enter>", lambda e: toggle_btn.configure(text_color=Colors.TEXT_PRIMARY))
        toggle_btn.bind("<Leave>", lambda e: toggle_btn.configure(text_color=Colors.TEXT_SECONDARY))

    def _create_input_field(self, label, placeholder, attr_name, show=""):
        """Helper to create consistent input fields."""
        ctk.CTkLabel(
            self.form_frame, text=label,
            font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(fill="x", pady=(0, 4))

        entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text=placeholder,
            placeholder_text_color=Colors.TEXT_DIM,
            font=Fonts.ENTRY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.INPUT_BG,
            border_width=1, border_color=Colors.INPUT_BORDER,
            corner_radius=Dims.ENTRY_CORNER,
            height=Dims.ENTRY_HEIGHT,
            width=380,
            show=show
        )
        entry.pack(anchor="w", pady=(0, 12))
        setattr(self, attr_name, entry)

    def _switch_account(self, event=None):
        clear_saved_profile()
        self._mode = "login"
        self._populate_form()

    def _toggle_mode(self, event=None):
        """Switch between login and signup modes."""
        self._mode = "signup" if self._mode == "login" else "login"
        self._populate_form()

    def _calculate_age(self, event=None):
        if not hasattr(self, "dob_entry") or not hasattr(self, "age_label"):
            return
        dob_text = self.dob_entry.get().strip()
        if len(dob_text) == 10 and dob_text.count("-") == 2:
            try:
                from datetime import datetime
                dob_date = datetime.strptime(dob_text, "%Y-%m-%d")
                today = datetime.now()
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                if age >= 0:
                    self.age_label.configure(text=f"Age: {age} years old", text_color=Colors.SUCCESS)
                    self._computed_age = age
                else:
                    self.age_label.configure(text="Age: Invalid", text_color=Colors.ERROR)
                    self._computed_age = None
            except ValueError:
                self.age_label.configure(text="Age: Invalid format", text_color=Colors.ERROR)
                self._computed_age = None
        else:
            self.age_label.configure(text="Age: --", text_color=Colors.TEXT_PRIMARY)
            self._computed_age = None

    def _authenticate_login(self):
        self.error_label.configure(text="", text_color=Colors.ERROR)
        
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            self.error_label.configure(text="Please enter your email and password.")
            return

        success, msg = login_user(email, password, remember_me=self.remember_var.get())
        
        if success:
            self._trigger_success()
        else:
            self.error_label.configure(text=msg)

    def _authenticate_signup(self):
        self.error_label.configure(text="", text_color=Colors.ERROR)
        
        name = self.name_entry.get().strip()
        username = getattr(self, "username_entry", None)
        username = username.get().strip() if username else ""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        dob = getattr(self, "dob_entry", None)
        dob = dob.get().strip() if dob else ""
        age = getattr(self, "_computed_age", None)

        if not name or not username or not email or not password or not dob:
            self.error_label.configure(text="Please fill out all fields.")
            return
        if age is None:
            self.error_label.configure(text="Please enter a valid Date of Birth (YYYY-MM-DD).")
            return
        if len(password) < 4:
            self.error_label.configure(text="Password must be at least 4 characters.")
            return
            
        success, msg = signup_user(name, email, username, password, dob, age)
        
        if success:
            # Auto-login after signup
            login_success, _ = login_user(email, password, remember_me=True)
            if login_success:
                self._trigger_success()
            else:
                self.error_label.configure(text="Account created, but failed to log in.")
        else:
            self.error_label.configure(text=msg)

    def _build_graphic(self):
        """Draw the abstract floating antigravity network graphic."""
        from utils.animations import resolve_color
        
        canvas = ctk.CTkCanvas(
            self.right_pane, bg=resolve_color(Colors.CARD_BG), highlightthickness=0,
            width=460, height=Dims.AUTH_CARD_H - 40
        )
        canvas.pack(fill="both", expand=True)

        nodes = [
            (220, 260, 25, resolve_color(Colors.ACCENT_PRIMARY)),     # Core node
            (120, 200, 15, resolve_color(Colors.ACCENT_PRIMARY)),
            (320, 220, 15, resolve_color(Colors.ACCENT_HOVER)),
            (150, 350, 18, resolve_color(Colors.ACCENT_PRIMARY)),
            (300, 340, 12, resolve_color(Colors.ACCENT_PRIMARY)),
            (200, 120, 12, resolve_color(Colors.ACCENT_HOVER)),
            (280, 150, 8, resolve_color(Colors.ACCENT_PRIMARY)),
            (100, 280, 10, resolve_color(Colors.ACCENT_PRIMARY))
        ]

        lines = [
            (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
            (1, 5), (1, 7), (2, 6), (2, 4), (3, 7), (3, 4)
        ]

        for n1, n2 in lines:
            x1, y1, _, _ = nodes[n1]
            x2, y2, _, _ = nodes[n2]
            canvas.create_line(x1, y1, x2, y2, fill=resolve_color(Colors.BORDER_HOVER), width=2)

        for x, y, r, color in nodes:
            canvas.create_oval(x-r*1.5, y-r*1.5, x+r*1.5, y+r*1.5, fill="", outline=resolve_color(Colors.BORDER_HOVER), width=1)
            canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=resolve_color(Colors.TEXT_PRIMARY), width=1)
            
        canvas.create_rectangle(140, 160, 160, 175, fill=resolve_color(Colors.BORDER_ACTIVE), outline=resolve_color(Colors.ACCENT_PRIMARY))
        canvas.create_polygon(340, 280, 355, 295, 340, 310, fill=resolve_color(Colors.ACCENT_PRIMARY), outline="")
