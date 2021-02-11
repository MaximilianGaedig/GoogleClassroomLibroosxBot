import tkinter
from PIL import Image, ImageTk

root = tkinter.Tk()
root.iconbitmap('classroom.ico')
canvas = tkinter.Canvas(root, width=600, height=300)
canvas.grid(columnspan=3)
logo = ImageTk.PhotoImage(Image.open("classroom.svg"))
logo_label = tkinter.Label(image=logo)
logo_label.image = logo
logo_label.grid(column=1, row=0)
instructions = tkinter.Label(root, text="test")
instructions.grid(columnspan=3, column=0, row=1)
btn_text = tkinter.StringVar()
btn_test = tkinter.Button(root, textvariable=btn_text, command=lambda:print("hi"), width=30, height=30)
btn_test.grid(column=1, row=1)
root.mainloop()
