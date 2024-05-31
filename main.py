import os
import sys
from tkinter import Tk, Canvas, PhotoImage, ttk
from PIL import ImageTk, Image, ImageSequence
from PIL.ImagePath import Path
from checkers.constants import X_SIZE, Y_SIZE
from tkinter import *
from PIL import Image, ImageTk
from checkers import constants
import customtkinter

from checkers.game import Game


def resources_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def update_max_depth(new_depth):
    global constants
    constants.MAX_DEPTH['value'] = new_depth

def update_timer(difficulty):
    global constants
    constants.TIMER['value'] = difficulty

def change_mode(mode):
    global constants
    if constants.MULTIPLAYER['value'] == 0.0:
        constants.MULTIPLAYER['value'] = mode
        #print(constants.MULTIPLAYER['value'])
    if constants.MULTIPLAYER['value'] == 1.0:
        constants.MULTIPLAYER['value'] = mode
        #print(constants.MULTIPLAYER['value'])


class CustomScale(ttk.Scale):
    def __init__(self, master=None, **kw):
        kw.setdefault("orient", "horizontal")
        kw.setdefault("from_", 1)
        kw.setdefault("to", 3)
        self.variable = kw.pop('variable', DoubleVar(master))
        self.variable.set(self.get_initial_value())
        ttk.Scale.__init__(self, master, variable=self.variable, **kw)
        self._style_name = '{}.custom.{}.TScale'.format(self, kw['orient'].capitalize())
        self['style'] = self._style_name
        self.last_pos = self.variable.get()
        self.dragging = False
        self.bind("<B1-Motion>", self.change_cursor)
        self.bind("<ButtonRelease-1>", self.set_to_nearest)
        self.bind("<B3-Motion>", self.change_cursor)
        self.bind("<ButtonRelease-3>", self.set_to_nearest)

    def get_initial_value(self):
        depth = constants.MAX_DEPTH['value']
        if depth <= 1.0:
            return 1
        elif depth <= 3.0:
            return 2
        else:
            return 3

    def change_cursor(self, event):
        self.config(cursor="star")

    def set_to_nearest(self, event):
        positions = [1, 2, 3]
        current_value = self.variable.get()
        closest_position = min(positions, key=lambda x: abs(x - current_value))
        self.variable.set(closest_position)
        self.dragging = False

        if self.variable.get() == 1:
            update_max_depth(1.0)
            update_timer(180)
        elif self.variable.get() == 2:
            update_max_depth(3.0)
            update_timer(120)
        elif self.variable.get() == 3:
            update_max_depth(5.0)
            update_timer(90)
        self.config(cursor="hand2")


def show_menu(main_window, canvas_width, canvas_height, menu_canvas, main_canvas):
    main_canvas.pack_forget()
    menu_canvas.pack()


def hide_menu(menu_canvas, main_canvas):
    menu_canvas.pack_forget()
    main_canvas.pack()


def start_game(main_canvas, menu_canvas, main_window):
    main_canvas.pack()
    game = Game(main_canvas, X_SIZE, Y_SIZE, main_window, menu_canvas)
    main_canvas.bind("<Motion>", game.mouse_move)
    main_canvas.bind("<Button-1>", game.mouse_down)
    menu_canvas.pack_forget()


def main():
    main_window = customtkinter.CTk()
    icon_path = resources_path('assets\\white-queen.ico')
    main_window.iconbitmap(icon_path)
    main_window.title('Шашки')
    main_window.resizable(0, 0)
    mod_table_image = None
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
    start_button_image = PhotoImage(
        file=resources_path('assets//play.png'))
    start_button = Button(main_window, image=start_button_image,
                          command=lambda: start_game(main_canvas, menu_canvas, main_window),
                          borderwidth=0,
                          highlightthickness=0,
                          bg='#0099DD', activebackground='#0099DD',
                          cursor='hand2')
    start_button.image = start_button_image  # Сохраняем ссылку на изображение, чтобы оно отображалось
    start_button_window = menu_canvas.create_window(canvas_width / 2, canvas_height / 2 + 100, window=start_button)
    difficulty_image = PhotoImage(file=resources_path('assets/difficulty_table.png'))
    difficulty = menu_canvas.create_image(canvas_width - 150, canvas_height / 2 + button_height + 150,
                                          image=difficulty_image)
    track_image = PhotoImage(file=resources_path('assets/track.png'))  # Укажите путь к изображению трека
    handle_image = PhotoImage(file=resources_path('assets/handle.png'))  # Укажите путь к изображению ручки
    style = ttk.Style(main_window)
    style.element_create('custom.Scale.trough', 'image', track_image)
    style.element_create('custom.Scale.slider', 'image', handle_image)
    style.layout('custom.Horizontal.TScale',
                 [('custom.Scale.trough', {'sticky': 'we'}),
                  ('custom.Scale.slider', {'side': 'left', 'sticky': ''})])
    style.configure('custom.Horizontal.TScale', background='#EDAB50')
    scale1 = CustomScale(main_window, from_=1, to=3, orient='horizontal', cursor='hand2')
    scale1_window = menu_canvas.create_window(canvas_width - 150, canvas_height / 2 + button_height + 163,
                                              window=scale1)
    mode_image = PhotoImage(file=resources_path('assets//mode.png'))

    def show_extended(mod_table_image):
        mod_tab = menu_canvas.create_image(31, canvas_height / 2 + button_height + 25, image=mod_table_image,
                                           anchor='nw')
        mode_button.destroy()
        mode = ""
        radio_unchecked1 = PhotoImage(file=resources_path("assets/checked.png"))  # Изображение для неотмеченной радиокнопки
        radio_unchecked2 = PhotoImage(file=resources_path("assets/unchecked.png"))

        def active():
            #print(constants.MULTIPLAYER['value'])
            radio_unchecked2.configure(file=resources_path('assets/checked.png'))
            radio_unchecked1.configure(file=resources_path('assets/unchecked.png'))
            radiobtn1.configure(command=inactive)
            change_mode(1.0)
            radiobtn2.configure(command=active)

        def inactive():
            #print(constants.MULTIPLAYER['value'])
            radio_unchecked2.configure(file=resources_path('assets/unchecked.png'))
            radio_unchecked1.configure(file=resources_path('assets/checked.png'))
            radiobtn2.configure(command=active)
            change_mode(0.0)
            radiobtn1.configure(command=inactive)
        radiobtn1 = Button(menu_canvas, image=radio_unchecked1, border=0, command=inactive)
        radiobtn2 = Button(menu_canvas, image=radio_unchecked2, border=0, command=active)
        radiobtn1.configure(background='#EDAB50', activebackground='#EDAB50', cursor='hand2')
        radiobtn2.configure(background='#EDAB50', activebackground='#EDAB50', cursor='hand2')
        radiobtn1.place(x=51, y=canvas_height / 2 + button_height + 150)
        radiobtn2.place(x=51, y=canvas_height / 2 + button_height + 200)

    mod_table_image = PhotoImage(file=resources_path('assets/mode_table.png'))
    mode_button = Button(main_window, image=mode_image,
                         command=lambda: show_extended(mod_table_image), borderwidth=0,
                         highlightthickness=0,
                         bg='#0099DD', activebackground='#0099DD',
                         cursor='hand2')
    mode_button_window = menu_canvas.create_window(150, canvas_height / 2 + button_height + 150, window=mode_button)
    exit_button_image = PhotoImage(file=resources_path('assets//exit.png'))

    exit_button = Button(main_window, image=exit_button_image, command=main_window.quit, borderwidth=0,
                         highlightthickness=0,
                         bg='#0099DD', activebackground='#0099DD',
                         cursor='hand2')
    exit_button.image = exit_button_image
    exit_button_window = menu_canvas.create_window(canvas_width / 2, canvas_height / 2 + button_height + 200,
                                                   window=exit_button)

    main_window.mainloop()


if __name__ == '__main__':
    main()
