import customtkinter as ctk
from theme import Colors
from background import NebulaBackground
from views.auth_view import AuthView
from ui.dashboard import DashboardView
from ui.sidebar import Sidebar
from ui.settings import SettingsView
from ui.views.assistant_view import AssistantView
from pages.history import HistoryView
from ui.views.notes_docs_view import NotesDocsView
from pages.generic_pages import CalendarView, AnalyticsView
from ui.views.task_manager_view import TasksView
from ui.views.planner_view import PlannerView
from services.event_bus import bus
from services.engine import focus_tracker, suggestion_scanner

class AurexApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("AUREX Cosmic Glass Workspace")
        self.geometry("1400x850")
        self.minsize(1000, 650)
        self.configure(fg_color=Colors.BG_DEEPSPACE)

        self._current_view = None
        self._current_view_name = None
        self._main_layout_built = False
        self._cached_views = {}

        self.nebula = NebulaBackground(self)
        self.nebula.setup()

        # Initialize event bus marshaling
        bus.set_app(self)

        self._show_login()

    def _show_login(self):
        self._teardown_main_layout()
        self._current_view_name = "auth"
        self._current_view = AuthView(self, on_auth_success=self._on_login_success)
        self._current_view.place(x=0, y=0, relwidth=1, relheight=1)
        self._current_view.lift()

    def _show_signup(self):
        self._show_login()

    def _on_login_success(self):
        if self._current_view:
            self._current_view.destroy()
            self._current_view = None
        self._build_main_layout()
        
        # Start background tracking and AI rules engines
        focus_tracker.start()
        suggestion_scanner.start()
        
        self.navigate("Dashboard")

    def _build_main_layout(self):
        if self._main_layout_built: return

        self._main_container = ctk.CTkFrame(self, fg_color="transparent")
        self._main_container.place(x=0, y=0, relwidth=1, relheight=1)
        self._main_container.lift()

        self._sidebar = Sidebar(self._main_container, navigate_callback=self.navigate, logout_callback=self._show_login)
        self._sidebar.pack(side="left", fill="y")

        self._content_area = ctk.CTkFrame(self._main_container, fg_color="transparent")
        self._content_area.pack(side="left", fill="both", expand=True)

        self._main_layout_built = True

    def _teardown_main_layout(self):
        if hasattr(self, '_main_container') and self._main_container:
            self._main_container.destroy()
            self._main_container = None
        self._sidebar = None
        self._content_area = None
        self._content_frame = None
        self._main_layout_built = False

    def navigate(self, page_name: str):
        if page_name == self._current_view_name: return

        # Hide current view if it exists
        if self._current_view_name and self._current_view_name in self._cached_views:
            self._cached_views[self._current_view_name].pack_forget()

        self._current_view_name = page_name

        views = {
            "Dashboard": DashboardView,
            "Settings": SettingsView,
            "Aurex AI": AssistantView,
            "History": HistoryView,
            "AI Planner": PlannerView,
            "Task Manager": TasksView,
            "Notes & Docs": NotesDocsView,
            "Calendar": CalendarView,
            "Analytics": AnalyticsView
        }
        
        # Instantiate and cache if not exists
        if page_name not in self._cached_views:
            view_class = views.get(page_name, DashboardView)
            self._cached_views[page_name] = view_class(self._content_area)
            
        self._content_frame = self._cached_views[page_name]
        self._content_frame.pack(fill="both", expand=True, padx=12, pady=(8, 4))
