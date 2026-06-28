import customtkinter as ctk
from PIL import Image

app = ctk.CTk()
app.geometry("400x400")

img = ctk.CTkImage(Image.new("RGB", (400,400), "red"), size=(400,400))
lbl = ctk.CTkLabel(app, image=img, text="")
lbl.place(x=0, y=0, relwidth=1, relheight=1)

# Put a label directly on the image label
btn = ctk.CTkLabel(lbl, text="Hello", fg_color="transparent", bg_color="transparent")
btn.place(x=200, y=200)

app.after(3000, app.destroy)
app.mainloop()
