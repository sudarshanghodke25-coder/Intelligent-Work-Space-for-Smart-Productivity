import customtkinter as ctk
from theme import Colors, Fonts
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from services.event_bus import bus

class DonutChart(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        
        bus.subscribe("COMPLETION_UPDATED", self._on_completion)
        self._completion = 0
        self._pending = 0
        self._fetch_stats()
        self._build()

    def _fetch_stats(self):
        from database.database import get_connection
        conn = get_connection()
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='Completed'").fetchone()[0]
        conn.close()
        
        if total > 0:
            self._completion = int((completed / total) * 100)
            self._pending = 100 - self._completion
        else:
            self._completion = 0
            self._pending = 100

    def _on_completion(self, data):
        self._fetch_stats()
        for widget in self.container.winfo_children():
            widget.destroy()
        self._build()

    def _build(self):
        self.segments = [
            {"label": "Completed", "value": self._completion, "color": Colors.CHART_GREEN},
            {"label": "Pending", "value": self._pending, "color": Colors.CHART_RED},
        ]
        
        # Legend frame
        legend_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        legend_frame.pack(side="right", fill="y", padx=10, pady=10)
        
        for seg in self.segments:
            row = ctk.CTkFrame(legend_frame, fg_color="transparent")
            row.pack(anchor="w", pady=4, fill="x")
            dot = ctk.CTkFrame(row, width=10, height=10, corner_radius=5, fg_color=seg["color"])
            dot.pack(side="left", padx=(0, 8))
            dot.pack_propagate(False)
            ctk.CTkLabel(row, text=f"{seg['value']}%", font=Fonts.BODY_BOLD, text_color=Colors.TEXT_PRIMARY).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(row, text=seg["label"], font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY).pack(side="left")

        # Matplotlib Figure
        fig, self.ax = plt.subplots(figsize=(2.5, 2.5), facecolor='none')
        fig.patch.set_alpha(0.0)
        self.ax.patch.set_alpha(0.0)
        
        values = [s["value"] for s in self.segments]
        colors = [s["color"] for s in self.segments]
        
        wedges, _ = self.ax.pie(
            values, colors=colors, startangle=90, 
            wedgeprops=dict(width=0.3, edgecolor='none')
        )
        self.ax.text(0, 0, f"{sum(values)}%", ha='center', va='center', color='white', fontsize=16, fontweight='bold')
        self.ax.text(0, -0.3, "Total", ha='center', va='center', color='#9ca3af', fontsize=10)

        self.canvas = FigureCanvasTkAgg(fig, master=self.container)
        self.canvas.draw()
        
        # We must make the Tkinter canvas widget background match the glass fill because matplotlib's transparent background in TkAgg often falls back to the window default color.
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=Colors.GLASS_FILL, highlightthickness=0)
        widget.pack(side="left", fill="both", expand=True, padx=10, pady=10)
