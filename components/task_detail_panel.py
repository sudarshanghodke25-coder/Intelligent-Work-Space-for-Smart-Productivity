import customtkinter as ctk
from theme import Colors, Fonts

class TaskDetailPanel(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.pack_propagate(False)
        
        self.tabview = ctk.CTkTabview(
            self, 
            fg_color=Colors.GLASS_FILL_LIGHT, 
            segmented_button_fg_color=Colors.GLASS_FILL,
            segmented_button_selected_color=Colors.ACCENT_PRIMARY,
            segmented_button_selected_hover_color=Colors.ACCENT_HOVER,
            segmented_button_unselected_color="transparent",
            segmented_button_unselected_hover_color=Colors.GLASS_FILL_HOVER,
            text_color=Colors.TEXT_PRIMARY
        )
        self.tabview.pack(fill="both", expand=True)
        
        # Create tabs exactly as requested
        self.tab_overview = self.tabview.add("Overview")
        self.tab_description = self.tabview.add("Description")
        self.tab_notes = self.tabview.add("Notes")
        self.tab_activity = self.tabview.add("Activity")
        
        self.current_task = None
        
        self.overview_scroll = ctk.CTkScrollableFrame(self.tab_overview, fg_color="transparent")
        self.overview_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.description_scroll = ctk.CTkScrollableFrame(self.tab_description, fg_color="transparent")
        self.description_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.notes_scroll = ctk.CTkFrame(self.tab_notes, fg_color="transparent")
        self.notes_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.activity_scroll = ctk.CTkScrollableFrame(self.tab_activity, fg_color="transparent")
        self.activity_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    def clear_all(self):
        for container in [self.overview_scroll, self.description_scroll, self.notes_scroll, self.activity_scroll]:
            for widget in container.winfo_children():
                widget.destroy()
