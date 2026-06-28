import customtkinter as ctk

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*[int(x) for x in rgb])

def interpolate_color(color1, color2, factor):
    """Interpolate between two hex colors. factor is 0.0 to 1.0."""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    new_rgb = (
        rgb1[0] + (rgb2[0] - rgb1[0]) * factor,
        rgb1[1] + (rgb2[1] - rgb1[1]) * factor,
        rgb1[2] + (rgb2[2] - rgb1[2]) * factor
    )
    return rgb_to_hex(new_rgb)

def resolve_color(color):
    if isinstance(color, (tuple, list)):
        mode = ctk.get_appearance_mode()
        return color[1] if mode == "Dark" else color[0]
    return color

def animate_color(widget, property_name, start_color, end_color, steps=8, delay=5):
    """
    Animates a color property of a CustomTkinter widget.
    property_name can be 'fg_color', 'border_color', 'text_color'.
    """
    if not widget.winfo_exists(): return
    
    start_c = resolve_color(start_color)
    end_c = resolve_color(end_color)
    
    def step_animation(current_step):
        if not widget.winfo_exists(): return
        
        if current_step >= steps:
            # Re-apply the original tuple so it stays dynamic to theme switches
            widget.configure(**{property_name: end_color})
            return
            
        factor = current_step / float(steps)
        current_color = interpolate_color(start_c, end_c, factor)
        widget.configure(**{property_name: current_color})
        
        widget.after(delay, step_animation, current_step + 1)
            
    step_animation(1)

def apply_hover_animation(widget, property_name, normal_color, hover_color):
    """Binds hover events to smoothly animate a widget's color."""
    widget.bind("<Enter>", lambda e: animate_color(widget, property_name, normal_color, hover_color), add="+")
    widget.bind("<Leave>", lambda e: animate_color(widget, property_name, hover_color, normal_color), add="+")
