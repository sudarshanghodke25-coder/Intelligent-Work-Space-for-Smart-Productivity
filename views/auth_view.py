"""
Aurex AuthView — Modern Dual-Pane Login & Registration Interface.
Features real-time validation, dynamic responsiveness, quick auto-login,
password reveal toggles, and premium glassmorphic styling.
"""
import re
from datetime import datetime
import customtkinter as ctk
from theme import Colors, Fonts, Dims
from services.auth_service import (
    login_user,
    signup_user,
    check_active_session,
    clear_saved_profile
)


class AuthView(ctk.CTkFrame):
    """
    Modern authentication screen with seamless Login / Signup / Quick-Resume modes.
    Centered glassmorphic card over the dynamic cosmic nebula background.
    """

    def __init__(self, parent, on_auth_success=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._on_auth_success = on_auth_success
        has_profile, auto_login, profile_data = check_active_session()
        self._saved_profile_data = profile_data or {}
        self._auto_login_valid = auto_login
        
        # If active session exists, start in quick-resume mode; otherwise login
        if self._auto_login_valid and self._saved_profile_data.get("full_name"):
            self._mode = "resume"
        else:
            self._mode = "login"

        self._show_password = False
        self._computed_age = None

        # Center the auth card
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Dual Pane Card
        self.card = ctk.CTkFrame(
            self,
            fg_color=Colors.CARD_BG,
            corner_radius=22,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            width=980,
            height=540,
        )
        self.card.grid(row=0, column=0, padx=20, pady=20)
        self.card.grid_propagate(False)

        # Left pane (Form Container)
        self.left_pane = ctk.CTkFrame(self.card, fg_color="transparent", width=490)
        self.left_pane.pack(side="left", fill="both", expand=True, padx=(36, 20), pady=28)

        # Right pane (Cosmic Graphic)
        self.right_pane = ctk.CTkFrame(self.card, fg_color="transparent", width=470)
        self.right_pane.pack(side="right", fill="both", expand=True, padx=(0, 24), pady=24)

        self._build_header()
        self._build_form()
        self._build_graphic()

    def _trigger_success(self):
        if callable(self._on_auth_success):
            self._on_auth_success()

    def _build_header(self):
        """Build the AUREX brand header."""
        self.header_frame = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 16))

        brand_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        brand_row.pack(anchor="w")

        ctk.CTkLabel(
            brand_row, text="◆",
            font=("Segoe UI", 28, "bold"), text_color=Colors.ACCENT_PRIMARY,
            fg_color="transparent"
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            brand_row, text="AUREX",
            font=("Segoe UI", 24, "bold"), text_color=Colors.TEXT_PRIMARY,
            fg_color="transparent"
        ).pack(side="left")

        self.subtitle = ctk.CTkLabel(
            self.header_frame, text="Cosmic Workspace & Productivity Studio",
            font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY,
            fg_color="transparent"
        )
        self.subtitle.pack(anchor="w", pady=(2, 0))

    def _build_form(self):
        """Container for form fields."""
        self.form_container = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        self.form_container.pack(fill="both", expand=True)
        self._populate_form()

    def _populate_form(self):
        """Populate form based on current mode."""
        for widget in self.form_container.winfo_children():
            widget.destroy()

        self.remember_var = ctk.BooleanVar(value=True)

        if self._mode == "resume":
            self._render_resume_view()
        elif self._mode == "signup":
            self._render_signup_view()
        else:
            self._render_login_view()

    def _render_resume_view(self):
        """Render quick unlock screen for returning users with active session."""
        self.card.configure(height=520)
        self.subtitle.configure(text="Welcome back to your workspace")

        resume_box = ctk.CTkFrame(
            self.form_container,
            fg_color=Colors.CARD_FLOATING,
            corner_radius=16,
            border_width=1,
            border_color=Colors.BORDER_HOVER
        )
        resume_box.pack(fill="x", pady=(12, 20), padx=4)

        user_name = self._saved_profile_data.get("full_name", "Explorer")
        user_email = self._saved_profile_data.get("email", "")

        ctk.CTkLabel(
            resume_box, text=f"👤  {user_name}",
            font=Fonts.HEADING, text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            resume_box, text=user_email,
            font=Fonts.BODY, text_color=Colors.TEXT_MUTED,
            anchor="w"
        ).pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(
            self.form_container,
            text="Launch Workspace →",
            font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Dims.BTN_CORNER,
            height=Dims.BTN_HEIGHT,
            command=self._trigger_success
        ).pack(fill="x", pady=(8, 12))

        switch_btn = ctk.CTkLabel(
            self.form_container,
            text="Switch account or sign in with password",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY,
            cursor="hand2",
            fg_color="transparent"
        )
        switch_btn.pack(anchor="w", pady=(4, 0))
        switch_btn.bind("<Button-1>", lambda e: self._switch_to_login())
        switch_btn.bind("<Enter>", lambda e: switch_btn.configure(text_color=Colors.TEXT_PRIMARY))
        switch_btn.bind("<Leave>", lambda e: switch_btn.configure(text_color=Colors.TEXT_SECONDARY))

    def _render_login_view(self):
        """Render the primary login form."""
        self.card.configure(height=540)
        self.subtitle.configure(text="Sign in to your intelligent workspace")

        # Email
        self._create_input_field("Email Address", "name@domain.com", "email_entry")
        if self._saved_profile_data.get("email"):
            self.email_entry.insert(0, self._saved_profile_data["email"])

        # Password with show/hide toggle
        self._create_password_field("Password", "password_entry")
        if self._saved_profile_data.get("password"):
            self.password_entry.insert(0, self._saved_profile_data["password"])

        # Options Row (Remember Me)
        opts_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        opts_frame.pack(fill="x", pady=(2, 10))

        ctk.CTkCheckBox(
            opts_frame,
            text="Keep me signed in",
            font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY,
            variable=self.remember_var,
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            border_color=Colors.BORDER_HOVER,
            corner_radius=4,
            height=20,
            width=20
        ).pack(side="left")

        # Feedback Error Label
        self.error_label = ctk.CTkLabel(
            self.form_container, text="",
            font=Fonts.SMALL, text_color=Colors.ERROR,
            fg_color="transparent", anchor="w"
        )
        self.error_label.pack(fill="x", pady=(0, 6))

        # Sign In Button
        sign_in_btn = ctk.CTkButton(
            self.form_container,
            text="Sign In",
            font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Dims.BTN_CORNER,
            height=Dims.BTN_HEIGHT,
            command=self._authenticate_login
        )
        sign_in_btn.pack(fill="x", pady=(6, 12))

        # Toggle to Signup
        toggle_row = ctk.CTkFrame(self.form_container, fg_color="transparent")
        toggle_row.pack(anchor="w")

        ctk.CTkLabel(
            toggle_row, text="New to Aurex? ",
            font=Fonts.SMALL, text_color=Colors.TEXT_MUTED,
            fg_color="transparent"
        ).pack(side="left")

        toggle_lbl = ctk.CTkLabel(
            toggle_row, text="Create an account",
            font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_PRIMARY,
            cursor="hand2", fg_color="transparent"
        )
        toggle_lbl.pack(side="left")
        toggle_lbl.bind("<Button-1>", lambda e: self._toggle_mode("signup"))
        toggle_lbl.bind("<Enter>", lambda e: toggle_lbl.configure(text_color=Colors.ACCENT_HOVER))
        toggle_lbl.bind("<Leave>", lambda e: toggle_lbl.configure(text_color=Colors.ACCENT_PRIMARY))

        # Bind Enter key
        if hasattr(self, "email_entry"):
            self.email_entry.bind("<Return>", lambda e: self._authenticate_login())
        if hasattr(self, "password_entry"):
            self.password_entry.bind("<Return>", lambda e: self._authenticate_login())

    def _render_signup_view(self):
        """Render the registration form with dynamic scroll safety."""
        self.card.configure(height=650)
        self.subtitle.configure(text="Create your new workspace account")

        # Scrollable container so signup fields fit comfortably
        scroll_form = ctk.CTkScrollableFrame(
            self.form_container,
            fg_color="transparent",
            scrollbar_button_color=Colors.CARD_FLOATING,
            scrollbar_button_hover_color=Colors.CARD_HOVER,
            height=460
        )
        scroll_form.pack(fill="both", expand=True)

        self._create_input_field("Full Name", "E.g., Alex Mercer", "name_entry", parent=scroll_form)
        self._create_input_field("Username", "E.g., alex_mercer", "username_entry", parent=scroll_form)
        self._create_input_field("Email Address", "alex@example.com", "email_entry", parent=scroll_form)

        # Date of birth with age indicator
        dob_label_frame = ctk.CTkFrame(scroll_form, fg_color="transparent")
        dob_label_frame.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            dob_label_frame, text="Date of Birth",
            font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(side="left")

        self.age_badge = ctk.CTkLabel(
            dob_label_frame, text="Age: --",
            font=Fonts.SMALL, text_color=Colors.TEXT_MUTED,
            anchor="e", fg_color="transparent"
        )
        self.age_badge.pack(side="right")

        self.dob_entry = ctk.CTkEntry(
            scroll_form,
            placeholder_text="YYYY-MM-DD",
            placeholder_text_color=Colors.TEXT_DISABLED,
            font=Fonts.ENTRY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.INPUT_BG,
            border_width=1, border_color=Colors.INPUT_BORDER,
            corner_radius=Dims.ENTRY_CORNER,
            height=Dims.ENTRY_HEIGHT
        )
        self.dob_entry.pack(fill="x", pady=(0, 10))
        self.dob_entry.bind("<KeyRelease>", self._calculate_age)

        # Password fields
        self._create_password_field("Create Password", "password_entry", parent=scroll_form)
        self._create_password_field("Confirm Password", "confirm_password_entry", parent=scroll_form)

        # Feedback Error Label
        self.error_label = ctk.CTkLabel(
            scroll_form, text="",
            font=Fonts.SMALL, text_color=Colors.ERROR,
            fg_color="transparent", anchor="w"
        )
        self.error_label.pack(fill="x", pady=(0, 6))

        # Submit Button
        signup_btn = ctk.CTkButton(
            scroll_form,
            text="Create Account",
            font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY,
            hover_color=Colors.ACCENT_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=Dims.BTN_CORNER,
            height=Dims.BTN_HEIGHT,
            command=self._authenticate_signup
        )
        signup_btn.pack(fill="x", pady=(6, 12))

        # Toggle to Login
        toggle_row = ctk.CTkFrame(scroll_form, fg_color="transparent")
        toggle_row.pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(
            toggle_row, text="Already have an account? ",
            font=Fonts.SMALL, text_color=Colors.TEXT_MUTED,
            fg_color="transparent"
        ).pack(side="left")

        toggle_lbl = ctk.CTkLabel(
            toggle_row, text="Sign in",
            font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_PRIMARY,
            cursor="hand2", fg_color="transparent"
        )
        toggle_lbl.pack(side="left")
        toggle_lbl.bind("<Button-1>", lambda e: self._toggle_mode("login"))
        toggle_lbl.bind("<Enter>", lambda e: toggle_lbl.configure(text_color=Colors.ACCENT_HOVER))
        toggle_lbl.bind("<Leave>", lambda e: toggle_lbl.configure(text_color=Colors.ACCENT_PRIMARY))

        # Bind Enter key
        for entry_name in ["name_entry", "username_entry", "email_entry", "dob_entry", "password_entry", "confirm_password_entry"]:
            entry = getattr(self, entry_name, None)
            if entry:
                entry.bind("<Return>", lambda e: self._authenticate_signup())

    def _create_input_field(self, label, placeholder, attr_name, parent=None):
        """Helper to create sleek text entry fields."""
        p = parent or self.form_container
        ctk.CTkLabel(
            p, text=label,
            font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(fill="x", pady=(0, 4))

        entry = ctk.CTkEntry(
            p,
            placeholder_text=placeholder,
            placeholder_text_color=Colors.TEXT_DISABLED,
            font=Fonts.ENTRY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.INPUT_BG,
            border_width=1, border_color=Colors.INPUT_BORDER,
            corner_radius=Dims.ENTRY_CORNER,
            height=Dims.ENTRY_HEIGHT
        )
        entry.pack(fill="x", pady=(0, 10))
        entry.bind("<Key>", lambda e: self._clear_error())
        setattr(self, attr_name, entry)
        return entry

    def _create_password_field(self, label, attr_name, parent=None):
        """Helper to create secure password field with visibility toggle."""
        p = parent or self.form_container
        ctk.CTkLabel(
            p, text=label,
            font=Fonts.SMALL_BOLD, text_color=Colors.TEXT_SECONDARY,
            anchor="w", fg_color="transparent"
        ).pack(fill="x", pady=(0, 4))

        pw_row = ctk.CTkFrame(p, fg_color="transparent")
        pw_row.pack(fill="x", pady=(0, 10))

        entry = ctk.CTkEntry(
            pw_row,
            placeholder_text="••••••••",
            placeholder_text_color=Colors.TEXT_DISABLED,
            font=Fonts.ENTRY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.INPUT_BG,
            border_width=1, border_color=Colors.INPUT_BORDER,
            corner_radius=Dims.ENTRY_CORNER,
            height=Dims.ENTRY_HEIGHT,
            show="•"
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        entry.bind("<Key>", lambda e: self._clear_error())
        setattr(self, attr_name, entry)

        toggle_btn = ctk.CTkButton(
            pw_row,
            text="👁",
            width=38,
            height=Dims.ENTRY_HEIGHT,
            fg_color=Colors.INPUT_BG,
            hover_color=Colors.CARD_HOVER,
            text_color=Colors.TEXT_SECONDARY,
            border_width=1,
            border_color=Colors.INPUT_BORDER,
            corner_radius=Dims.ENTRY_CORNER,
            command=lambda: self._toggle_password_visibility(entry, toggle_btn)
        )
        toggle_btn.pack(side="right")
        return entry

    def _toggle_password_visibility(self, entry, btn):
        """Toggle mask character for password entry."""
        if entry.cget("show") == "•":
            entry.configure(show="")
            btn.configure(text="🔒")
        else:
            entry.configure(show="•")
            btn.configure(text="👁")

    def _clear_error(self):
        if hasattr(self, "error_label") and self.error_label.winfo_exists():
            self.error_label.configure(text="")

    def _switch_to_login(self):
        """Clear session token lock and present standard login form."""
        self._mode = "login"
        self._populate_form()

    def _toggle_mode(self, mode):
        """Switch between login and signup modes."""
        self._mode = mode
        self._populate_form()

    def _calculate_age(self, event=None):
        """Calculate and display user age in real-time as DOB is typed."""
        if not hasattr(self, "dob_entry") or not hasattr(self, "age_badge"):
            return
        dob_text = self.dob_entry.get().strip()
        if len(dob_text) == 10 and dob_text.count("-") == 2:
            try:
                dob_date = datetime.strptime(dob_text, "%Y-%m-%d")
                today = datetime.now()
                age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                if 5 <= age <= 120:
                    self.age_badge.configure(text=f"Age: {age} yrs", text_color=Colors.SUCCESS)
                    self._computed_age = age
                else:
                    self.age_badge.configure(text="Age: Invalid", text_color=Colors.ERROR)
                    self._computed_age = None
            except ValueError:
                self.age_badge.configure(text="Format: YYYY-MM-DD", text_color=Colors.ERROR)
                self._computed_age = None
        else:
            self.age_badge.configure(text="Age: --", text_color=Colors.TEXT_MUTED)
            self._computed_age = None

    def _authenticate_login(self):
        """Validate and execute login."""
        self._clear_error()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            self.error_label.configure(text="Please enter both email and password.")
            return

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            self.error_label.configure(text="Please enter a valid email address.")
            return

        success, msg = login_user(email, password, remember_me=self.remember_var.get())
        if success:
            self._trigger_success()
        else:
            self.error_label.configure(text=msg)

    def _authenticate_signup(self):
        """Validate and execute registration."""
        self._clear_error()
        name = getattr(self, "name_entry", None)
        name = name.get().strip() if name else ""

        username = getattr(self, "username_entry", None)
        username = username.get().strip() if username else ""

        email = getattr(self, "email_entry", None)
        email = email.get().strip() if email else ""

        dob = getattr(self, "dob_entry", None)
        dob = dob.get().strip() if dob else ""
        age = self._computed_age

        password = getattr(self, "password_entry", None)
        password = password.get().strip() if password else ""

        confirm_pw = getattr(self, "confirm_password_entry", None)
        confirm_pw = confirm_pw.get().strip() if confirm_pw else ""

        if not name or not username or not email or not dob or not password:
            self.error_label.configure(text="Please fill in all required fields.")
            return

        if len(name) < 2:
            self.error_label.configure(text="Full name must be at least 2 characters.")
            return

        if not re.match(r"^[A-Za-z0-9_]{3,20}$", username):
            self.error_label.configure(text="Username must be 3-20 letters, numbers, or underscores.")
            return

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            self.error_label.configure(text="Please enter a valid email address.")
            return

        if age is None:
            self.error_label.configure(text="Please provide a valid birthdate (YYYY-MM-DD).")
            return

        if len(password) < 4:
            self.error_label.configure(text="Password must be at least 4 characters.")
            return

        if password != confirm_pw:
            self.error_label.configure(text="Passwords do not match.")
            return

        success, msg = signup_user(name, email, username, password, dob, age)
        if success:
            # Automatically sign in on successful registration
            login_success, _ = login_user(email, password, remember_me=True)
            if login_success:
                self._trigger_success()
            else:
                self._mode = "login"
                self._populate_form()
                self.error_label.configure(text="Account created! Please log in.", text_color=Colors.SUCCESS)
        else:
            self.error_label.configure(text=msg)

    def _build_graphic(self):
        """Draw an enhanced cosmic orbital network illustration."""
        from utils.animations import resolve_color

        canvas = ctk.CTkCanvas(
            self.right_pane,
            bg=resolve_color(Colors.CARD_BG),
            highlightthickness=0,
            width=450,
            height=500
        )
        canvas.pack(fill="both", expand=True)

        center_x, center_y = 225, 250

        # Orbital concentric rings
        accent_color = resolve_color(Colors.ACCENT_PRIMARY)
        border_subtle = resolve_color(Colors.BORDER_SUBTLE)
        border_hover = resolve_color(Colors.BORDER_HOVER)
        card_bg = resolve_color(Colors.CARD_FLOATING)
        text_primary = resolve_color(Colors.TEXT_PRIMARY)
        text_muted = resolve_color(Colors.TEXT_MUTED)

        for radius in [170, 125, 80]:
            canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline=border_subtle, width=1, dash=(4, 6)
            )

        # Star / Constellation Nodes (x, y, radius, color)
        nodes = [
            (center_x, center_y, 22, accent_color),
            (center_x - 110, center_y - 70, 10, accent_color),
            (center_x + 115, center_y - 60, 12, resolve_color(Colors.ACCENT_HOVER)),
            (center_x - 90, center_y + 95, 14, accent_color),
            (center_x + 105, center_y + 85, 11, resolve_color(Colors.ACCENT_ACTIVE)),
            (center_x - 30, center_y - 130, 9, accent_color),
            (center_x + 50, center_y + 135, 8, resolve_color(Colors.ACCENT_HOVER)),
            (center_x - 145, center_y + 20, 7, accent_color),
            (center_x + 140, center_y - 10, 8, accent_color),
        ]

        # Constellation links
        connections = [
            (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
            (1, 5), (1, 7), (2, 8), (3, 7), (4, 6), (2, 4)
        ]

        for i, j in connections:
            x1, y1, _, _ = nodes[i]
            x2, y2, _, _ = nodes[j]
            canvas.create_line(x1, y1, x2, y2, fill=border_hover, width=1.5)

        # Render nodes
        for x, y, r, color in nodes:
            # Outer subtle glow aura
            canvas.create_oval(x - r * 1.5, y - r * 1.5, x + r * 1.5, y + r * 1.5, fill="", outline=border_hover, width=1)
            # Solid core
            canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=text_primary, width=1)

        # Center geometric diamond
        d = 10
        canvas.create_polygon(
            center_x, center_y - d,
            center_x + d, center_y,
            center_x, center_y + d,
            center_x - d, center_y,
            fill=text_primary, outline=""
        )

        # Bottom badge
        badge_w, badge_h = 240, 36
        bx1 = center_x - badge_w // 2
        by1 = center_y + 175
        canvas.create_rectangle(
            bx1, by1, bx1 + badge_w, by1 + badge_h,
            fill=card_bg, outline=border_hover, width=1
        )
        canvas.create_text(
            center_x, by1 + badge_h // 2,
            text="AUREX // INTELLIGENT WORKSPACE",
            font=("Segoe UI", 9, "bold"),
            fill=text_muted
        )
