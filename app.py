"""
AurexApp — Root application window with routing and layout management.
"""

import customtkinter as ctk
from theme import Colors, Dims
from background import NebulaBackground
from views.auth_view import AuthView
from views.dashboard_view import DashboardView
from views.placeholder_view import PlaceholderView
from components.sidebar import Sidebar
from components.dock import Dock


class AurexApp(ctk.CTk):
    """
    Main Aurex application.
    Manages the nebula background, authentication flow,
    and the main dashboard layout with routing.
    """

    def __init__(self):
        super().__init__()

        # ── Window configuration ────────────────────────────────────────
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Aurex")
        self.geometry("1400x850")
        self.minsize(1000, 650)
        self.configure(fg_color=Colors.BG_DEEPSPACE)

        # ── State ───────────────────────────────────────────────────────
        self._current_view = None
        self._current_view_name = None
        self._main_layout_built = False

        # Layout containers (created when entering main layout)
        self._sidebar = None
        self._content_area = None
        self._dock = None
        self._content_frame = None  # holds the current view

        # ── Nebula background ───────────────────────────────────────────
        self.nebula = NebulaBackground(self)
        self.nebula.setup()

        # ── Start with auth ─────────────────────────────────────────────
        self._show_auth()

    # ── Navigation / Routing ────────────────────────────────────────────

    def _show_auth(self):
        """Show the authentication view."""
        self._teardown_main_layout()
        self._current_view_name = "auth"

        self._current_view = AuthView(
            self, on_auth_success=self._on_auth_success
        )
        self._current_view.place(x=0, y=0, relwidth=1, relheight=1)
        self._current_view.lift()

    def _on_auth_success(self):
        """Called when authentication succeeds — transition to main layout."""
        if self._current_view:
            self._current_view.destroy()
            self._current_view = None

        self._build_main_layout()
        self.navigate("Dashboard")

    def _build_main_layout(self):
        """Build the sidebar + content area + dock layout structure."""
        if self._main_layout_built:
            return

        # Main container over the background
        self._main_container = ctk.CTkFrame(self, fg_color="transparent")
        self._main_container.place(x=0, y=0, relwidth=1, relheight=1)
        self._main_container.lift()

        # ── Sidebar (left) ──────────────────────────────────────────────
        self._sidebar = Sidebar(
            self._main_container,
            navigate_callback=self.navigate,
            logout_callback=self._on_logout,
        )
        self._sidebar.pack(side="left", fill="y")

        # ── Right area (content + dock) ─────────────────────────────────
        right = ctk.CTkFrame(self._main_container, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        # Content area (fills most of the space)
        self._content_area = ctk.CTkFrame(right, fg_color="transparent")
        self._content_area.pack(fill="both", expand=True)

        # Dock (bottom)
        self._dock = Dock(right)
        self._dock.pack(fill="x", side="bottom")

        self._main_layout_built = True

    def _teardown_main_layout(self):
        """Remove the main layout (used when going back to auth)."""
        if hasattr(self, '_main_container') and self._main_container:
            self._main_container.destroy()
            self._main_container = None

        self._sidebar = None
        self._content_area = None
        self._dock = None
        self._content_frame = None
        self._main_layout_built = False

    def navigate(self, page_name: str):
        """
        Navigate to a named page.
        Dashboard → DashboardView
        Everything else → PlaceholderView
        """
        if page_name == self._current_view_name:
            return

        # Destroy current content view
        if self._content_frame:
            self._content_frame.destroy()
            self._content_frame = None

        self._current_view_name = page_name

        if hasattr(self, '_sidebar') and self._sidebar:
            self._sidebar.set_active(page_name)

        if page_name == "Dashboard":
            self._content_frame = DashboardView(self._content_area)
        else:
            self._content_frame = PlaceholderView(
                self._content_area, page_name=page_name
            )

        self._content_frame.pack(fill="both", expand=True, padx=12, pady=(8, 4))

    def _on_logout(self):
        """Handle logout — return to auth screen."""
        self._current_view_name = None
        self._show_auth()
