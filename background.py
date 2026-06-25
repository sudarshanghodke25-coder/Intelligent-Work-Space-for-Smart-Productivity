"""
Aurex Background Generator — Dynamic deep-space nebula with starfield.
Uses Pillow to generate a cosmic background image at runtime.
"""

import random
import math
import threading
from PIL import Image, ImageDraw, ImageFilter
import customtkinter as ctk


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
    top_color = (12, 10, 32)
    mid_color = (10, 8, 28)
    bot_color = (6, 6, 18)

    for y in range(height):
        t = y / max(height - 1, 1)
        if t < 0.5:
            c = _lerp_color(top_color, mid_color, t * 2)
        else:
            c = _lerp_color(mid_color, bot_color, (t - 0.5) * 2)
        draw.line([(0, y), (width, y)], fill=c)

    # ── Layer 2: Nebula glow blobs ──────────────────────────────────────
    nebula_colors = [
        (80, 20, 120),    # cosmic purple
        (20, 30, 100),    # deep blue
        (100, 40, 15),    # muted orange
        (30, 50, 110),    # blue-teal
        (90, 15, 70),     # magenta
        (15, 40, 90),     # navy
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
        color = rng.choice([(60, 30, 90), (30, 40, 80), (70, 25, 10)])
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
    """Manages a responsive nebula background for a CTk window."""

    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self._bg_label = None
        self._current_size = (0, 0)
        self._resize_after_id = None
        self._seed = random.randint(1, 99999)

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
        self._render(w, h)

        # Bind resize with debounce
        self.parent.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """Debounced resize handler — regenerates background."""
        if event.widget != self.parent:
            return
        if self._resize_after_id:
            self.parent.after_cancel(self._resize_after_id)
        self._resize_after_id = self.parent.after(500, self._do_resize)

    def _do_resize(self):
        """Actually regenerate the background on resize."""
        w = self.parent.winfo_width()
        h = self.parent.winfo_height()
        if (w, h) != self._current_size and w > 100 and h > 100:
            self._render(w, h)

    def _render(self, w: int, h: int):
        """Generate and apply the background image in a separate thread."""
        self._current_size = (w, h)
        
        def _generate_and_apply():
            img = generate_nebula_background(w, h, seed=self._seed)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
            
            def _apply():
                if self._bg_label:
                    self._bg_label.configure(image=ctk_img)
                    self._bg_label._ctk_image = ctk_img  # prevent GC
            
            # Schedule UI update on main thread
            if hasattr(self.parent, "after"):
                self.parent.after(0, _apply)
        
        threading.Thread(target=_generate_and_apply, daemon=True).start()

    @property
    def label(self):
        return self._bg_label
