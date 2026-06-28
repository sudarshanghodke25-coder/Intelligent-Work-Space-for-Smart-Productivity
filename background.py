"""
Aurex Background Generator — Dynamic deep-space nebula with starfield.
Uses Pillow to generate a cosmic background image at runtime.
"""

import random
import math
import threading
import os
from PIL import Image, ImageDraw, ImageFilter
import customtkinter as ctk

# Mapping page views to their respective custom space backgrounds
PAGE_BACKGROUNDS = {
    "Dashboard": "bg_dashboard.png",
    "Aurex AI": "bg_aurex_ai.png",
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
    draw = ImageDraw.Draw(img)

    # ── Layer 1: Base gradient ──────────────────────────────────────────
    top_color = (16, 25, 45)
    mid_color = (12, 21, 38)
    bot_color = (8, 17, 32)

    # Render gradient at reduced height, then scale — much faster than per-pixel at full res
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
    draw = ImageDraw.Draw(img)

    # ── Layer 2: Nebula glow blobs ──────────────────────────────────────
    nebula_colors = [
        (139, 92, 246),    # electric purple
        (6, 182, 212),     # cyan
        (244, 63, 94),     # hot pink
        (109, 59, 215),    # deep purple
        (3, 181, 211),     # teal cyan
    ]

    # Create a separate layer for nebula blobs
    nebula_layer = Image.new("RGB", (width, height), (0, 0, 0))
    nebula_draw = ImageDraw.Draw(nebula_layer)

    num_blobs = rng.randint(6, 10)
    for _ in range(num_blobs):
        cx = rng.randint(int(-width * 0.2), int(width * 1.2))
        cy = rng.randint(int(-height * 0.2), int(height * 1.2))
        rx = rng.randint(int(width * 0.15), int(width * 0.5))
        ry = rng.randint(int(height * 0.15), int(height * 0.5))
        color = rng.choice(nebula_colors)
        # Dim the color for subtlety
        color = tuple(c // 3 for c in color)
        nebula_draw.ellipse(
            [cx - rx, cy - ry, cx + rx, cy + ry],
            fill=color
        )

    # Heavy Gaussian blur to create smooth glow
    nebula_layer = nebula_layer.filter(ImageFilter.GaussianBlur(radius=max(width, height) // 6))

    # Blend nebula layer onto base using screen-like additive blending
    from PIL import ImageChops
    img = ImageChops.add(img, nebula_layer)

    # ── Layer 3: Subtle secondary glow spots ────────────────────────────
    glow_layer = Image.new("RGB", (width, height), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    for _ in range(4):
        cx = rng.randint(0, width)
        cy = rng.randint(0, height)
        r = rng.randint(int(min(width, height) * 0.05), int(min(width, height) * 0.15))
        color = rng.choice([(139, 92, 246), (6, 182, 212), (244, 63, 94)])
        color = tuple(c // 2 for c in color)
        glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=max(width, height) // 10))
    img = ImageChops.add(img, glow_layer)

    # ── Layer 4: Starfield ──────────────────────────────────────────────
    draw = ImageDraw.Draw(img)
    num_stars = max(150, (width * height) // 5000)

    for _ in range(num_stars):
        sx = rng.randint(0, width - 1)
        sy = rng.randint(0, height - 1)
        brightness = rng.randint(80, 255)
        size = rng.choices([0, 1], weights=[85, 15])[0]

        if size == 0:
            draw.point((sx, sy), fill=(brightness, brightness, brightness))
        else:
            # Slightly larger star with glow
            b2 = brightness // 3
            draw.point((sx, sy), fill=(brightness, brightness, brightness))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = sx + dx, sy + dy
                if 0 <= nx < width and 0 <= ny < height:
                    draw.point((nx, ny), fill=(b2, b2, b2))

    return img


class NebulaBackground:
    """Manages a responsive deep-space background with dynamic image cross-fading."""

    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self._bg_label = None
        self._current_size = (0, 0)
        self._resize_after_id = None
        self._seed = random.randint(1, 99999)
        self.current_page = "Dashboard"
        self.current_pil_image = None
        self._transition_id = 0

        # Build absolute path to backgrounds
        self.bg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "backgrounds")

    def setup(self, container=None):
        """Create the background label and bind resize."""
        target = container or self.parent
        self._bg_label = ctk.CTkLabel(target, text="")
        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self._bg_label.lower()

        # Generate initial background
        self.parent.update_idletasks()
        w = max(self.parent.winfo_width(), 800)
        h = max(self.parent.winfo_height(), 600)
        self.parent.after(100, lambda: self._render(w, h))

        # Bind resize with debounce
        self.parent.bind("<Configure>", self._on_resize)

    def set_page_background(self, page_name: str):
        """Transition the background to the theme of the new page."""
        if page_name == self.current_page and self.current_pil_image is not None:
            return
        self.current_page = page_name
        w = max(self.parent.winfo_width(), 100)
        h = max(self.parent.winfo_height(), 100)
        self._render(w, h, force_transition=True)

    def _on_resize(self, event):
        """Debounced resize handler — regenerates background."""
        if event.widget != self.parent:
            return
        if self._resize_after_id:
            self.parent.after_cancel(self._resize_after_id)
        self._resize_after_id = self.parent.after(300, self._do_resize)

    def _do_resize(self):
        """Actually regenerate/resize the background on resize."""
        w = self.parent.winfo_width()
        h = self.parent.winfo_height()
        if (w, h) != self._current_size and w > 100 and h > 100:
            self._render(w, h)

    def _load_page_image(self, page_name: str, target_w: int, target_h: int) -> Image.Image:
        """Load the universal main background image and resize it, or fallback."""
        filepath = os.path.join(self.bg_dir, "main_bg.jpg")

        if os.path.exists(filepath):
            try:
                img = Image.open(filepath)
                # Ensure it's RGB
                if img.mode != "RGB":
                    img = img.convert("RGB")
                return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"Error loading background image {filepath}: {e}")

        # Fallback to procedural generation
        return generate_nebula_background(target_w, target_h, seed=self._seed)

    def _render(self, w: int, h: int, force_transition: bool = False):
        """Load and apply the page background with cross-fade transition."""
        self._current_size = (w, h)
        render_w = min(w, 1280)
        render_h = min(h, 720)

        # Increment transition ID to cancel previous animations
        self._transition_id += 1
        tid = self._transition_id

        def _load_and_animate():
            new_img = self._load_page_image(self.current_page, render_w, render_h)
            
            def _start_animation():
                if tid != self._transition_id:
                    return
                
                # If there's no current image or we are not forcing transition, just set it
                if self.current_pil_image is None or not force_transition:
                    self.current_pil_image = new_img
                    self._apply_image(new_img, w, h)
                    return

                # Animate cross-fade
                steps = 12
                duration_ms = 600
                step_ms = duration_ms // steps
                start_img = self.current_pil_image.copy()

                def _animate_step(step=0):
                    if tid != self._transition_id:
                        return
                    if step > steps:
                        self.current_pil_image = new_img
                        self._apply_image(new_img, w, h)
                        return
                    
                    alpha = step / steps
                    # Ease In-Out: 3t^2 - 2t^3
                    t = alpha * alpha * (3 - 2 * alpha)
                    
                    try:
                        blended = Image.blend(start_img, new_img, t)
                        self._apply_image(blended, w, h)
                    except Exception as e:
                        # Fallback in case of blend error
                        self.current_pil_image = new_img
                        self._apply_image(new_img, w, h)
                        return
                        
                    self.parent.after(step_ms, lambda: _animate_step(step + 1))

                _animate_step(0)

            # Schedule animation start on main thread
            if hasattr(self.parent, "after"):
                self.parent.after(0, _start_animation)

        threading.Thread(target=_load_and_animate, daemon=True).start()

    def _apply_image(self, pil_img: Image.Image, w: int, h: int):
        """Convert PIL image to CTkImage and apply to the background label."""
        if (pil_img.width, pil_img.height) != (w, h):
            # Scale to final window dimensions
            display_img = pil_img.resize((w, h), Image.Resampling.BILINEAR)
        else:
            display_img = pil_img

        ctk_img = ctk.CTkImage(light_image=display_img, dark_image=display_img, size=(w, h))
        if self._bg_label:
            self._bg_label.configure(image=ctk_img)
            self._bg_label._ctk_image = ctk_img  # prevent GC

    @property
    def label(self):
        return self._bg_label
