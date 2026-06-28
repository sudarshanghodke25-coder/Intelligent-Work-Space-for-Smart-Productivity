import customtkinter as ctk
from PIL import Image

app = ctk.CTk()
app.geometry("400x400")
img = ctk.CTkImage(Image.new("RGB", (400,400), "red"), size=(400,400))
lbl = ctk.CTkLabel(app, image=img, text="")
lbl.place(x=0, y=0)
frame = ctk.CTkFrame(lbl, fg_color="transparent", width=200, height=200, border_width=2, border_color="white")
frame.place(x=100, y=100)
app.after(2000, app.destroy)
app.mainloop()
