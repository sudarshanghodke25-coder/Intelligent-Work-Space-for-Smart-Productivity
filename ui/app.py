import customtkinter as ctk
from theme import Colors
from background import NebulaBackground
from views.auth_view import AuthView
from ui.sidebar import Sidebar
from services.event_bus import bus
from services.engine import focus_tracker, suggestion_scanner
from services.event_subscribers import init_subscribers
from utils.ui_helpers import sync_sidebar_active


class AurexApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        init_subscribers()

        import json
        from pathlib import Path
        try:
            settings_path = Path(__file__).parent.parent / "settings.json"
            if settings_path.exists():
                with open(settings_path, "r") as f:
                    settings = json.load(f)
                    theme = settings.get("theme", "Dark")
                    if theme == "Light":
                        ctk.set_appearance_mode("light")
                    else:
                        ctk.set_appearance_mode("dark")
            else:
                ctk.set_appearance_mode("dark")
        except:
            ctk.set_appearance_mode("dark")
            
        ctk.set_default_color_theme("dark-blue")

        self.title("AUREX Cosmic Glass Workspace")
        self.geometry("1400x850")
        self.minsize(1000, 650)
        self.configure(fg_color=Colors.BG_PRIMARY)

        self._current_view = None
        self._current_view_name = None
        self._main_layout_built = False
        self._cached_views = {}
        self._view_registry = None

        self.nebula = NebulaBackground(self)
        self.nebula.setup()

        bus.set_app(self)
        bus.subscribe("NAVIGATE_TO", self.navigate)
        bus.subscribe("LOGOUT", lambda _: self._show_login())

        self._show_login()

    def _get_view_registry(self):
        """Lazy-load heavy view modules on first navigation."""
        if self._view_registry is None:
            from ui.dashboard import DashboardView
            from ui.settings import SettingsView
            from ui.views.assistant_view import AssistantView
            from pages.history import HistoryView
            from ui.views.notes_docs_view import NotesDocsView
            from ui.views.task_manager_view import TasksView
            from ui.views.planner_view import PlannerView
            from ui.views.image_studio_view import ImageStudioView
            from file_converter.views.converter_view import FileConverterView
            from ui.views.focus_view import FocusView
            from ui.views.goal_tracker_view import GoalTrackerView
            from ui.views.accounts_view import AccountsView
            from ui.views.calendar_view import CalendarView
            from ui.views.analytics_view import AnalyticsView
            from ui.views.upgrade_view import UpgradeView

            self._view_registry = {
                "Dashboard": DashboardView,
                "Settings": SettingsView,
                "Aurex AI": AssistantView,
                "History": HistoryView,
                "AI Planner": PlannerView,
                "Task Manager": TasksView,
                "Summarizer": NotesDocsView,
                "Notes & Docs": NotesDocsView,
                "Image Studio": ImageStudioView,
                "File Converter": FileConverterView,
                "Focus Mode": FocusView,
                "Pomodoro Timer": FocusView,
                "Goal Tracker": GoalTrackerView,
                "Habit Tracker": GoalTrackerView,
                "Accounts": AccountsView,
                "Calendar": CalendarView,
                "Analytics": AnalyticsView,
                "Upgrade": UpgradeView,
            }
        return self._view_registry

    def _show_login(self):
        self._teardown_main_layout()
        self._current_view_name = "auth"
        self._current_view = AuthView(self, on_auth_success=self._on_login_success)
        self._current_view.place(x=0, y=0, relwidth=1, relheight=1)
        self._current_view.lift()
        if hasattr(self, "nebula") and self.nebula:
            self.nebula.set_page_background("auth")

    def _show_signup(self):
        self._show_login()

    def _on_login_success(self):
        if self._current_view:
            self._current_view.destroy()
            self._current_view = None
        self._build_main_layout()
        
        focus_tracker.start()
        suggestion_scanner.start()
        
        from services.task_status_engine import task_status_engine
        task_status_engine.start()

        from services.embeddings.embedding_service import embedding_service
        import threading
        threading.Thread(target=embedding_service.preload, daemon=True).start()
        
        self.navigate("Dashboard")

    def _build_main_layout(self):
        if self._main_layout_built:
            return

        self._main_container = ctk.CTkFrame(self, fg_color="transparent")
        self._main_container.place(x=0, y=0, relwidth=1, relheight=1)
        self._main_container.lift()

        self._sidebar = Sidebar(self._main_container, navigate_callback=self.navigate, logout_callback=self._show_login)
        self._sidebar.pack(side="left", fill="y", padx=(16, 8), pady=16)

        self._content_area = ctk.CTkFrame(self._main_container, fg_color="transparent")
        self._content_area.pack(side="left", fill="both", expand=True, padx=(8, 16), pady=16)

        self._main_layout_built = True

    def _teardown_main_layout(self):
        for view in self._cached_views.values():
            try:
                if view.winfo_exists():
                    view.destroy()
            except Exception:
                pass
        self._cached_views.clear()
        self._current_view_name = None
        self._view_registry = None

        if hasattr(self, '_main_container') and self._main_container:
            self._main_container.destroy()
            self._main_container = None
        self._sidebar = None
        self._content_area = None
        self._content_frame = None
        self._main_layout_built = False

    def navigate(self, page_name: str):
        if page_name == self._current_view_name:
            return

        if self._current_view_name and self._current_view_name in self._cached_views:
            self._cached_views[self._current_view_name].pack_forget()

        self._current_view_name = page_name
        sync_sidebar_active(getattr(self, "_sidebar", None), page_name)

        views = self._get_view_registry()
        from ui.dashboard import DashboardView

        if page_name not in self._cached_views:
            view_class = views.get(page_name, DashboardView)
            self._cached_views[page_name] = view_class(self._content_area)
            
        self._content_frame = self._cached_views[page_name]
        self._content_frame.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        if hasattr(self, "nebula") and self.nebula:
            self.nebula.set_page_background(page_name)

        on_show = getattr(self._content_frame, "on_show", None)
        if callable(on_show):
            self.after_idle(on_show)
