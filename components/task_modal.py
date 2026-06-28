import customtkinter as ctk
from datetime import datetime
from theme import Colors, Fonts, Dims

class TaskModal(ctk.CTkToplevel):
    def __init__(self, parent, task=None, on_save=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.title("New Task" if not task else "Edit Task")
        self.geometry("450x550")
        self.configure(fg_color=Colors.BG_DEEPSPACE)
        self.resizable(False, False)
        
        # Center the modal relative to parent
        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (450 // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (550 // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass
            
        self.transient(parent)
        self.grab_set()
        
        self.task = task
        self.on_save = on_save
        
        self._build_ui()
        self._populate()
        
    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Colors.CARD_FLOATING, corner_radius=15, border_width=1, border_color=Colors.BORDER_SUBTLE)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        lbl_font = Fonts.SMALL_BOLD
        
        # Title
        ctk.CTkLabel(container, text="Task Title", font=lbl_font, text_color=Colors.TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 5))
        self.title_entry = ctk.CTkEntry(container, font=Fonts.ENTRY, fg_color=Colors.INPUT_BG, border_color=Colors.INPUT_BORDER, height=Dims.ENTRY_HEIGHT)
        self.title_entry.pack(fill="x", padx=15)
        
        # Grid for Category, Priority, Due Date
        grid = ctk.CTkFrame(container, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=10)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        
        # Category
        ctk.CTkLabel(grid, text="Project/Category", font=lbl_font, text_color=Colors.TEXT_MUTED).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.cat_entry = ctk.CTkEntry(grid, font=Fonts.ENTRY, fg_color=Colors.INPUT_BG, border_color=Colors.INPUT_BORDER, height=Dims.ENTRY_HEIGHT)
        self.cat_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        # Priority
        ctk.CTkLabel(grid, text="Priority", font=lbl_font, text_color=Colors.TEXT_MUTED).grid(row=0, column=1, sticky="w", pady=(0, 5))
        self.priority_var = ctk.StringVar(value="Medium")
        self.priority_combo = ctk.CTkComboBox(grid, values=["High", "Medium", "Low"], variable=self.priority_var, font=Fonts.ENTRY, fg_color=Colors.INPUT_BG, border_color=Colors.INPUT_BORDER, button_color=Colors.CARD_FLOATING, height=Dims.ENTRY_HEIGHT)
        self.priority_combo.grid(row=1, column=1, sticky="ew")
        
        # Due Date
        ctk.CTkLabel(container, text="Due Date (YYYY-MM-DD)", font=lbl_font, text_color=Colors.TEXT_MUTED).pack(anchor="w", padx=15, pady=(5, 5))
        self.due_entry = ctk.CTkEntry(container, font=Fonts.ENTRY, fg_color=Colors.INPUT_BG, border_color=Colors.INPUT_BORDER, height=Dims.ENTRY_HEIGHT, placeholder_text="e.g. 2026-12-31")
        self.due_entry.pack(fill="x", padx=15)
        
        # Description
        ctk.CTkLabel(container, text="Description", font=lbl_font, text_color=Colors.TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 5))
        self.desc_text = ctk.CTkTextbox(container, font=Fonts.ENTRY, fg_color=Colors.INPUT_BG, border_color=Colors.INPUT_BORDER, height=80, border_width=1)
        self.desc_text.pack(fill="x", padx=15)
        
        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=20, side="bottom")
        
        ctk.CTkButton(btn_frame, text="Cancel", font=Fonts.BUTTON, fg_color="transparent", border_width=1, border_color=Colors.BORDER_SUBTLE, hover_color=Colors.CARD_HOVER, command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Save Task", font=Fonts.BUTTON, fg_color=Colors.ACCENT_PRIMARY, hover_color=Colors.ACCENT_HOVER, command=self._save).pack(side="right", expand=True, padx=(5, 0))
        
    def _populate(self):
        if self.task:
            self.title_entry.insert(0, self.task.get("title", ""))
            self.cat_entry.insert(0, self.task.get("category") or "Work")
            self.priority_var.set(self.task.get("priority", "Medium"))
            
            due = self.task.get("due_date") or ""
            self.due_entry.insert(0, due[:10])
            
            desc = self.task.get("description", "")
            if desc:
                self.desc_text.insert("1.0", desc)
                
    def _save(self):
        if not self.on_save:
            self.destroy()
            return
            
        data = {
            "title": self.title_entry.get().strip() or "Untitled Task",
            "category": self.cat_entry.get().strip() or "Work",
            "priority": self.priority_var.get(),
            "due_date": self.due_entry.get().strip(),
            "description": self.desc_text.get("1.0", "end-1c").strip()
        }
        
        if self.task:
            data["id"] = self.task["id"]
            
        self.on_save(data)
        self.destroy()
