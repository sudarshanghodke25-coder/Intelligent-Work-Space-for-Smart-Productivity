import customtkinter as ctk
from tkinter import filedialog
import threading
import os
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from database.database import get_connection
from services.event_bus import bus
from services.ai_service import ai_service
from utils.file_parser import extract_text

class NotesDocsView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        # Grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1, minsize=300) # Left Sidebar
        self.grid_columnconfigure(1, weight=3)              # Right Editor/Viewer
        
        # Left Panel Container
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(4, 10), pady=10)
        
        # Right Panel Container (GlassCard)
        self.right_panel = GlassCard(self, title="Document Viewer")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 4), pady=10)
        
        # State tracking
        self.current_doc_id = None
        self.current_state = "BLANK" # states: BLANK, MANUAL_EDIT, LOADING, AI_VIEW
        
        self._build_left_panel()
        self._build_right_panel()
        
        bus.subscribe("DOC_ANALYZED", self._on_doc_analyzed)
        self._load_documents()

    def _build_left_panel(self):
        # Header
        ctk.CTkLabel(
            self.left_panel, text="📁 Notes & Docs", 
            font=Fonts.TITLE, text_color=Colors.TEXT_PRIMARY, anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        # Search Bar
        self.search_entry = ctk.CTkEntry(
            self.left_panel, placeholder_text="Search in notes...", 
            font=Fonts.ENTRY, height=Dims.ENTRY_HEIGHT
        )
        self.search_entry.pack(fill="x", pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._load_documents)
        
        # Action Buttons
        btn_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(
            btn_frame, text="Create Note", font=Fonts.BUTTON, 
            fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, 
            command=self._create_note
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        ctk.CTkButton(
            btn_frame, text="Upload Document", font=Fonts.BUTTON, 
            fg_color=Colors.GLASS_FILL_LIGHT, hover_color=Colors.GLASS_FILL_HOVER, 
            text_color=Colors.TEXT_PRIMARY, border_color=Colors.GLASS_BORDER_BRIGHT, 
            border_width=1, command=self._upload_doc
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))
        
        # Document List
        self.doc_list = ctk.CTkScrollableFrame(
            self.left_panel, fg_color=Colors.GLASS_FILL, 
            border_width=1, border_color=Colors.GLASS_BORDER, corner_radius=10
        )
        self.doc_list.pack(fill="both", expand=True)

    def _load_documents(self, event=None):
        search_query = self.search_entry.get().strip().lower()
        
        for widget in self.doc_list.winfo_children():
            widget.destroy()
            
        conn = get_connection()
        if search_query:
            docs = conn.execute("SELECT id, title, file_type, summary FROM documents WHERE lower(title) LIKE ? ORDER BY created_at DESC", (f"%{search_query}%",)).fetchall()
        else:
            docs = conn.execute("SELECT id, title, file_type, summary FROM documents ORDER BY created_at DESC").fetchall()
        conn.close()
        
        for d in docs:
            self._build_doc_row(d)

    def _build_doc_row(self, doc):
        row = ctk.CTkFrame(self.doc_list, fg_color="transparent")
        row.pack(fill="x", pady=4)
        
        icon = "📄" if doc["file_type"] == "manual" else "📚"
        title = doc["title"]
        if len(title) > 25: title = title[:22] + "..."
        
        ctk.CTkLabel(row, text=icon, font=Fonts.BODY).pack(side="left", padx=(5, 5))
        ctk.CTkLabel(row, text=title, font=Fonts.BODY, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=(0, 10))
        
        btn_text = "View" if doc["file_type"] == "manual" else ("Summary" if doc["summary"] else "Analyze")
        btn_color = Colors.ACCENT_PRIMARY if doc["summary"] or doc["file_type"] == "manual" else Colors.GLASS_FILL_LIGHT
        
        ctk.CTkButton(
            row, text=btn_text, font=Fonts.SMALL, width=60, height=24, 
            fg_color=btn_color, command=lambda d=doc: self._open_document(d)
        ).pack(side="right", padx=(0, 5))

    def _build_right_panel(self):
        # Destroy current card content
        for widget in self.right_panel.content.winfo_children():
            widget.destroy()
            
        if self.current_state == "BLANK":
            ctk.CTkLabel(
                self.right_panel.content, text="Select a document or Create a new note", 
                font=Fonts.BODY, text_color=Colors.TEXT_MUTED
            ).pack(expand=True)
            
        elif self.current_state == "LOADING":
            ctk.CTkLabel(
                self.right_panel.content, text="Analyzing Document via Aurex AI...", 
                font=Fonts.BODY_BOLD, text_color=Colors.ACCENT_PRIMARY
            ).pack(expand=True)
            
        elif self.current_state == "MANUAL_EDIT":
            self.note_textbox = ctk.CTkTextbox(
                self.right_panel.content, font=Fonts.BODY, 
                fg_color=Colors.ENTRY_BG, border_width=1, border_color=Colors.ENTRY_BORDER, 
                text_color=Colors.TEXT_PRIMARY
            )
            self.note_textbox.pack(fill="both", expand=True, pady=(0, 10))
            
            ctk.CTkButton(
                self.right_panel.content, text="Save Note", font=Fonts.BUTTON, 
                fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, 
                command=self._save_manual_note
            ).pack(anchor="e")
            
        elif self.current_state == "AI_VIEW":
            
            ctk.CTkLabel(
                self.right_panel.content, text="Executive Summary", 
                font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_GLOW, anchor="w"
            ).pack(fill="x", pady=(0, 4))
            
            self.summary_box = ctk.CTkTextbox(
                self.right_panel.content, font=Fonts.BODY, 
                fg_color=Colors.GLASS_FILL_LIGHT, height=120, text_color=Colors.TEXT_PRIMARY,
                wrap="word"
            )
            self.summary_box.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(
                self.right_panel.content, text="Key Points Extraction", 
                font=Fonts.SMALL_BOLD, text_color=Colors.ACCENT_GLOW, anchor="w"
            ).pack(fill="x", pady=(0, 4))
            
            self.keypoints_box = ctk.CTkTextbox(
                self.right_panel.content, font=Fonts.BODY, 
                fg_color=Colors.GLASS_FILL_LIGHT, text_color=Colors.TEXT_PRIMARY,
                wrap="word"
            )
            self.keypoints_box.pack(fill="both", expand=True)

    def _create_note(self):
        self.current_state = "MANUAL_EDIT"
        self.current_doc_id = None
        self._build_right_panel()
        
    def _save_manual_note(self):
        text = self.note_textbox.get("1.0", "end-1c").strip()
        if not text: return
        title = text[:20] + "..." if len(text) > 20 else text
        
        conn = get_connection()
        if self.current_doc_id:
            conn.execute("UPDATE documents SET raw_content = ?, title = ? WHERE id = ?", (text, title, self.current_doc_id))
        else:
            cur = conn.execute("INSERT INTO documents (title, file_type, raw_content) VALUES (?, 'manual', ?)", (title, text))
            self.current_doc_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        self._load_documents()

    def _upload_doc(self):
        filepath = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.docx *.txt")])
        if not filepath: return
        
        title = os.path.basename(filepath)
        ext = os.path.splitext(filepath)[1].lower().replace('.', '')
        if not ext: ext = "txt"
        
        raw_text = extract_text(filepath)
        
        # Save to DB immediately
        conn = get_connection()
        cur = conn.execute("INSERT INTO documents (title, file_type, raw_content) VALUES (?, ?, ?)", (title, ext, raw_text))
        doc_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        self._load_documents()
        
        # Dispatch AI Analysis
        self.current_doc_id = doc_id
        self.current_state = "LOADING"
        self._build_right_panel()
        
        threading.Thread(target=ai_service.analyze_document_background, args=(doc_id, raw_text), daemon=True).start()

    def _open_document(self, doc):
        self.current_doc_id = doc["id"]
        
        conn = get_connection()
        full_doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc["id"],)).fetchone()
        conn.close()
        
        if full_doc["file_type"] == "manual":
            self.current_state = "MANUAL_EDIT"
            self._build_right_panel()
            self.note_textbox.insert("1.0", full_doc["raw_content"])
        else:
            if full_doc["summary"]:
                self.current_state = "AI_VIEW"
                self._build_right_panel()
                self.summary_box.insert("1.0", full_doc["summary"])
                self.summary_box.configure(state="disabled")
                self.keypoints_box.insert("1.0", full_doc["key_points"])
                self.keypoints_box.configure(state="disabled")
            else:
                # Missing summary, trigger re-analysis
                self.current_state = "LOADING"
                self._build_right_panel()
                threading.Thread(target=ai_service.analyze_document_background, args=(full_doc["id"], full_doc["raw_content"]), daemon=True).start()

    def _on_doc_analyzed(self, payload):
        # Use .after() to guarantee thread safety when unpacking background thread results
        self.after(0, lambda: self._process_analyzed_doc(payload))
        
    def _process_analyzed_doc(self, payload):
        doc_id = payload.get("doc_id")
        error = payload.get("error")
        summary = payload.get("summary")
        key_points = payload.get("key_points")
        
        if error:
            if self.current_doc_id == doc_id:
                self.current_state = "BLANK"
                self._build_right_panel()
            return
            
        conn = get_connection()
        conn.execute("UPDATE documents SET summary = ?, key_points = ? WHERE id = ?", (summary, key_points, doc_id))
        conn.commit()
        conn.close()
        
        self._load_documents()
        
        if self.current_doc_id == doc_id:
            self.current_state = "AI_VIEW"
            self._build_right_panel()
            
            self.summary_box.insert("1.0", summary)
            self.summary_box.configure(state="disabled")
            
            self.keypoints_box.insert("1.0", key_points)
            self.keypoints_box.configure(state="disabled")
