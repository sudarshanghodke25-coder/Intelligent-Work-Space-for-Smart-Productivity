import uuid
import threading
import datetime
import customtkinter as ctk
from theme import Colors, Fonts, Dims
from services.event_bus import bus
from services.ai_service import ai_service
from database.database import get_connection
from authentication.session import current_session
from utils.ui_helpers import destroy_tracked
import speech_recognition as sr

MAX_CHAT_MESSAGES = 50

class AssistantView(ctk.CTkFrame):
    """Cosmic Command Center - AI Workspace"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)
        
        # Session Management
        self.session_id = self._get_or_create_session()
        self.user_id = current_session.user_id or 1
        self.loading_bubble = None
        self._chat_bubbles = []
        self._log_widgets = []
        
        # Layout: 2 Columns (75% Left, 25% Right for chat focus)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._build_left_column()
        self._build_right_column()
        
        bus.subscribe("AI_RESPONSE_RECEIVED", self._on_ai_response)

    def on_show(self):
        threading.Thread(target=self._refresh_conversation_history_async, daemon=True).start()

    def _clear_chat(self):
        destroy_tracked(self._chat_bubbles)

    def _get_or_create_session(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT session_id FROM chat_sessions ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            session_id = row["session_id"]
        else:
            session_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO chat_sessions (session_id) VALUES (?)", (session_id,))
            conn.commit()
        conn.close()
        return session_id

    def _build_left_column(self):
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        left_frame.pack_propagate(False)
        
        # Header (Clean, Premium, No Technical Badges)
        header = ctk.CTkFrame(left_frame, fg_color="transparent", height=60)
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text="AUREX AI COMMAND", font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(header, text="The intelligence layer of your workspace.", font=Fonts.BODY, text_color=Colors.TEXT_SECONDARY).pack(anchor="w", pady=(2, 0))

        # Chat Area - Increased visual prominence
        self.chat_canvas = ctk.CTkScrollableFrame(
            left_frame, fg_color=Colors.CARD_BG,
            corner_radius=20, border_width=1, border_color=Colors.BORDER_SUBTLE,
            scrollbar_button_color=Colors.CARD_FLOATING,
            scrollbar_button_hover_color=Colors.CARD_HOVER
        )
        self.chat_canvas.pack(fill="both", expand=True, pady=(0, 20))
        
        self._load_chat_history()

        # Input Area (Focused solely on conversation)
        input_frame = ctk.CTkFrame(left_frame, fg_color="transparent", height=Dims.ENTRY_HEIGHT + 10)
        input_frame.pack(fill="x", pady=(0, 10))
        
        self.mic_btn = ctk.CTkButton(
            input_frame, text="🎤", font=("Segoe UI", 18), width=50, height=Dims.ENTRY_HEIGHT + 10,
            fg_color=Colors.CARD_FLOATING, hover_color=Colors.ACCENT_HOVER, corner_radius=15,
            command=self._start_voice_recognition
        )
        self.mic_btn.pack(side="left", padx=(0, 10))
        
        self.entry = ctk.CTkEntry(
            input_frame, placeholder_text="Message Aurex...",
            font=Fonts.ENTRY, text_color=Colors.TEXT_PRIMARY,
            fg_color=Colors.INPUT_BG, border_width=1, border_color=Colors.INPUT_BORDER,
            height=Dims.ENTRY_HEIGHT + 10, corner_radius=15
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self._send_message())
        
        self.send_btn = ctk.CTkButton(
            input_frame, text="Send", font=Fonts.BUTTON,
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER,
            width=90, height=Dims.ENTRY_HEIGHT + 10, corner_radius=15,
            command=self._send_message
        )
        self.send_btn.pack(side="right")

    def _build_right_column(self):
        right_frame = ctk.CTkFrame(
            self, fg_color=Colors.CARD_BG,
            corner_radius=20, border_width=1, border_color=Colors.BORDER_SUBTLE
        )
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.pack_propagate(False)
        
        header = ctk.CTkFrame(right_frame, fg_color="transparent", height=40)
        header.pack(fill="x", padx=15, pady=(20, 10))
        ctk.CTkLabel(header, text="💬 Conversation History", font=Fonts.HEADING, text_color=Colors.ACCENT_PRIMARY).pack(side="left")
        
        # New Conversation Button
        new_btn = ctk.CTkButton(
            right_frame, text="+ New Conversation", font=Fonts.BUTTON,
            fg_color=Colors.CARD_FLOATING, hover_color=Colors.ACCENT_SUBTLE,
            border_width=1, border_color=Colors.ACCENT_PRIMARY, corner_radius=15,
            command=self._new_conversation
        )
        new_btn.pack(fill="x", padx=15, pady=(0, 10))
        
        self.log_canvas = ctk.CTkScrollableFrame(right_frame, fg_color="transparent")
        self.log_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._refresh_conversation_history()

    def _new_conversation(self):
        new_id = str(uuid.uuid4())
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_sessions (session_id) VALUES (?)", (new_id,))
        conn.commit()
        conn.close()
        
        self.session_id = new_id
        
        self._clear_chat()
        self._load_chat_history()
        self._refresh_conversation_history()

    def _refresh_conversation_history_async(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, title, custom_title, updated_at FROM chat_sessions ORDER BY updated_at DESC LIMIT 15")
        sessions = cursor.fetchall()
        conn.close()
        self.after(0, lambda: self._render_conversation_history(sessions))

    def _refresh_conversation_history(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, title, custom_title, updated_at FROM chat_sessions ORDER BY updated_at DESC LIMIT 15")
        sessions = cursor.fetchall()
        conn.close()
        self._render_conversation_history(sessions)

    def _render_conversation_history(self, sessions):
        destroy_tracked(self._log_widgets)

        if not sessions:
            lbl = ctk.CTkLabel(self.log_canvas, text="No conversation history.", text_color=Colors.TEXT_MUTED, font=Fonts.BODY)
            lbl.pack(pady=20)
            self._log_widgets.append(lbl)
            return
            
        for s in sessions:
            sid = s["session_id"]
            
            display_title = s["custom_title"] if s["custom_title"] else s["title"]
                
            card = ctk.CTkFrame(
                self.log_canvas, 
                fg_color=Colors.CARD_FLOATING if sid != self.session_id else Colors.ACCENT_SUBTLE,
                corner_radius=12, border_width=1, 
                border_color=Colors.ACCENT_PRIMARY if sid == self.session_id else Colors.BORDER_SUBTLE
            )
            card.pack(fill="x", pady=6)
            self._log_widgets.append(card)
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(side="left", fill="both", expand=True, padx=12, pady=12)
            
            ctk.CTkLabel(inner, text=display_title, font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY, anchor="w").pack(fill="x")
            
            updated_at = s["updated_at"]
            if updated_at:
                ts_str = updated_at[:16] if isinstance(updated_at, str) else updated_at.strftime("%Y-%m-%d %H:%M")
            else:
                ts_str = "Just now"
                
            ctk.CTkLabel(inner, text=ts_str, font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED, anchor="w").pack(fill="x", pady=(2, 0))
            
            del_btn = ctk.CTkButton(
                card, text="✕", font=("Segoe UI", 12), width=24, height=24,
                fg_color="transparent", text_color=Colors.TEXT_MUTED, hover_color=Colors.ACCENT_HOVER, corner_radius=12,
                command=lambda s_id=sid: self._confirm_delete_session(s_id)
            )
            del_btn.pack(side="right", padx=(0, 10))

            # Bind click event
            card.bind("<Button-1>", lambda e, s_id=sid: self._load_session(s_id))
            card.configure(cursor="hand2")
            for child in card.winfo_children():
                if child != del_btn:
                    child.bind("<Button-1>", lambda e, s_id=sid: self._load_session(s_id))
                    child.configure(cursor="hand2")
                    for subchild in child.winfo_children():
                        subchild.bind("<Button-1>", lambda e, s_id=sid: self._load_session(s_id))
                        subchild.configure(cursor="hand2")

    def _confirm_delete_session(self, session_id):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm")
        dialog.geometry("300x150")
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (300 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (150 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="Delete this conversation?", font=Fonts.BODY_BOLD).pack(pady=(20, 20))
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)
        
        def on_delete():
            dialog.destroy()
            self._delete_session(session_id)
            
        def on_cancel():
            dialog.destroy()
            
        ctk.CTkButton(btn_frame, text="Cancel", fg_color=Colors.CARD_FLOATING, hover_color=Colors.CARD_HOVER, width=100, command=on_cancel).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Delete", fg_color=Colors.ERROR, hover_color=Colors.ERROR_HOVER, width=100, command=on_delete).pack(side="right", padx=10)

    def _delete_session(self, session_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE session_id=?", (session_id,))
        cursor.execute("DELETE FROM chat_sessions WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()
        
        if self.session_id == session_id:
            self._new_conversation()
        else:
            self._refresh_conversation_history()

    def _load_session(self, session_id):
        if self.session_id == session_id:
            return
            
        self.session_id = session_id
        
        self._clear_chat()
        self._load_chat_history()
        self._refresh_conversation_history()

    def _load_chat_history(self):
        conn = get_connection()
        history = conn.execute(
            "SELECT role, message, timestamp FROM chat_messages WHERE session_id=? ORDER BY timestamp DESC LIMIT ?",
            (self.session_id, MAX_CHAT_MESSAGES),
        ).fetchall()
        conn.close()
        
        if history:
            for row in reversed(history):
                if row["role"] in ["user", "assistant"]:
                    self._add_bubble(row["message"], row["role"], row["timestamp"])
        else:
            self._add_bubble("Greetings. I am Aurex AI. How may I assist you today?", "assistant", datetime.datetime.now())

    def _add_bubble(self, text, role, timestamp=None):
        row = ctk.CTkFrame(self.chat_canvas, fg_color="transparent")
        row.pack(fill="x", pady=12, padx=10)
        self._chat_bubbles.append(row)
        
        if role == "user":
            bg_color = Colors.ACCENT_PRIMARY # Approximates vibrant gradient feel
            border_color = Colors.ACCENT_HOVER
            text_color = Colors.TEXT_PRIMARY
            side = "right"
            justify = "right"
            sender_text = "You"
        else:
            bg_color = Colors.CARD_FLOATING
            border_color = Colors.BORDER_SUBTLE
            text_color = Colors.TEXT_PRIMARY
            side = "left"
            justify = "left"
            sender_text = "AUREX AI"
            
        bubble = ctk.CTkFrame(row, fg_color=bg_color, corner_radius=18, border_width=1, border_color=border_color)
        bubble.pack(side=side, fill="x", expand=False)
        
        header_frame = ctk.CTkFrame(bubble, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(header_frame, text=sender_text, font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_PRESSED if role == "assistant" else Colors.TEXT_PRIMARY).pack(side="left")
        if timestamp:
            ts_str = timestamp if isinstance(timestamp, str) else timestamp.strftime("%H:%M")
            ctk.CTkLabel(header_frame, text=ts_str[:16], font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED).pack(side="right", padx=(15, 0))
        
        lbl = ctk.CTkLabel(
            bubble, text=text, font=Fonts.BODY, text_color=text_color,
            justify=justify, wraplength=700 # Increased wrap length
        )
        lbl.pack(padx=20, pady=(6, 16))
        
        self.after(50, lambda: self.chat_canvas._parent_canvas.yview_moveto(1.0))
        return bubble

    def _send_message(self, text_override=None):
        msg = text_override if text_override is not None else self.entry.get().strip()
        if not msg: return
        
        if text_override is None:
            self.entry.delete(0, 'end')
            
        self._add_bubble(msg, "user", datetime.datetime.now())
        
        self.loading_bubble = self._add_bubble("Thinking...", "assistant", datetime.datetime.now())
        self.send_btn.configure(state="disabled")
        self.mic_btn.configure(state="disabled")
        
        threading.Thread(target=ai_service.process_message, args=(self.session_id, self.user_id, msg), daemon=True).start()

    def _on_ai_response(self, data):
        if data.get("session_id") != self.session_id: return
            
        if self.loading_bubble:
            self.loading_bubble.master.destroy()
            self.loading_bubble = None
            
        response_text = data.get("text", "Error rendering response.")
        self._add_bubble(response_text, "assistant", datetime.datetime.now())
        
        self.send_btn.configure(state="normal")
        self.mic_btn.configure(state="normal")
        self.mic_btn.configure(text="🎤", fg_color=Colors.CARD_FLOATING)
        
        # Refresh log in case actions were taken (like a new session created implicitly, although we don't do that yet, but good to refresh)
        self._refresh_conversation_history()

    def _start_voice_recognition(self):
        self.mic_btn.configure(state="disabled", text="🎙️", fg_color=Colors.ACCENT_PRIMARY)
        self.entry.configure(placeholder_text="Listening...")
        threading.Thread(target=self._listen_worker, daemon=True).start()
        
    def _listen_worker(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = recognizer.recognize_google(audio)
                
                self.after(0, self._handle_voice_success, text)
            except sr.WaitTimeoutError:
                self.after(0, self._handle_voice_error, "Listening timed out.")
            except sr.UnknownValueError:
                self.after(0, self._handle_voice_error, "Could not understand audio.")
            except Exception as e:
                self.after(0, self._handle_voice_error, f"Error: {str(e)}")

    def _handle_voice_success(self, text):
        self.entry.configure(placeholder_text="Message Aurex...")
        self.mic_btn.configure(state="normal", text="🎤", fg_color=Colors.CARD_FLOATING)
        self._send_message(text_override=text)
        
    def _handle_voice_error(self, error_msg):
        self.entry.configure(placeholder_text="Message Aurex...")
        self.mic_btn.configure(state="normal", text="🎤", fg_color=Colors.CARD_FLOATING)
        self._add_bubble(f"Voice Error: {error_msg}", "assistant", datetime.datetime.now())
