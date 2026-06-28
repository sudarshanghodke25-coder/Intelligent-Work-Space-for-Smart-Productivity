import sys
import customtkinter as ctk

app = ctk.CTk()
app.geometry("400x400")

# Apply monkey patch
def fast_scroll(self, event):
    if self.check_if_master_is_canvas(event.widget):
        if sys.platform in ["apple", "darwin"]:
            self._parent_canvas.yview("scroll", int(-1 * (event.delta)), "units")
        else:
            self._parent_canvas.yview("scroll", int(-1 * (event.delta / 120) * 4), "units")
            
ctk.CTkScrollableFrame._mouse_wheel_all = fast_scroll

sf = ctk.CTkScrollableFrame(app)
sf.pack(fill="both", expand=True)

for i in range(100):
    ctk.CTkLabel(sf, text=f"Item {i}").pack(pady=10)

print("Patch applied successfully")
