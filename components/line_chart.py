import customtkinter as ctk
from theme import Colors, Fonts
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database.database import get_connection
from services.event_bus import bus

class LineChart(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        bus.subscribe("FOCUS_UPDATED", self._on_focus)
        self._build()
        
    def _on_focus(self, data):
        for widget in self.container.winfo_children():
            widget.destroy()
        self._build()

    def _build(self):
        # Fetch actual focus logs or use mock
        conn = get_connection()
        logs = conn.execute("SELECT SUM(duration_minutes) as t FROM focus_logs").fetchone()
        conn.close()
        
        self.data_1 = [30, 55, 45, 70, 60, 80, 65]
        self.data_2 = [20, 35, 40, 50, 45, 55, 50]
        self.labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # Matplotlib Figure
        fig, self.ax = plt.subplots(figsize=(4, 2), facecolor='none')
        fig.patch.set_alpha(0.0)
        self.ax.patch.set_alpha(0.0)
        
        self.ax.plot(self.labels, self.data_1, color=Colors.CHART_PURPLE, linewidth=2, zorder=3)
        self.ax.plot(self.labels, self.data_2, color=Colors.CHART_BLUE, linewidth=2, zorder=2)
        
        # Fill under
        self.ax.fill_between(self.labels, self.data_1, alpha=0.2, color=Colors.CHART_PURPLE, zorder=1)
        self.ax.fill_between(self.labels, self.data_2, alpha=0.2, color=Colors.CHART_BLUE, zorder=1)
        
        self.ax.tick_params(axis='x', colors=Colors.TEXT_MUTED)
        self.ax.tick_params(axis='y', colors=Colors.TEXT_MUTED)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#3a3a4a')
        self.ax.spines['bottom'].set_color('#3a3a4a')
        
        fig.tight_layout(pad=1.0)
        
        self.canvas = FigureCanvasTkAgg(fig, master=self.container)
        self.canvas.draw()
        
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=Colors.GLASS_FILL, highlightthickness=0)
        widget.pack(fill="both", expand=True, pady=(0, 8))
        
        # Stats row
        stats_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        stats_frame.pack(fill="x")
        stats_frame.pack_propagate(False)

        stats = [
            ("61%", "Focus Score", Colors.CHART_GREEN),
            ("28h", "Deep Work", Colors.CHART_PURPLE),
            ("11", "Tasks Done", Colors.CHART_BLUE),
        ]

        for value, label, color in stats:
            col = ctk.CTkFrame(stats_frame, fg_color="transparent")
            col.pack(side="left", expand=True)

            ctk.CTkLabel(col, text=value, font=Fonts.SUBHEADING, text_color=color).pack()
            ctk.CTkLabel(col, text=label, font=Fonts.CAPTION, text_color=Colors.TEXT_MUTED).pack()
