"""
FLOWSPACE Background Generator — Dynamic deep-space nebula with starfield.
Uses Pillow to generate a cosmic background image at runtime.
"""

import random
import threading
import os
from PIL import Image, ImageDraw, ImageFilter
import customtkinter as ctk

# Mapping page views to their respective custom space backgrounds
PAGE_BACKGROUNDS = {
    "Dashboard": "bg_dashboard.png",
    "FLOWSPACE AI": "bg_aurex_ai.png",
    "AI Planner": "bg_ai_planner.png",
    "Task Manager": "bg_task_manager.png",
    "Summarizer": "bg_notes_docs.png",
    "Notes & Docs": "bg_notes_docs.png",
    "Calendar": "bg_calendar.png",
    "Analytics": "bg_analytics.png",
    "History": "bg_history.png",
    "Image Studio": "bg_calendar.png",
    "File Converter": "bg_analytics.png",
    "Focus Mode": "bg_focus_mode.png",
    "Pomodoro Timer": "bg_focus_mode.png",
    "Goal Tracker": "bg_goal_tracker.png",
    "Habit Tracker": "bg_goal_tracker.png",
    "Settings": "bg_settings.png",
    "Accounts": "bg_settings.png",
    "auth": "bg_settings.png"
}



def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Linearly interpolate between two RGB colors."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def generate_nebula_background(width: int, height: int, seed: int = 42) -> Image.Image:
    """
    Generate a rich deep-space nebula background image.

    Layers:
    1. Dark gradient base (deep navy → near-black)
    2. Multiple nebula glow blobs (purple, blue, orange) with heavy blur
    3. Scattered starfield (tiny bright dots)
    """
    rng = random.Random(seed)
    img = Image.new("RGB", (width, height), (8, 8, 24))

    # ── Layer 1: Base gradient ──────────────────────────────────────────
    top_color = (16, 25, 45)
    mid_color = (12, 21, 38)
    bot_color = (8, 17, 32)

    grad_h = min(height, 256)
    grad = Image.new("RGB", (1, grad_h))
    grad_draw = ImageDraw.Draw(grad)
    for y in range(grad_h):
        t = y / max(grad_h - 1, 1)
        if t < 0.5:
            c = _lerp_color(top_color, mid_color, t * 2)
        else:
            c = _lerp_color(mid_color, bot_color, (t - 0.5) * 2)
        grad_draw.point((0, y), fill=c)
    img = grad.resize((width, height), Image.Resampling.BILINEAR)

    # ── Layer 2 & 3 Optimization: Downscaled Blur ─────────────────────
    scale = 256 / max(width, height) if max(width, height) > 256 else 1.0
    sw, sh = max(1, int(width * scale)), max(1, int(height * scale))

    nebula_layer = Image.new("RGB", (sw, sh), (0, 0, 0))
    nebula_draw = ImageDraw.Draw(nebula_layer)

    nebula_colors = [
        (139, 92, 246),    # electric purple
        (6, 182, 212),     # cyan
        (244, 63, 94),     # hot pink
        (109, 59, 215),    # deep purple
        (3, 181, 211),     # teal cyan
    ]

    for _ in range(rng.randint(6, 9)):
        cx = rng.randint(int(-sw * 0.2), int(sw * 1.2))
        cy = rng.randint(int(-sh * 0.2), int(sh * 1.2))
        rx = rng.randint(int(sw * 0.15), int(sw * 0.5))
        ry = rng.randint(int(sh * 0.15), int(sh * 0.5))
        color = tuple(c // 3 for c in rng.choice(nebula_colors))
        nebula_draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color)

    nebula_layer = nebula_layer.filter(ImageFilter.GaussianBlur(radius=max(sw, sh) // 6))

    from PIL import ImageChops
    if scale != 1.0:
        nebula_layer = nebula_layer.resize((width, height), Image.Resampling.BILINEAR)

    img = ImageChops.add(img, nebula_layer)

    # ── Layer 4: Starfield ──────────────────────────────────────────────
    draw = ImageDraw.Draw(img)
    num_stars = max(120, (width * height) // 6000)

    for _ in range(num_stars):
        sx = rng.randint(0, width - 1)
        sy = rng.randint(0, height - 1)
        brightness = rng.randint(90, 255)
        if rng.random() > 0.85:
            b2 = brightness // 3
            draw.point((sx, sy), fill=(brightness, brightness, brightness))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = sx + dx, sy + dy
                if 0 <= nx < width and 0 <= ny < height:
                    draw.point((nx, ny), fill=(b2, b2, b2))
        else:
            draw.point((sx, sy), fill=(brightness, brightness, brightness))

    return img


class NebulaBackground:
    """Manages a high-performance responsive deep-space background with caching."""

    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self._bg_label = None
        self._current_size = (0, 0)
        self._resize_after_id = None
        self._seed = 42
        self.current_page = "Dashboard"
        self.current_pil_image = None
        self._ctk_image = None
        self._is_rendering = False

        self.bg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "backgrounds")

    def setup(self, container=None):
        """Create the background label and bind resize."""
        target = container or self.parent
        self._bg_label = ctk.CTkLabel(target, text="")
        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self._bg_label.lower()

        # Generate initial background once window metrics are available
        self.parent.update_idletasks()
        w = max(self.parent.winfo_width(), 1000)
        h = max(self.parent.winfo_height(), 650)
        self.parent.after(50, lambda: self._render(w, h))

        # Bind resize with debounce
        self.parent.bind("<Configure>", self._on_resize)

    def set_page_background(self, page_name: str):
        """Switch page reference; reuse cached background without re-render lag."""
        self.current_page = page_name
        if self._ctk_image is not None and self._bg_label:
            return  # Already rendered and active, avoid freezing the UI thread

        w = max(self.parent.winfo_width(), 1000)
        h = max(self.parent.winfo_height(), 650)
        self._render(w, h)

    def _on_resize(self, event):
        """Debounced resize handler — only triggers on window resizing."""
        if event.widget != self.parent:
            return
        if self._resize_after_id:
            try:
                self.parent.after_cancel(self._resize_after_id)
            except Exception:
                pass
        self._resize_after_id = self.parent.after(250, self._do_resize)

    def _do_resize(self):
        """Regenerate background only if dimensions changed significantly."""
        w = self.parent.winfo_width()
        h = self.parent.winfo_height()
        # Avoid thrashing on tiny 1-2px resizing
        if abs(w - self._current_size[0]) > 35 or abs(h - self._current_size[1]) > 35:
            if w > 100 and h > 100:
                self._render(w, h)

    def _render(self, w: int, h: int):
        """Generate and apply background image asynchronously."""
        if self._is_rendering:
            return
        self._is_rendering = True
        self._current_size = (w, h)

        render_w = min(w, 1280)
        render_h = min(h, 720)

        def _worker():
            try:
                img = generate_nebula_background(render_w, render_h, seed=self._seed)
            except Exception as e:
                print(f"Background generation error: {e}")
                img = Image.new("RGB", (render_w, render_h), (8, 12, 24))

            def _apply():
                self._is_rendering = False
                self.current_pil_image = img
                self._apply_image(img, w, h)

            if hasattr(self.parent, "after"):
                self.parent.after(0, _apply)

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_image(self, pil_img: Image.Image, w: int, h: int):
        """Convert PIL image to CTkImage and apply to the background label."""
        if (pil_img.width, pil_img.height) != (w, h):
            display_img = pil_img.resize((w, h), Image.Resampling.BILINEAR)
        else:
            display_img = pil_img

        ctk_img = ctk.CTkImage(light_image=display_img, dark_image=display_img, size=(w, h))
        self._ctk_image = ctk_img
        if self._bg_label and self._bg_label.winfo_exists():
            self._bg_label.configure(image=ctk_img)
            self._bg_label._ctk_image = ctk_img  # prevent GC

    @property
    def label(self):
        return self._bg_label
