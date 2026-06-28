import threading
import customtkinter as ctk
from theme import Colors, Fonts
from ui.glass_card import GlassCard
from authentication.session import current_session
from services.history_service import get_recent_activities, clear_history
from utils.ui_helpers import destroy_tracked


class HistoryView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._timeline_widgets = []

        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=Colors.CARD_FLOATING,
            scrollbar_button_hover_color=Colors.CARD_HOVER,
        )
        self.scroll.pack(fill="both", expand=True)

        self._build_header()
        self._build_content()

    def on_show(self):
        threading.Thread(target=self._load_timeline_async, daemon=True).start()

    def _build_header(self):
        header = ctk.CTkFrame(self.scroll, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="🕐 History",
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY,
            anchor="w", fg_color="transparent"
        ).pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(
            header, text="Clear All History",
            fg_color=Colors.ERROR, hover_color="#dc2626",
            command=self._clear_history
        ).pack(side="right")

    def _build_content(self):
        self.card = GlassCard(self.scroll, title="Recent Activity Timeline")
        self.card.pack(fill="x", padx=4, pady=10)
        
        self.timeline_frame = ctk.CTkFrame(self.card.content, fg_color="transparent")
        self.timeline_frame.pack(fill="both", expand=True)
        self._load_timeline()

    def _load_timeline_async(self):
        activities = get_recent_activities(current_session.user_id) if current_session.is_logged_in() else []
        self.after(0, lambda: self._render_timeline(activities))

    def _load_timeline(self):
        activities = get_recent_activities(current_session.user_id) if current_session.is_logged_in() else []
        self._render_timeline(activities)

    def _render_timeline(self, activities):
        destroy_tracked(self._timeline_widgets)
        
        if not activities:
            lbl = ctk.CTkLabel(self.timeline_frame, text="No recent activity found.", font=Fonts.BODY, text_color=Colors.TEXT_MUTED)
            lbl.pack(pady=20)
            self._timeline_widgets.append(lbl)
            return

        for act in activities:
            row = ctk.CTkFrame(self.timeline_frame, fg_color=Colors.CARD_FLOATING, corner_radius=10)
            row.pack(fill="x", pady=4)
            self._timeline_widgets.append(row)
            
            ctk.CTkLabel(row, text=act['timestamp'], font=Fonts.SMALL, text_color=Colors.TEXT_MUTED, width=150, anchor="w").pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(row, text=act['activity_type'], font=Fonts.BODY_BOLD, text_color=Colors.ACCENT_PRIMARY, width=120, anchor="w").pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(row, text=act['description'], font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=10)

    def _clear_history(self):
        if current_session.is_logged_in():
            clear_history(current_session.user_id)
            self._load_timeline()
