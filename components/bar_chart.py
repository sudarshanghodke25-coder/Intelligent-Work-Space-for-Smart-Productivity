import customtkinter as ctk
from theme import Colors, Fonts
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class BarChart(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.data = [
            ("Sun", 3.2), ("Mon", 5.8), ("Tue", 7.1),
            ("Wed", 4.5), ("Thu", 8.0), ("Fri", 6.3), ("Sat", 2.0),
        ]
        
        fig, self.ax = plt.subplots(figsize=(4, 2.5), facecolor='none')
        fig.patch.set_alpha(0.0)
        self.ax.patch.set_alpha(0.0)
        
        labels = [d[0] for d in self.data]
        values = [d[1] for d in self.data]
        
        self.ax.bar(labels, values, color=Colors.ACCENT_PRIMARY, width=0.5, zorder=3)
        
        self.ax.tick_params(axis='x', colors=Colors.TEXT_MUTED)
        self.ax.tick_params(axis='y', colors=Colors.TEXT_MUTED)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#3a3a4a')
        self.ax.spines['bottom'].set_color('#3a3a4a')
        self.ax.grid(axis='y', linestyle='--', alpha=0.2, zorder=0)
        
        fig.tight_layout(pad=1.0)
        
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=Colors.GLASS_FILL, highlightthickness=0)
        widget.pack(fill="both", expand=True)
