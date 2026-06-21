import customtkinter as ctk
import threading
from theme import Colors, Fonts, Dims
from services.event_bus import bus
from services.ai_service import ai_service

class AssistantView(ctk.CTkFrame):
    """Conversational AI portal powered by Groq."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)
        
        self.conversation_history = [
            {"role": "system", "content": "You are Aurex AI, a highly intelligent and efficient AI assistant built into the Aurex Workspace platform. You respond concisely and professionally."}
        ]
        
        self.loading_bubble = None
        
        self._build_header()
        self._build_chat_area()
        self._build_input_area()
        
        bus.subscribe("AI_RESPONSE_RECEIVED", self._on_ai_response)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=4, pady=(8, 0))
        ctk.CTkLabel(
            header, text="🤖 Aurex AI", 
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(side="left", fill="x")

    def _build_chat_area(self):
        self.chat_canvas = ctk.CTkScrollableFrame(
            self, fg_color=Colors.GLASS_FILL,
            corner_radius=15, border_width=1, border_color=Colors.GLASS_BORDER,
            scrollbar_button_color=Colors.GLASS_FILL_LIGHT,
            scrollbar_button_hover_color=Colors.GLASS_FILL_HOVER
        )
        self.chat_canvas.pack(fill="both", expand=True, padx=4, pady=(10, 10))
        
        self._add_bubble("Greetings. I am Aurex AI. How can I assist you in your workspace today?", "assistant")

    def _build_input_area(self):
        input_frame = ctk.CTkFrame(self, fg_color="transparent", height=Dims.ENTRY_HEIGHT + 10)
        input_frame.pack(fill="x", padx=4, pady=(0, 10))
        
        self.entry = ctk.CTkEntry(
            input_frame, placeholder_text="Transmit message to Aurex AI...",
            font=Fonts.ENTRY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.ENTRY_BG, border_width=1, border_color=Colors.ENTRY_BORDER,
            height=Dims.ENTRY_HEIGHT
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self._send_message())
        
        self.send_btn = ctk.CTkButton(
            input_frame, text="Send", font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
            width=80, height=Dims.ENTRY_HEIGHT,
            command=self._send_message
        )
        self.send_btn.pack(side="right")

    def _add_bubble(self, text, role):
        """Adds a visual text bubble to the chat canvas."""
        row = ctk.CTkFrame(self.chat_canvas, fg_color="transparent")
        row.pack(fill="x", pady=8, padx=10)
        
        if role == "user":
            bg_color = Colors.ACCENT_PRIMARY
            text_color = Colors.TEXT_PRIMARY
            side = "right"
            justify = "right"
        else:
            bg_color = Colors.GLASS_FILL_LIGHT
            text_color = Colors.TEXT_PRIMARY
            side = "left"
            justify = "left"
            
        bubble = ctk.CTkFrame(row, fg_color=bg_color, corner_radius=15)
        bubble.pack(side=side)
        
        lbl = ctk.CTkLabel(
            bubble, text=text, font=Fonts.BODY, text_color=text_color,
            justify=justify, wraplength=650
        )
        lbl.pack(padx=16, pady=10)
        
        # Auto-scroll down
        self.after(50, lambda: self.chat_canvas._parent_canvas.yview_moveto(1.0))
        return bubble

    def _send_message(self):
        msg = self.entry.get().strip()
        if not msg: return
            
        self.entry.delete(0, 'end')
        self._add_bubble(msg, "user")
        
        self.conversation_history.append({"role": "user", "content": msg})
        
        # Truncate context to last 10 messages to save tokens while keeping context
        if len(self.conversation_history) > 11:
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-10:]
            
        self.loading_bubble = self._add_bubble("Aurex AI is analyzing transmission...", "assistant")
        self.send_btn.configure(state="disabled")
        
        history_copy = list(self.conversation_history)
        threading.Thread(target=ai_service.generate_response, args=(history_copy,), daemon=True).start()

    def _on_ai_response(self, data):
        # EventBus guarantees this is marshalled onto the main thread
        if self.loading_bubble:
            self.loading_bubble.master.destroy()
            self.loading_bubble = None
            
        response_text = data.get("text", "Error rendering response.")
        
        self.conversation_history.append({"role": "assistant", "content": response_text})
        self._add_bubble(response_text, "assistant")
        
        self.send_btn.configure(state="normal")
