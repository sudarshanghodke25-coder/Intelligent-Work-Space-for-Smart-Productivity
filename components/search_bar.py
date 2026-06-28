import customtkinter as ctk
from theme import Colors, Fonts, Dims

class SearchBar(ctk.CTkFrame):
    def __init__(self, parent, placeholder="Search...", command=None, **kwargs):
        super().__init__(parent, fg_color=Colors.INPUT_BG, corner_radius=Dims.ENTRY_CORNER, border_width=1, border_color=Colors.INPUT_BORDER, height=Dims.ENTRY_HEIGHT, **kwargs)
        self.pack_propagate(False)
        
        self.command = command
        
        self.icon_label = ctk.CTkLabel(self, text="🔍", font=Fonts.BODY, text_color=Colors.TEXT_MUTED, width=30)
        self.icon_label.pack(side="left", padx=(10, 5))
        
        self.entry = ctk.CTkEntry(
            self, placeholder_text=placeholder, font=Fonts.ENTRY, 
            fg_color="transparent", border_width=0, text_color=Colors.TEXT_PRIMARY
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Debounce timer
        self._timer = None
        self.entry.bind("<KeyRelease>", self._on_key_release)
        
    def _on_key_release(self, event):
        if self._timer is not None:
            self.after_cancel(self._timer)
        self._timer = self.after(300, self._execute_command)
        
    def _execute_command(self):
        if self.command:
            self.command(self.entry.get().strip())
            
    def get_query(self):
        return self.entry.get().strip()
    
    def focus_search(self):
        self.entry.focus()
