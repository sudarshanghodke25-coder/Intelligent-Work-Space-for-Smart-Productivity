import customtkinter as ctk
from theme import Colors, Fonts
from ui.glass_card import GlassCard

class AssistantView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)

        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        ctk.CTkLabel(header, text="🤖 AI Assistant", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(side="left", fill="x")

        card = GlassCard(self, title="Chat Interface")
        card.pack(fill="both", expand=True, padx=4, pady=10)
        
        chat_area = ctk.CTkScrollableFrame(card.content, fg_color="transparent")
        chat_area.pack(fill="both", expand=True, pady=(0, 10))
        
        ctk.CTkLabel(chat_area, text="Aurex: How can I help you today?", font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY, anchor="w", fg_color=Colors.CARD_FLOATING, corner_radius=8, padx=10, pady=10).pack(fill="x", pady=5)
        
        input_frame = ctk.CTkFrame(card.content, fg_color="transparent", height=50)
        input_frame.pack(fill="x")
        
        ctk.CTkEntry(input_frame, placeholder_text="Type a message...", font=Fonts.BODY, fg_color=Colors.INPUT_BG, border_color=Colors.INPUT_BORDER).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(input_frame, text="Send", width=80, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER).pack(side="right")
