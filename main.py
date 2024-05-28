import os
import sys
from tkinter import Tk, Canvas, PhotoImage, Button
from PIL import ImageTk, Image, ImageSequence
import customtkinter

def resources_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def show_menu(main_window, canvas_width, canvas_height, menu_canvas, main_canvas):
    main_canvas.pack_forget()
    menu_canvas.pack()

def hide_menu(menu_canvas, main_canvas):
    menu_canvas.pack_forget()
    main_canvas.pack()

def start_game(main_canvas, menu_canvas, main_window):
    main_canvas.pack()
    menu_canvas.pack_forget()

def main():
    main_window = customtkinter.CTk()
    icon_path = resources_path('assets\\white-queen.ico')
    main_window.iconbitmap(icon_path)
    main_window.title('Шашки')
    main_window.resizable(0, 0)

    canvas_width = 800
    canvas_height = 800
    main_canvas = Canvas(main_window, width=canvas_width, height=canvas_height, highlightthickness=0, bd=0)
    menu_canvas = Canvas(main_window, width=canvas_width, height=canvas_height, highlightthickness=0, bd=0)

    menu_canvas.pack()
    gif_image = Image.open(resources_path('assets\\main_menu-min.gif'))
    gif_frames = [ImageTk.PhotoImage(frame.convert("RGBA")) for frame in ImageSequence.Iterator(gif_image)]
    current_frame = 0
    gif_item = menu_canvas.create_image(0, 0, image=gif_frames[current_frame], anchor='nw')

    def update_gif():
        nonlocal current_frame
        current_frame = (current_frame + 1) % len(gif_frames)
        menu_canvas.itemconfig(gif_item, image=gif_frames[current_frame])
        menu_canvas.after(100, update_gif)

    update_gif()
    button_width = 100
    button_height = 30
    start_button_image = PhotoImage(file=resources_path('assets//play.png'))
    start_button = Button(main_window, image=start_button_image, command=lambda: start_game(main_canvas, menu_canvas, main_window),
                          borderwidth=0, highlightthickness=0, bg='#0099DD', activebackground='#0099DD',
                          cursor='hand2')
    start_button.image = start_button_image
    start_button_window = menu_canvas.create_window(canvas_width / 2, canvas_height / 2 + 100, window=start_button)

    exit_button_image = PhotoImage(file=resources_path('assets//exit.png'))
    exit_button = Button(main_window, image=exit_button_image, command=main_window.quit, borderwidth=0,
                         highlightthickness=0, bg='#0099DD', activebackground='#0099DD', cursor='hand2')
    exit_button.image = exit_button_image
    exit_button_window = menu_canvas.create_window(canvas_width / 2, canvas_height / 2 + button_height + 200, window=exit_button)

    main_window.mainloop()

if __name__ == '__main__':
    main()
