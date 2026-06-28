import customtkinter as ctk
from PIL import Image

app = ctk.CTk()
app.geometry("400x400")
app.configure(fg_color="transparent") # Test this!

img = ctk.CTkImage(Image.new("RGB", (400,400), "red"), size=(400,400))
lbl = ctk.CTkLabel(app, image=img, text="")
lbl.place(x=0, y=0, relwidth=1, relheight=1)

frame = ctk.CTkFrame(app, fg_color="transparent", border_width=5, border_color="white")
frame.place(relx=0.5, rely=0.5, relwidth=0.8, relheight=0.8, anchor="center")

lbl2 = ctk.CTkLabel(frame, text="Hello", fg_color="transparent", bg_color="transparent")
lbl2.pack(expand=True)

def capture():
    app.update()
    app.after(500, app.destroy)

app.after(1000, capture)
app.mainloop()
