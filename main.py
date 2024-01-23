import os
import sys
from idlelib import window
from tkinter import Tk, Canvas, PhotoImage
from tkinter.ttk import Label

from PIL import ImageTk, Image
from PIL.ImagePath import Path

from checkers.game import Game
from checkers.constants import X_SIZE, Y_SIZE, CELL_SIZE, BOARD_BORDER
from tkinter import *
from PIL import Image, ImageTk
from pathlib import Path
def resources_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
def main():

    main_window = Tk()
    main_window.title('Шашке')
    main_window.resizable(0, 0)
    main_window.iconphoto(False, PhotoImage(file=resources_path("icon.png")))
    # Создание холста
    main_canvas = Canvas(main_window, width=(CELL_SIZE * X_SIZE) + BOARD_BORDER*2, height=(CELL_SIZE * Y_SIZE) + BOARD_BORDER*2)
    main_canvas.pack()
    game = Game(main_canvas, X_SIZE, Y_SIZE)
    main_canvas.bind("<Motion>", game.mouse_move)
    main_canvas.bind("<Button-1>", game.mouse_down)
    main_window.mainloop()

if __name__ == '__main__':
    main()
