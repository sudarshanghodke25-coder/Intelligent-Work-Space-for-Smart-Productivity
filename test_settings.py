import customtkinter as ctk
from ui.settings import SettingsView
import traceback

app = ctk.CTk()
app.geometry("800x600")

try:
    sv = SettingsView(app)
    sv.pack(fill="both", expand=True)
    print("SettingsView packed successfully")
except Exception as e:
    print("ERROR INSTANTIATING SettingsView:")
    traceback.print_exc()
    
# app.mainloop() # don't loop so we can see output immediately
