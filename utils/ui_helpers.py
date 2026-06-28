"""Shared UI helpers for safe CustomTkinter scrollable-frame management."""


def destroy_tracked(widgets):
    """Destroy only user-created widgets; safe for CTkScrollableFrame contents."""
    for widget in widgets:
        try:
            if widget.winfo_exists():
                widget.destroy()
        except Exception:
            pass
    widgets.clear()


def clear_scrollable(scroll_frame, tracked_widgets):
    """Clear a CTkScrollableFrame without touching internal canvas/scrollbar."""
    destroy_tracked(tracked_widgets)


def sync_sidebar_active(sidebar, page_name):
    """Update sidebar highlight without triggering navigation."""
    if not sidebar or page_name not in getattr(sidebar, "_menu_items", {}):
        return
    if page_name == sidebar._active_page:
        return
    if sidebar._active_page in sidebar._menu_items:
        sidebar._menu_items[sidebar._active_page].set_active(False)
    sidebar._active_page = page_name
    sidebar._menu_items[page_name].set_active(True)
