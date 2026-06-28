import customtkinter as ctk
from PIL import Image, ImageGrab

app = ctk.CTk()
app.geometry("400x400")

# Red background image
img = ctk.CTkImage(Image.new("RGB", (400,400), "red"), size=(400,400))
lbl = ctk.CTkLabel(app, image=img, text="")
lbl.place(x=0, y=0, relwidth=1, relheight=1)

# Make lbl the MASTER
frame = ctk.CTkFrame(lbl, fg_color="transparent", border_width=5, border_color="white")
frame.place(relx=0.5, rely=0.5, relwidth=0.8, relheight=0.8, anchor="center")

def capture():
    app.update()
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    ImageGrab.grab(bbox=(x, y, x+400, y+400)).save("d:/Aurex/test_screenshot.png")
    app.after(500, app.destroy)

app.after(1000, capture)
app.mainloop()
