import customtkinter as ctk
from datetime import datetime, timedelta
from theme import Colors, Fonts, Dims
from ui.glass_card import GlassCard
from database.database import get_connection
from services.event_bus import bus
from authentication.session import current_session
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.app = self.winfo_toplevel()
        
        # Grid Architecture
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=4)
        
        # References for Memory Management
        self.donut_canvas = None
        self.donut_fig = None
        self.bar_canvas = None
        self.bar_fig = None
        
        # KPI Cards (Row 0)
        self.kpi_tasks = GlassCard(self, title="Total Tasks")
        self.kpi_tasks.grid(row=0, column=0, sticky="nsew", padx=(4, 6), pady=(10, 6))
        
        self.kpi_progress = GlassCard(self, title="Overall Progress")
        self.kpi_progress.grid(row=0, column=1, sticky="nsew", padx=6, pady=(10, 6))
        
        self.kpi_events = GlassCard(self, title="Upcoming Events")
        self.kpi_events.grid(row=0, column=2, sticky="nsew", padx=(6, 4), pady=(10, 6))
        
        # Chart Containers (Row 1)
        # Using native CTkFrames for charts to avoid GlassCard padding constraints clipping charts
        self.donut_container = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=Dims.RADIUS_CARD, border_width=1, border_color=Colors.BORDER_SUBTLE)
        self.donut_container.grid(row=1, column=0, columnspan=1, sticky="nsew", padx=(4, 6), pady=(6, 10))
        self.donut_container.pack_propagate(False)
        
        self.bar_container = ctk.CTkFrame(self, fg_color=Colors.CARD_BG, corner_radius=Dims.RADIUS_CARD, border_width=1, border_color=Colors.BORDER_SUBTLE)
        self.bar_container.grid(row=1, column=1, columnspan=2, sticky="nsew", padx=(6, 4), pady=(6, 10))
        self.bar_container.pack_propagate(False)
        
        # Initial Build
        self._rebuild_dashboard()
        
        # Subscriptions
        bus.subscribe("TASKS_UPDATED", self._safe_refresh)
        bus.subscribe("EVENTS_UPDATED", self._safe_refresh)

    def _safe_refresh(self, data=None):
        self.app.after(0, self._rebuild_dashboard)
        
    def _rebuild_dashboard(self):
        self._build_kpi_cards()
        self._build_donut_chart()
        self._build_bar_chart()
        
    def _build_kpi_cards(self):
        # Clear existing
        for widget in self.kpi_tasks.content.winfo_children(): widget.destroy()
        for widget in self.kpi_progress.content.winfo_children(): widget.destroy()
        for widget in self.kpi_events.content.winfo_children(): widget.destroy()
        
        conn = get_connection()
        
        # Total Tasks
        user_id = current_session.user_id or 1
        pending = conn.execute("SELECT COUNT(*) FROM tasks WHERE status != 'Completed' AND user_id=?", (user_id,)).fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Completed' AND user_id=?", (user_id,)).fetchone()[0]
        
        # Overall Progress
        avg_prog = conn.execute("SELECT AVG(progress) FROM tasks WHERE user_id=?", (user_id,)).fetchone()[0]
        prog_val = int(avg_prog) if avg_prog else 0
        
        # Upcoming Events (Next 7 Days)
        today_str = datetime.now().strftime("%Y-%m-%d")
        next_week_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        events_count = conn.execute("SELECT COUNT(*) FROM events WHERE event_date BETWEEN ? AND ?", (today_str, next_week_str)).fetchone()[0]
        
        conn.close()
        
        # Render Tasks KPI
        ctk.CTkLabel(self.kpi_tasks.content, text=str(pending + completed), font=("Segoe UI", 48, "bold"), text_color=Colors.TEXT_PRIMARY).pack(expand=True, pady=(10, 0))
        ctk.CTkLabel(self.kpi_tasks.content, text=f"{pending} pending | {completed} completed", font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY).pack(pady=(0, 10))
        
        # Render Progress KPI
        ctk.CTkLabel(self.kpi_progress.content, text=f"{prog_val}%", font=("Segoe UI", 48, "bold"), text_color=Colors.ACCENT_PRIMARY).pack(expand=True, pady=(10, 0))
        ctk.CTkLabel(self.kpi_progress.content, text="Average Task Progress", font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY).pack(pady=(0, 10))
        
        # Render Events KPI
        ctk.CTkLabel(self.kpi_events.content, text=str(events_count), font=("Segoe UI", 48, "bold"), text_color=Colors.SUCCESS).pack(expand=True, pady=(10, 0))
        ctk.CTkLabel(self.kpi_events.content, text="Events in Next 7 Days", font=Fonts.SMALL, text_color=Colors.TEXT_SECONDARY).pack(pady=(0, 10))

    def _build_donut_chart(self):
        # Memory Management: Clear old figure and canvas
        if self.donut_canvas:
            self.donut_canvas.get_tk_widget().destroy()
        if self.donut_fig:
            plt.close(self.donut_fig)
            
        conn = get_connection()
        user_id = current_session.user_id or 1
        rows = conn.execute("SELECT status, COUNT(*) FROM tasks WHERE user_id=? GROUP BY status", (user_id,)).fetchall()
        conn.close()
        
        labels = []
        sizes = []
        colors = []
        
        color_map = {
            "Pending": Colors.CHART_AMBER,
            "In Progress": Colors.CHART_BLUE,
            "Completed": Colors.CHART_GREEN
        }
        
        for row in rows:
            status = row[0]
            count = row[1]
            labels.append(f"{status} ({count})")
            sizes.append(count)
            colors.append(color_map.get(status, Colors.CHART_PURPLE))
            
        if not sizes:
            labels = ["No Tasks"]
            sizes = [1]
            colors = [Colors.CARD_FLOATING]
            
        self.donut_fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        self.donut_fig.patch.set_facecolor(Colors.CARD_BG)
        
        wedges, texts = ax.pie(sizes, colors=colors, startangle=90, wedgeprops=dict(width=0.4, edgecolor=Colors.CARD_BG, linewidth=2))
        ax.axis('equal')
        
        # Title
        ax.set_title("Task Breakdown", color=Colors.TEXT_PRIMARY, fontfamily="Segoe UI", fontsize=14, weight="bold", pad=20)
        
        # Legend
        ax.legend(wedges, labels, loc="center", bbox_to_anchor=(0.5, -0.1), frameon=False, labelcolor=Colors.TEXT_SECONDARY, prop={"family": "Segoe UI", "size": 10})
        
        # Embed
        self.donut_canvas = FigureCanvasTkAgg(self.donut_fig, master=self.donut_container)
        self.donut_canvas.draw()
        self.donut_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
    def _build_bar_chart(self):
        # Memory Management
        if self.bar_canvas:
            self.bar_canvas.get_tk_widget().destroy()
        if self.bar_fig:
            plt.close(self.bar_fig)
            
        # Determine current week dates (Monday to Sunday)
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        
        dates = [start_of_week + timedelta(days=i) for i in range(7)]
        days_str = [d.strftime("%Y-%m-%d") for d in dates]
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        conn = get_connection()
        user_id = current_session.user_id or 1
        tasks = conn.execute("SELECT date(due_date), COUNT(*) FROM tasks WHERE due_date IS NOT NULL AND user_id=? GROUP BY date(due_date)", (user_id,)).fetchall()
        events = conn.execute("SELECT event_date, COUNT(*) FROM events GROUP BY event_date").fetchall()
        conn.close()
        
        task_counts = {row[0]: row[1] for row in tasks}
        event_counts = {row[0]: row[1] for row in events}
        
        t_data = [task_counts.get(d, 0) for d in days_str]
        e_data = [event_counts.get(d, 0) for d in days_str]
        
        self.bar_fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.bar_fig.patch.set_facecolor(Colors.CARD_BG)
        ax.set_facecolor(Colors.CARD_BG)
        
        x = range(len(labels))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], t_data, width, label='Tasks', color=Colors.ACCENT_PRIMARY)
        ax.bar([i + width/2 for i in x], e_data, width, label='Events', color=Colors.CHART_CYAN)
        
        # Styling
        ax.set_title("Weekly Workload", color=Colors.TEXT_PRIMARY, fontfamily="Segoe UI", fontsize=14, weight="bold", pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, color=Colors.TEXT_SECONDARY, fontfamily="Segoe UI")
        ax.tick_params(axis='y', colors=Colors.TEXT_SECONDARY)
        
        # Spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(Colors.BORDER_HOVER)
        ax.spines['bottom'].set_color(Colors.BORDER_HOVER)
        
        # Grid
        ax.yaxis.grid(True, linestyle='--', alpha=0.2, color=Colors.TEXT_MUTED)
        ax.set_axisbelow(True)
        
        # Legend
        ax.legend(frameon=False, labelcolor=Colors.TEXT_PRIMARY, prop={"family": "Segoe UI"})
        
        # Embed
        self.bar_canvas = FigureCanvasTkAgg(self.bar_fig, master=self.bar_container)
        self.bar_canvas.draw()
        self.bar_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

