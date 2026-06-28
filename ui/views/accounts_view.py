import os
import uuid
import shutil
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from authentication.session import current_session
from services.auth_service import logout_user, update_user_profile
from services.event_bus import bus
from tkinter import messagebox

class AccountsView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.CARD_FLOATING,
            scrollbar_button_hover_color=Colors.CARD_HOVER,
        )
        self.scroll.pack(fill="both", expand=True)
        
        self.is_edit_mode = False
        self.new_profile_image = None
        self.entries = {}
        self.content_frame = None

        self._build_header()
        self._build_content()
        
        bus.subscribe("PROFILE_UPDATED", self._on_profile_updated)

    def _on_profile_updated(self, _):
        if not self.is_edit_mode:
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
        if self.content_frame:
            self.content_frame.destroy()
            
        self.content_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)
        
        # Account Section
        acc_card = GlassCard(self.content_frame, title="Account Information")
        acc_card.pack(fill="x", padx=4, pady=10)
        
        # Avatar Section
        avatar_frame = ctk.CTkFrame(acc_card.content, fg_color="transparent")
        avatar_frame.pack(fill="x", pady=(0, 20))
        
        # Load Avatar Image
        avatar_path = current_session.profile_image
        if self.is_edit_mode and self.new_profile_image:
            avatar_path = self.new_profile_image
            
        img_size = 80
        avatar_img = None
        if avatar_path and os.path.exists(avatar_path):
            try:
                pil_img = Image.open(avatar_path)
                # Crop to square for better avatar look
                size = min(pil_img.size)
                left = (pil_img.size[0] - size) // 2
                top = (pil_img.size[1] - size) // 2
                pil_img = pil_img.crop((left, top, left + size, top + size))
                avatar_img = ctk.CTkImage(pil_img, size=(img_size, img_size))
            except:
                pass
                
        if avatar_img:
            self.avatar_btn = ctk.CTkButton(
                avatar_frame, text="", image=avatar_img, 
                width=img_size, height=img_size,
                fg_color="transparent", hover_color=Colors.CARD_HOVER,
                command=self._upload_avatar if self.is_edit_mode else None,
                state="normal" if self.is_edit_mode else "disabled"
            )
        else:
            initials = "".join([n[0] for n in (current_session.full_name or "User").split() if n])[:2].upper()
            self.avatar_btn = ctk.CTkButton(
                avatar_frame, text=initials, font=("Inter", 24, "bold"),
                width=img_size, height=img_size, corner_radius=img_size//2,
                fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
                command=self._upload_avatar if self.is_edit_mode else None,
                state="normal" if self.is_edit_mode else "disabled"
            )
            
        self.avatar_btn.pack(side="left", padx=(0, 20))
        
        if self.is_edit_mode:
            upload_lbl = ctk.CTkLabel(avatar_frame, text="Click avatar to upload new photo", font=Fonts.BODY_SM, text_color=Colors.TEXT_MUTED)
            upload_lbl.pack(side="left")

        # Info Grid
        info_frame = ctk.CTkFrame(acc_card.content, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 24))
        
        self.entries = {}
        
        fields = [
            ("full_name", "Full Name", current_session.full_name),
            ("username", "Username", current_session.username),
            ("email", "Email Address", current_session.email),
            ("dob", "Date of Birth (YYYY-MM-DD)", current_session.dob or ""),
            ("age", "Age", str(current_session.age) if current_session.age else "")
        ]
        
        for key, label, val in fields:
            ctk.CTkLabel(info_frame, text=label, font=("Inter", 11, "bold"), text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x")
            if self.is_edit_mode:
                entry = ctk.CTkEntry(info_frame, height=36, corner_radius=Dims.BTN_CORNER)
                entry.pack(fill="x", pady=(4, 12))
                entry.insert(0, val if val else "")
                self.entries[key] = entry
            else:
                display_val = f"@{val}" if key == "username" else val
                display_val = display_val if display_val else "--"
                ctk.CTkLabel(info_frame, text=display_val, font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 12))
        
        if not self.is_edit_mode:
            ctk.CTkLabel(info_frame, text="Password", font=("Inter", 11, "bold"), text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x")
            ctk.CTkLabel(info_frame, text="********", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x")
        
        # Action Buttons
        btns_frame = ctk.CTkFrame(acc_card.content, fg_color="transparent")
        btns_frame.pack(fill="x")
        
        if self.is_edit_mode:
            ctk.CTkButton(btns_frame, text="Save Changes", fg_color=Colors.SUCCESS, hover_color=Colors.SUCCESS_HOVER, height=Dims.BTN_HEIGHT, corner_radius=Dims.BTN_CORNER, command=self._save_changes).pack(side="left", padx=(0,10))
            ctk.CTkButton(btns_frame, text="Cancel", fg_color="transparent", border_width=1, border_color=Colors.TEXT_MUTED, text_color=Colors.TEXT_PRIMARY, hover_color=Colors.CARD_HOVER, height=Dims.BTN_HEIGHT, corner_radius=Dims.BTN_CORNER, command=self._toggle_edit).pack(side="left")
        else:
            ctk.CTkButton(btns_frame, text="Update Profile", fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, height=Dims.BTN_HEIGHT, corner_radius=Dims.BTN_CORNER, command=self._toggle_edit).pack(side="left", padx=(0,10))
            logout_btn = ctk.CTkButton(btns_frame, text="Logout", fg_color="transparent", border_width=1, border_color=Colors.ERROR, text_color=Colors.ERROR, hover_color=Colors.ERROR_HOVER, height=Dims.BTN_HEIGHT, corner_radius=Dims.BTN_CORNER, command=self._on_logout)
            logout_btn.pack(side="left")

    def _toggle_edit(self):
        self.is_edit_mode = not self.is_edit_mode
        self.new_profile_image = None
        self._build_content()
        
    def _upload_avatar(self):
        filepath = filedialog.askopenfilename(
            title="Select Profile Picture",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if filepath:
            try:
                # Copy file to assets/profiles
                assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "profiles")
                os.makedirs(assets_dir, exist_ok=True)
                
                ext = os.path.splitext(filepath)[1]
                new_filename = f"{current_session.user_id}_{uuid.uuid4().hex[:8]}{ext}"
                dest_path = os.path.join(assets_dir, new_filename)
                
                shutil.copy2(filepath, dest_path)
                self.new_profile_image = dest_path
                self._build_content()
            except Exception as e:
                messagebox.showerror("Upload Error", f"Failed to upload image: {str(e)}")

    def _save_changes(self):
        full_name = self.entries["full_name"].get().strip()
        username = self.entries["username"].get().strip()
        email = self.entries["email"].get().strip()
        dob = self.entries["dob"].get().strip()
        age_str = self.entries["age"].get().strip()
        
        if not full_name or not username or not email:
            messagebox.showerror("Update Error", "Name, Username, and Email are required.")
            return
            
        age = None
        if age_str:
            try:
                age = int(age_str)
            except:
                messagebox.showerror("Update Error", "Age must be a number.")
                return
                
        final_image = self.new_profile_image if self.new_profile_image else current_session.profile_image
        
        success, msg = update_user_profile(full_name, username, email, dob, age, final_image)
        if success:
            messagebox.showinfo("Profile Updated", "Profile updated successfully!")
            self.is_edit_mode = False
            self.new_profile_image = None
            self._build_content()
        else:
            messagebox.showerror("Update Error", msg)

    def _on_logout(self):
        """Logs the user out and triggers the application transition to AuthView."""
        logout_user()
        bus.publish("LOGOUT")
