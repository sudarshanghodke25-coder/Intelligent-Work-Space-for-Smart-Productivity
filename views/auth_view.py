"""
AuthView — Login / Signup authentication frame with glassmorphism styling.
"""
import customtkinter as ctk
import math
from theme import Colors, Fonts, Dims
from services.auth_service import login_user, signup_user, check_active_session, clear_saved_profile

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
        
        if auto_login:
            # Token completely valid, skip UI
            self.after(10, self._trigger_success)
            return

        if has_profile:
            self._mode = "quick_login"
        else:
            self._mode = "login"

        # Center the auth card
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Outer glass card - Dual Pane layout (wider)
        self.card = ctk.CTkFrame(
            self,
            fg_color=Colors.GLASS_FILL,
            corner_radius=20,
            border_width=1,
            border_color=Colors.GLASS_BORDER,
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
            font=("Segoe UI", 36, "bold"), text_color=Colors.ACCENT_GLOW,
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

        if self._mode == "quick_login":
            self.subtitle.configure(text="Welcome back")
            
            # Avatar circle
            avatar_frame = ctk.CTkFrame(self.form_frame, width=80, height=80, corner_radius=40, fg_color=Colors.ACCENT_PRIMARY)
            avatar_frame.pack(pady=(10, 10))
            avatar_frame.pack_propagate(False)
            
            full_name = self._saved_profile_data.get("full_name", "User")
            initials = full_name[0].upper() if full_name else "U"
            if " " in full_name:
                initials += full_name.split()[-1][0].upper()
                
            ctk.CTkLabel(avatar_frame, text=initials, font=("Segoe UI", 32, "bold"), text_color=Colors.TEXT_PRIMARY, fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")
            
            # Continue text
            ctk.CTkLabel(self.form_frame, text=f"Continue as {full_name}", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(pady=(0, 20))
            
            # Password field only
            self._create_input_field("Password", "••••••••", "password_entry", show="•")
            
            # Quick Login Button
            btn_text = "Quick Login"
            auth_command = self._authenticate_quick
            
        elif self._mode == "signup":
            self.subtitle.configure(text="Create your account")
            self._create_input_field("Username", "E.g., johndoe", "username_entry")
            self._create_input_field("Email", "E.g., johndoe@aurex.com", "email_entry")
            self._create_input_field("Password", "••••••••", "password_entry", show="•")
            self._create_input_field("Confirm Password", "••••••••", "confirm_entry", show="•")
            btn_text = "Create Account"
            auth_command = self._authenticate
        else:
            self.subtitle.configure(text="Sign in to your workspace")
            self._create_input_field("Email", "E.g., johndoe@aurex.com", "email_entry")
            self._create_input_field("Password", "••••••••", "password_entry", show="•")
            
            # Remember me checkbox
            rem_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            rem_frame.pack(fill="x", pady=(0, 12))
            ctk.CTkCheckBox(
                rem_frame, text="Remember me", font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY,
                variable=self.remember_var, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
                border_color=Colors.GLASS_BORDER_BRIGHT
            ).pack(side="left")
            
            btn_text = "Login"
            auth_command = self._authenticate

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

        # Toggle links
        if self._mode == "quick_login":
            toggle_text = "Switch Account"
            cmd = self._switch_account
        else:
            toggle_text = "Already have an account?" if self._mode == "signup" else "Create an account"
            cmd = self._toggle_mode
            
        toggle_btn = ctk.CTkLabel(
            self.form_frame, text=toggle_text,
            font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY,
            cursor="hand2", fg_color="transparent"
        )
        toggle_btn.pack(anchor="w")
        toggle_btn.bind("<Button-1>", cmd)
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
            fg_color=Colors.ENTRY_BG,
            border_width=1, border_color=Colors.ENTRY_BORDER,
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

    def _authenticate_quick(self):
        self.error_label.configure(text="", text_color=Colors.ERROR)
        password = self.password_entry.get().strip()
        email = self._saved_profile_data.get("email")
        
        if len(password) < 4:
            self.error_label.configure(text="Password must be at least 4 characters.")
            return
            
        success, msg = login_user(email, password, remember_me=True)
        if success:
            self._trigger_success()
        else:
            self.error_label.configure(text=msg)

    def _authenticate(self):
        """Process the authentication logic based on mode."""
        self.error_label.configure(text="", text_color=Colors.ERROR)
        
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email:
            self.error_label.configure(text="Please enter your email.")
            return
        if len(password) < 4:
            self.error_label.configure(text="Password must be at least 4 characters.")
            return

        if self._mode == "signup":
            username = self.username_entry.get().strip()
            confirm = self.confirm_entry.get().strip()
            if not username:
                self.error_label.configure(text="Please enter a username.")
                return
            if password != confirm:
                self.error_label.configure(text="Passwords do not match.")
                return
            
            # Sign up via auth service
            success, msg = signup_user("User", email, username, password)
            if success:
                self._mode = "login"
                self._populate_form()
                self.error_label.configure(text="Account created. Please log in.", text_color=Colors.SUCCESS)
            else:
                self.error_label.configure(text=msg)
                
        else:
            rem = self.remember_var.get()
            success, msg = login_user(email, password, remember_me=rem)
            if success:
                self._trigger_success()
            else:
                self.error_label.configure(text=msg)

    def _build_graphic(self):
        """Draw the abstract floating antigravity network graphic."""
        canvas = ctk.CTkCanvas(
            self.right_pane, bg=Colors.GLASS_FILL, highlightthickness=0,
            width=460, height=Dims.AUTH_CARD_H - 40
        )
        canvas.pack(fill="both", expand=True)

        nodes = [
            (220, 260, 25, Colors.ACCENT_GLOW),     # Core node
            (120, 200, 15, Colors.ACCENT_PRIMARY),
            (320, 220, 15, Colors.ACCENT_HOVER),
            (150, 350, 18, Colors.ACCENT_PRIMARY),
            (300, 340, 12, Colors.ACCENT_GLOW),
            (200, 120, 12, Colors.ACCENT_HOVER),
            (280, 150, 8, Colors.ACCENT_PRIMARY),
            (100, 280, 10, Colors.ACCENT_GLOW)
        ]

        lines = [
            (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
            (1, 5), (1, 7), (2, 6), (2, 4), (3, 7), (3, 4)
        ]

        for n1, n2 in lines:
            x1, y1, _, _ = nodes[n1]
            x2, y2, _, _ = nodes[n2]
            canvas.create_line(x1, y1, x2, y2, fill=Colors.GLASS_BORDER_BRIGHT, width=2)

        for x, y, r, color in nodes:
            canvas.create_oval(x-r*1.5, y-r*1.5, x+r*1.5, y+r*1.5, fill="", outline=Colors.GLASS_BORDER_BRIGHT, width=1)
            canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=Colors.TEXT_PRIMARY, width=1)
            
        canvas.create_rectangle(140, 160, 160, 175, fill=Colors.ACCENT_MUTED, outline=Colors.ACCENT_GLOW)
        canvas.create_polygon(340, 280, 355, 295, 340, 310, fill=Colors.ACCENT_PRIMARY, outline="")
