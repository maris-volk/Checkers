import os
import random
import sys
import logging
import time
import tkinter
from tkinter import Canvas, Event, messagebox, Label, Button, Toplevel
from random import choice
from time import sleep
from math import inf
import customtkinter
from PIL import Image, ImageTk, ImageSequence
from checkers.field import Field
from checkers.move import Move
from checkers.constants import *
from checkers.enums import CheckerType, SideType
from checkers.point import Point
from threading import Thread


def resources_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


logger = logging.getLogger('my_logger')
logger.addHandler(logging.NullHandler())


def function_with_logging():
    time.sleep(0)


class Game:
    def __init__(self, canvas, x_field_size, y_field_size, main_window, menu_canvas):
        self.__current_player = SideType.WHITE if MULTIPLAYER['value'] == 1.0 else PLAYER_SIDE
        self.running = True
        self.digits_player_images = []
        for i in range(10):
            image_path = f"assets/{i}.png"
            image = Image.open(resources_path(image_path))
            self.digits_player_images.append(ImageTk.PhotoImage(image))
        self.digits_opponent_images = []
        for i in range(10):
            image_path = f"assets/{i}opponent.png"
            image = Image.open(resources_path(image_path))
            self.digits_opponent_images.append(ImageTk.PhotoImage(image))
        self.selected_if_has_killed = []
        self.in_main = False
        self.in_thread = False
        self.calc = False
        self.timer_sleep = False
        self.timer_player = int(TIMER['value'])
        self.timer_opponent = int(TIMER['value'])
        self.optimal_moves_list = []
        self.__hover_animation_in_progress = False
        self.__gif_select_item = None
        self.__gif_hover_item = None
        self.__buffered_state = None
        self.test_field = Field(x_field_size, y_field_size)
        self.__animation_in_progress = False
        self.menu_canvas = menu_canvas
        self.main_window = main_window
        self.__canvas = canvas
        self.__init_images()
        self.background = None
        self.__create_background()
        self.star_timer_values = self.seconds_to_list(int(TIMER['value']))
        self.PlayerTimer1 = self.__canvas.create_image(636, 752, image=self.digits_player_images[self.star_timer_values[0]])
        self.PlayerTimer2 = self.__canvas.create_image(682, 752, image=self.digits_player_images[self.star_timer_values[1]])
        self.PlayerTimer3 = self.__canvas.create_image(723, 752, image=self.digits_player_images[0])
        self.OpponentTimer1 = self.__canvas.create_image(65, 52, image=self.digits_opponent_images[self.star_timer_values[0]])
        self.OpponentTimer2 = self.__canvas.create_image(111, 52, image=self.digits_opponent_images[self.star_timer_values[1]])
        self.OpponentTimer3 = self.__canvas.create_image(152, 52, image=self.digits_opponent_images[0])
        self.game_over = False
        self.child_window = tkinter.Widget
        self.__field = Field(x_field_size, y_field_size)
        self.__player_turn = True
        self.ok_not_clicked = True
        self.__hovered_cell = Point()
        self.__selected_cell = Point()
        self.__animated_cell = Point()
        self.timer_player_run = True
        self.timer_opponent_run = False
        self.timer_start = False
        self.timer_value_of_enemy_turn_start = 0
        self.first_move_is_kill = False
        self.__draw()
        self.__gif_select_started = False
        self.__gif_hover_started = False
        self.__init_menu_button()


    def seconds_to_list(self, seconds):
        minutes = seconds // 60
        tens_seconds = (seconds % 60) // 10
        units_seconds = (seconds % 60) % 10
        return [int(minutes), int(tens_seconds), int(units_seconds)]

    def update_opponent_timer(self):
        if not self.running:
            return

        if (MULTIPLAYER['value'] == 1.0 and (self.__current_player == SideType.WHITE)) or (MULTIPLAYER['value'] == 0.0 and self.__player_turn ):
            if self.timer_player_run:
                return
            self.timer_player_run = True
            self.timer_opponent_run = False
            self.update_player_timer()
            return

        if not self.timer_opponent_run:
            return

        self.timer_opponent = self.timer_opponent - 1
        digits = self.seconds_to_list(self.timer_opponent)
        self.__canvas.itemconfig(self.OpponentTimer1, image=self.digits_opponent_images[digits[0]])
        self.__canvas.itemconfig(self.OpponentTimer2, image=self.digits_opponent_images[digits[1]])
        self.__canvas.itemconfig(self.OpponentTimer3, image=self.digits_opponent_images[digits[2]])
        if self.timer_opponent > 0:
            self.__canvas.after(1000, self.update_opponent_timer)
        else:
            self.__check_for_game_over()

    def update_player_timer(self):
        if not self.timer_player_run:
            return
        if self.timer_opponent_run:
            return
        if not self.running:
            return
        if (MULTIPLAYER['value'] == 1.0 and self.__current_player == SideType.BLACK) or (MULTIPLAYER['value'] == 0.0 and not self.__player_turn and not self.timer_sleep):
            if self.timer_opponent_run:
                return
            self.timer_player_run = False
            self.timer_opponent_run = True
            self.update_opponent_timer()
            return
        if not self.timer_player_run:
            return
        self.timer_player = self.timer_player - 1
        digits = self.seconds_to_list(self.timer_player)
        if self.timer_opponent_run:
            return
        self.__canvas.itemconfig(self.PlayerTimer1, image=self.digits_player_images[digits[0]])
        self.__canvas.itemconfig(self.PlayerTimer2, image=self.digits_player_images[digits[1]])
        self.__canvas.itemconfig(self.PlayerTimer3, image=self.digits_player_images[digits[2]])
        if self.timer_player > 0:
            self.__canvas.update()
            self.__canvas.after(1000, self.update_player_timer)
        else:
            self.__check_for_game_over()

    def return_to_main_menu(self):
        self.running = False
        self.timer_start = False
        self.timer_player = int(TIMER['value'])
        self.timer_opponent = int(TIMER['value'])

        self.__canvas.pack_forget()
        from main import main
        self.menu_canvas.pack()

    def __init_menu_button(self):
        exit_to_menu_image = ImageTk.PhotoImage(Image.open(resources_path('assets//exit_to_menu.png')))
        exit_to_menu_button = Button(self.__canvas, image=exit_to_menu_image,
                                     command=self.return_to_main_menu,
                                     borderwidth=0, highlightthickness=0,
                                     bg='#5D2C28', activebackground='#5D2C28',
                                     cursor='hand2',
                                     takefocus=False)
        exit_to_menu_button.image = exit_to_menu_image
        exit_to_menu_button.place(x=((BOARD_BORDER * 1.3 + CELL_SIZE * 8) - 1), y=8)

    def __init_images(self):
        self.__aim_image = ImageTk.PhotoImage(Image.open(resources_path('assets\\aim.png')).convert("RGBA"))
        self.__gif_select_image = Image.open(resources_path('assets\\select1.gif'))
        self.__gif_select_frames = []
        for frame in ImageSequence.Iterator(self.__gif_select_image):
            frame = frame.convert("RGBA")
            self.__gif_select_frames.append(ImageTk.PhotoImage(frame))
        self.__current_gif_select_frame = 0
        self.__gif_hover_image = Image.open(resources_path('assets\\select.gif'))
        self.__gif_hover_frames = []
        for frame_1 in ImageSequence.Iterator(self.__gif_hover_image):
            frame = frame_1.convert("RGBA")
            self.__gif_hover_frames.append(ImageTk.PhotoImage(frame))
        self.__current_gif_hover_frame = 0
        self.__images = {
            CheckerType.WHITE_REGULAR: ImageTk.PhotoImage(
                Image.open(resources_path('assets\\white-regular.png')).resize((CELL_SIZE - 2, CELL_SIZE - 2),
                                                                               Image.Resampling.LANCZOS)),
            CheckerType.BLACK_REGULAR: ImageTk.PhotoImage(
                Image.open(resources_path('assets\\black-regular.png')).resize((CELL_SIZE - 2, CELL_SIZE - 2),
                                                                               Image.Resampling.LANCZOS)),
            CheckerType.WHITE_QUEEN: ImageTk.PhotoImage(
                Image.open(resources_path('assets\\white-queen.png')).resize((CELL_SIZE - 2, CELL_SIZE - 2),
                                                                             Image.Resampling.LANCZOS)),
            CheckerType.BLACK_QUEEN: ImageTk.PhotoImage(
                Image.open(resources_path('assets\\black-queen.png')).resize((CELL_SIZE - 2, CELL_SIZE - 2),
                                                                             Image.Resampling.LANCZOS)),
            CheckerType.BOARD_BACKGROUND: ImageTk.PhotoImage(
                Image.open(resources_path('assets\\board.png')).resize((800, 800), Image.Resampling.LANCZOS)),

        }
    def __update_select_gif(self):

        self.__current_gif_select_frame = (self.__current_gif_select_frame + 1) % len(self.__gif_select_frames)
        self.__canvas.itemconfig(self.__gif_select_item,
                                 image=self.__gif_select_frames[self.__current_gif_select_frame])
        self.__canvas.after(150, self.__update_select_gif)

    def __update_hover_gif(self):

        self.__hover_animation_in_progress = True
        self.__current_gif_hover_frame = (self.__current_gif_hover_frame + 1) % len(self.__gif_hover_frames)
        self.__canvas.itemconfig(self.__gif_hover_item,
                                 image=self.__gif_hover_frames[self.__current_gif_hover_frame])
        self.__canvas.after(150, self.__update_hover_gif)

    def __animate_move(self, move: Move):
        self.__animated_cell = Point(move.from_x, move.from_y)
        self.__animation_in_progress = True
        self.__draw()
        animated_checker = self.__canvas.create_image((move.from_x * CELL_SIZE) + BOARD_BORDER,
                                                      (move.from_y * CELL_SIZE) + BOARD_BORDER, image=self.__images.get(
                self.__field.type_at(move.from_x, move.from_y)), anchor='nw', tag='animated_checker')
        self.selected_if_has_killed = [move.to_x, move.to_y]
        dx = 1 if move.from_x < move.to_x else -1
        dy = 1 if move.from_y < move.to_y else -1
        for distance in range(abs(move.from_x - move.to_x)):
            for _ in range(100 // ANIMATION_SPEED):
                self.__canvas.move(animated_checker, ANIMATION_SPEED / 100 * CELL_SIZE * dx,
                                   ANIMATION_SPEED / 100 * CELL_SIZE * dy)
                self.__canvas.update()
                sleep(0.01)

        self.__animated_cell = Point()
        self.__selected_cell = Point()
        self.__animation_in_progress = False

    def __draw(self):
        '''Отрисовка сетки поля и шашек'''
        elements_to_keep = [self.PlayerTimer1,
                            self.PlayerTimer2,
                            self.PlayerTimer3,
                            self.OpponentTimer1,
                            self.OpponentTimer2,
                            self.OpponentTimer3,
                            self.background]
        all_elements = self.__canvas.find_all()
        elements_to_delete = [element for element in all_elements if
                              element not in elements_to_keep]
        for element in elements_to_delete:
            self.__canvas.delete(element)

        self.__draw_field_grid()
        self.__draw_checkers()

    def __create_background(self):
        background_image = self.__images.get(CheckerType.BOARD_BACKGROUND)
        self.background = self.__canvas.create_image(0, 0, image=background_image, anchor='nw', tag='background')

    def __draw_field_grid(self):
        '''Отрисовка сетки поля'''
        for y in range(self.__field.y_size):
            for x in range(self.__field.x_size):
                if (x == self.__selected_cell.x and y == self.__selected_cell.y):
                    self.__gif_select_item = self.__canvas.create_image((x * CELL_SIZE + BOARD_BORDER),
                                                                        (y * CELL_SIZE + BOARD_BORDER),
                                                                        image=self.__gif_select_frames[
                                                                            self.__current_gif_select_frame],
                                                                        anchor='nw')
                    if not self.__gif_select_started:
                        self.__gif_select_started = True
                        self.__update_select_gif()
                elif (x == self.__hovered_cell.x and y == self.__hovered_cell.y):
                    self.__gif_hover_item = self.__canvas.create_image((x * CELL_SIZE + BOARD_BORDER),
                                                                       (y * CELL_SIZE + BOARD_BORDER),
                                                                       image=self.__gif_hover_frames[
                                                                           self.__current_gif_hover_frame],
                                                                       anchor='nw')
                    if not self.__gif_hover_started:
                        self.__gif_hover_started = True
                        self.__update_hover_gif()

        if self.__selected_cell:
            if MULTIPLAYER['value'] == 1.0:
                player_moves_list = self.__get_moves_list(self.__current_player)
            else:
                player_moves_list = self.__get_moves_list(PLAYER_SIDE)
            valid_moves_list = []

            for move in player_moves_list:
                if (self.__selected_cell.x == move.from_x and self.__selected_cell.y == move.from_y):
                    valid_moves_list.append(move)

            for move in valid_moves_list:
                self.__canvas.create_image(move.to_x * CELL_SIZE + BOARD_BORDER,
                                           move.to_y * CELL_SIZE + BOARD_BORDER, image=self.__aim_image, anchor='nw')

    def __draw_checkers(self):
        '''Отрисовка шашек'''
        for y in range(self.__field.y_size):
            for x in range(self.__field.x_size):
                if (self.__field.type_at(x, y) != CheckerType.NONE and not (
                        x == self.__animated_cell.x and y == self.__animated_cell.y)):
                    self.__canvas.create_image(((x * CELL_SIZE) + BOARD_BORDER) + 1,
                                               ((y * CELL_SIZE) + BOARD_BORDER) + 1,
                                               image=self.__images.get(self.__field.type_at(x, y)), anchor='nw',
                                               tag='checkers')

    def hover_test(self, x, y):
        if self.__gif_select_item:
            self.__canvas.delete(self.__gif_select_item)
            self.__gif_select_item = None
        if self.__gif_hover_item:
            self.__canvas.delete(self.__gif_hover_item)
            self.__gif_hover_item = None

        self.__hovered_cell = Point(x, y)
        self.__gif_hover_item = self.__canvas.create_image(
            (x * CELL_SIZE + BOARD_BORDER),
            (y * CELL_SIZE + BOARD_BORDER),
            image=self.__gif_hover_frames[self.__current_gif_hover_frame],
            anchor='nw'
        )

        if not self.__gif_hover_started:
            self.__gif_hover_started = True
            self.__update_hover_gif()

    def mouse_move(self, event: Event):
        x, y = (event.x - BOARD_BORDER) // CELL_SIZE, (event.y - BOARD_BORDER) // CELL_SIZE
        if (x != self.__hovered_cell.x or y != self.__hovered_cell.y) and (x >= 0 and x < self.__field.x_size) and (
                y >= 0 and y < self.__field.y_size):
            if not self.timer_start:
                self.timer_start = True
                self.update_player_timer()
            self.__hovered_cell = Point(x, y)
            if MULTIPLAYER['value'] == 1.0:
                if not self.__animation_in_progress:
                    self.__draw()
                else:
                    self.hover_test(x, y)
            elif not MULTIPLAYER['value'] == 1.0:
                if not self.__animation_in_progress and not self.calc:
                    self.in_main = True
                    self.__draw()
                    self.in_main = False
                else:
                    self.hover_test(x, y)

    def mouse_down(self, event: Event):
        if self.__animation_in_progress:
            return
        x, y = (event.x - BOARD_BORDER) // CELL_SIZE, (event.y - BOARD_BORDER) // CELL_SIZE
        if not (self.__field.is_within(x, y)): return

        if MULTIPLAYER['value'] == 1.0:

            if (self.__current_player == SideType.WHITE):
                player_checkers = WHITE_CHECKERS
            elif (self.__current_player == SideType.BLACK):
                player_checkers = BLACK_CHECKERS
            else:
                return

            if (self.__field.type_at(x, y) in player_checkers):
                self.__selected_cell = Point(x, y)
                self.__draw()
            elif (self.__player_turn):
                move = Move(self.__selected_cell.x, self.__selected_cell.y, x, y)
                if (move in self.__get_moves_list(self.__current_player)):
                    self.__handle_player_turn(move)
                    if not (self.__player_turn):
                        if (self.__current_player == SideType.WHITE):
                            self.__current_player = SideType.BLACK
                        elif (self.__current_player == SideType.BLACK):
                            self.__current_player = SideType.WHITE
                        self.__check_for_game_over()
                        self.update_player_timer()
                        self.__player_turn = True
        else:
            if not (self.__player_turn): return

            if (PLAYER_SIDE == SideType.WHITE):
                player_checkers = WHITE_CHECKERS
            elif (PLAYER_SIDE == SideType.BLACK):
                player_checkers = BLACK_CHECKERS
            else:
                return

            if (self.__field.type_at(x, y) in player_checkers):
                self.__selected_cell = Point(x, y)
                self.__draw()
            elif (self.__player_turn):
                move = Move(self.__selected_cell.x, self.__selected_cell.y, x, y)
                if (move in self.__get_moves_list(PLAYER_SIDE)):
                    self.__handle_player_turn(move)
                    if not (self.__player_turn):
                        self.timer_value_of_enemy_turn_start = self.timer_opponent
                        self.test_field = self.__field
                        thread_calc = self.handle_enemy_turn_calc_async()
                        while thread_calc.is_alive():
                            self.__canvas.update()
                        moves = self.optimal_moves_list
                        if MAX_DEPTH['value'] != 5:
                            if not moves:
                                self.simulate_thinking(game_over=True)
                            else:
                                self.simulate_thinking()
                        self.first_move_is_kill = False
                        self.__handle_enemy_turn(moves)

    def __handle_move(self, move: Move, field_for_check: Field = None, draw: bool = True) -> bool:
        function_with_logging()
        global has_killed_checker
        if MULTIPLAYER['value'] == 1.0:
            if (draw): self.__animate_move(move)
            if (move.to_y == 0 and self.__field.type_at(move.from_x, move.from_y) == CheckerType.WHITE_REGULAR):
                self.__field.at(move.from_x, move.from_y).change_type(CheckerType.WHITE_QUEEN)
            elif (move.to_y == self.__field.y_size - 1 and self.__field.type_at(move.from_x,
                                                                                move.from_y) == CheckerType.BLACK_REGULAR):
                self.__field.at(move.from_x, move.from_y).change_type(CheckerType.BLACK_QUEEN)
            self.__field.at(move.to_x, move.to_y).change_type(self.__field.type_at(move.from_x, move.from_y))
            self.__field.at(move.from_x, move.from_y).change_type(CheckerType.NONE)
            dx = -1 if move.from_x < move.to_x else 1
            dy = -1 if move.from_y < move.to_y else 1
            has_killed_checker = False
            x, y = move.to_x, move.to_y
            while (x != move.from_x or y != move.from_y):
                x += dx
                y += dy
                if (self.__field.type_at(x, y) != CheckerType.NONE):
                    self.__field.at(x, y).change_type(CheckerType.NONE)
                    has_killed_checker = True

            if (draw): self.__draw()
        elif not MULTIPLAYER['value'] == 1.0:
            if self.calc:
                if (draw): self.__animate_move(move)
                if (move.to_y == 0 and self.test_field.type_at(move.from_x, move.from_y) == CheckerType.WHITE_REGULAR):
                    self.test_field.at(move.from_x, move.from_y).change_type(CheckerType.WHITE_QUEEN)
                elif (move.to_y == self.test_field.y_size - 1 and self.test_field.type_at(move.from_x,
                                                                                          move.from_y) == CheckerType.BLACK_REGULAR):
                    self.test_field.at(move.from_x, move.from_y).change_type(CheckerType.BLACK_QUEEN)
                self.test_field.at(move.to_x, move.to_y).change_type(self.test_field.type_at(move.from_x, move.from_y))
                self.test_field.at(move.from_x, move.from_y).change_type(CheckerType.NONE)
                dx = -1 if move.from_x < move.to_x else 1
                dy = -1 if move.from_y < move.to_y else 1
                has_killed_checker = False
                x, y = move.to_x, move.to_y
                while (x != move.from_x or y != move.from_y):
                    x += dx
                    y += dy
                    if (field_for_check.type_at(x, y) != CheckerType.NONE):
                        field_for_check.at(x, y).change_type(CheckerType.NONE)
                        has_killed_checker = True
                if (draw): self.__draw()
            else:
                if (draw): self.__animate_move(move)
                if (move.to_y == 0 and self.__field.type_at(move.from_x, move.from_y) == CheckerType.WHITE_REGULAR):
                    self.__field.at(move.from_x, move.from_y).change_type(CheckerType.WHITE_QUEEN)
                elif (move.to_y == self.__field.y_size - 1 and self.__field.type_at(move.from_x,
                                                                                    move.from_y) == CheckerType.BLACK_REGULAR):
                    self.__field.at(move.from_x, move.from_y).change_type(CheckerType.BLACK_QUEEN)
                self.__field.at(move.to_x, move.to_y).change_type(self.__field.type_at(move.from_x, move.from_y))
                self.__field.at(move.from_x, move.from_y).change_type(CheckerType.NONE)
                dx = -1 if move.from_x < move.to_x else 1
                dy = -1 if move.from_y < move.to_y else 1
                has_killed_checker = False
                x, y = move.to_x, move.to_y
                while (x != move.from_x or y != move.from_y):
                    x += dx
                    y += dy
                    if (self.__field.type_at(x, y) != CheckerType.NONE):
                        self.__field.at(x, y).change_type(CheckerType.NONE)
                        has_killed_checker = True

                if (draw): self.__draw()

        return has_killed_checker

    def __handle_player_turn(self, move: Move):
        self.timer_sleep = True
        self.__player_turn = False
        has_killed_checker = self.__handle_move(move, self.__field)
        if MULTIPLAYER['value'] == 1.0:
            required_moves_list = list(
                filter(lambda required_move: move.to_x == required_move.from_x and move.to_y == required_move.from_y,
                       self.__get_required_moves_list(self.__current_player)))
        else:
            required_moves_list = list(
                filter(lambda required_move: move.to_x == required_move.from_x and move.to_y == required_move.from_y,
                       self.__get_required_moves_list(PLAYER_SIDE)))
        if (has_killed_checker and required_moves_list):
            self.__player_turn = True
            self.timer_sleep = False
            if not self.timer_player_run and not self.timer_opponent_run:
                self.update_player_timer()
            event = Event()
            event.x = (self.selected_if_has_killed[0] * CELL_SIZE) + BOARD_BORDER
            event.y = (self.selected_if_has_killed[1] * CELL_SIZE) + BOARD_BORDER
            self.mouse_down(event)
            self.__selected_cell = Point(self.selected_if_has_killed[0], self.selected_if_has_killed[1])
        else:
            self.timer_sleep = False
            if not self.timer_player_run and not self.timer_opponent_run:
                self.update_player_timer()
            self.selected_if_has_killed = []
            self.__selected_cell = Point()


    def __check_for_game_over(self):
        game_over = False
        self.ok_not_clicked = True

        white_moves_list = self.__get_moves_list(SideType.WHITE)
        def ok_button_clicked():
            self.ok_not_clicked = False
            self.child_window.destroy()
            self.return_to_main_menu()

        if not (white_moves_list) or self.timer_player == 0:
            self.timer_player_run = False
            self.timer_opponent_run = False
            self.running = False
            self.child_window = customtkinter.CTkToplevel(self.main_window, width=400, height=300)
            self.child_window.transient(self.main_window)
            self.child_window.resizable(False, False)
            self.child_window.overrideredirect(True)
            main_x = self.main_window.winfo_x()
            main_y = self.main_window.winfo_y()
            main_width = self.main_window.winfo_width()
            main_height = self.main_window.winfo_height()

            child_x = main_x + (main_width - 400) // 2
            child_y = main_y + (main_height - 300) // 2

            self.child_window.geometry(f'+{child_x}+{child_y}')
            self.child_window.grab_set()
            self.child_window.attributes('-topmost', True)

            images = ImageTk.PhotoImage(Image.open(resources_path('assets\\black_win.png')))
            background_label = Label(self.child_window, image=images)
            background_label.place(x=0, y=0, relwidth=1, relheight=1)
            background_label.image = images
            background_label.place(x=0, y=0)



            ok_button_image = ImageTk.PhotoImage(Image.open(resources_path('assets\\win_button.png')))
            ok_button = Button(self.child_window, image=ok_button_image, command=ok_button_clicked, borderwidth=0,
                               highlightthickness=0,
                               activebackground='#B5B4B5',
                               cursor='hand2')
            ok_button.place(relx=0.51, rely=0.8, anchor='center')
            self.child_window.wait_window()
            game_over = True

        black_moves_list = self.__get_moves_list(SideType.BLACK)
        if not (black_moves_list) or self.timer_opponent == 0:

            self.timer_player_run = False
            self.timer_opponent_run = False
            self.running = False
            self.child_window = customtkinter.CTkToplevel(self.main_window, width=400, height=300)
            self.child_window.transient(self.main_window)
            self.child_window.resizable(False, False)
            self.child_window.overrideredirect(True)
            main_x = self.main_window.winfo_x()
            main_y = self.main_window.winfo_y()
            main_width = self.main_window.winfo_width()
            main_height = self.main_window.winfo_height()

            child_x = main_x + (main_width - 400) // 2
            child_y = main_y + (main_height - 300) // 2

            self.child_window.geometry(f'+{child_x}+{child_y}')
            self.child_window.grab_set()
            self.child_window.attributes('-topmost', True)

            images = ImageTk.PhotoImage(Image.open(resources_path('assets\\white_win.png')))
            background_label = Label(self.child_window, image=images)
            background_label.place(x=0, y=0, relwidth=1, relheight=1)
            background_label.image = images  # Сохранение ссылки на изображение
            background_label.place(x=0, y=0)

            ok_button_image = ImageTk.PhotoImage(Image.open(resources_path('assets\\win_button.png')))
            ok_button = Button(self.child_window, image=ok_button_image, command=ok_button_clicked, borderwidth=0,
                               highlightthickness=0,
                               activebackground='#B5B4B5',
                               cursor='hand2')
            ok_button.place(relx=0.51, rely=0.8, anchor='center')
            self.timer_player_run = False
            self.timer_opponent_run = False
            self.child_window.wait_window()
            game_over = True




    def handle_enemy_turn_calc_async(self):
        function_with_logging()
        thread = Thread(target=self.__handle_enemy_turn_calc, daemon=True)
        thread.start()
        return thread

    def __handle_enemy_turn_calc(self):
        function_with_logging()
        self.__player_turn = False
        self.in_thread = True
        self.calc = True
        if not self.running:
            return
        self.optimal_moves_list = self.__predict_optimal_moves(SideType.opposite(PLAYER_SIDE))
        if not self.running:
            return
        self.calc = False
        self.in_thread = False

    def simulate_thinking(self, game_over: bool = False):
        if game_over:
            return
        and_of_predict_moves = self.timer_opponent
        time_of_predict = self.timer_value_of_enemy_turn_start - and_of_predict_moves
        if self.timer_value_of_enemy_turn_start > TIMER['value']/2:
            time_of_thinking = random.randint(3, 5)
            time_to_kill = 2
        else:
            time_of_thinking = random.randint(2, 4)
            time_to_kill = 1
        if self.first_move_is_kill:

            if time_of_predict >= 3:
                return
            else:
                current_opponent_time = self.timer_opponent
                while self.timer_value_of_enemy_turn_start - current_opponent_time < time_to_kill:
                    self.__canvas.update()
                    current_opponent_time = self.timer_opponent
                return
        else:

            if time_of_predict >= 3:
                return
            else:
                current_opponent_time = self.timer_opponent
                while self.timer_value_of_enemy_turn_start-time_of_thinking != current_opponent_time:
                    self.__canvas.update()
                    current_opponent_time = self.timer_opponent
                return






    def __handle_enemy_turn(self, moves):
        function_with_logging()
        if not self.running:
            return
        for move in moves:
            self.timer_sleep = True
            self.__handle_move(move, self.__field)
            self.timer_sleep = False
            if not self.timer_player_run and not self.timer_opponent_run:
                self.update_player_timer()
        self.__player_turn = True
        self.__check_for_game_over()




    def __predict_optimal_moves(self, side: SideType) -> list[Move]:
        function_with_logging()
        if PLAYER_SIDE == SideType.WHITE:
            side = SideType.BLACK
        function_with_logging()
        best_result = 0
        optimal_moves = []
        self.test_field = Field.copy(self.__field)
        if not self.running:
            return
        predicted_moves_list = self.__get_predicted_moves_list(MAX_DEPTH['value'], side)
        if not self.running:
            return
        self.test_field = Field.copy(self.__field)
        if (predicted_moves_list):
            field_copy = Field.copy(self.test_field)
            for moves in predicted_moves_list:
                if not self.running:
                    return
                for move in moves:
                    if not self.running:
                        return
                    self.__handle_move(move, self.test_field, draw=False)
                try:
                    if (side == SideType.WHITE):
                        result = self.test_field.white_score / self.test_field.black_score
                    elif (side == SideType.BLACK):
                        result = self.test_field.black_score / self.test_field.white_score
                except ZeroDivisionError:
                    result = inf
                if (result > best_result):
                    best_result = result
                    optimal_moves.clear()
                    optimal_moves.append(moves)
                elif (result == best_result):
                    optimal_moves.append(moves)
                self.test_field = Field.copy(field_copy)
        optimal_move = []
        if (optimal_moves):
            for move in choice(optimal_moves):
                if (side == SideType.WHITE and self.__field.type_at(move.from_x, move.from_y) in BLACK_CHECKERS):
                    break
                elif (side == SideType.BLACK and self.__field.type_at(move.from_x, move.from_y) in WHITE_CHECKERS):
                    break
                optimal_move.append(move)
        return optimal_move

    def __get_predicted_moves_list(self, depth, side: SideType, current_prediction_depth: int = 0,
                                   all_moves_list: list[Move] = [], current_moves_list: list[Move] = [],
                                   required_moves_list: list[Move] = []) -> list[Move]:
        function_with_logging()
        if not self.running:
            return

        check_kill_on_first_move = (current_prediction_depth == 0)

        if (current_moves_list):
            all_moves_list.append(current_moves_list)
        else:
            all_moves_list.clear()

        if (required_moves_list):
            moves_list = required_moves_list
        else:
            if check_kill_on_first_move:
                moves_list = self.__get_moves_list(side, self.test_field, check_kill_on_first_move)
            else:
                moves_list = self.__get_moves_list(side, self.test_field)
        if (moves_list and current_prediction_depth < depth):
            field_copy = Field.copy(self.test_field)
            for move in moves_list:
                if not self.running:
                    return
                has_killed_checker = self.__handle_move(move, self.test_field, draw=False)
                function_with_logging()
                required_moves_list = list(filter(
                    lambda required_move: move.to_x == required_move.from_x and move.to_y == required_move.from_y,
                    self.__get_required_moves_list(side, self.test_field)))
                if (has_killed_checker and required_moves_list):
                    if not self.running:
                        return
                    self.__get_predicted_moves_list(depth, side, current_prediction_depth, all_moves_list,
                                                    current_moves_list + [move], required_moves_list)
                else:
                    if not self.running:
                        return
                    self.__get_predicted_moves_list(depth, SideType.opposite(side), current_prediction_depth + 1,
                                                    all_moves_list, current_moves_list + [move])
                self.test_field = Field.copy(field_copy)
        return all_moves_list

    def __get_moves_list(self, side: SideType, field: Field = None, check_kill_first_move: bool = None) -> list[Move]:
        function_with_logging()
        if field is None:
            field = self.__field
        moves_list = self.__get_required_moves_list(side, field)
        if moves_list and check_kill_first_move and self.calc:
            self.first_move_is_kill = True
        if not (moves_list):
            moves_list = self.__get_optional_moves_list(side, field)
        return moves_list

    def __get_required_moves_list(self, side: SideType, field: Field = None) -> list[Move]:
        function_with_logging()
        if field is None:
            field = self.__field

        moves_list = []
        if (side == SideType.WHITE):
            friendly_checkers = WHITE_CHECKERS
            enemy_checkers = BLACK_CHECKERS
        elif (side == SideType.BLACK):
            friendly_checkers = BLACK_CHECKERS
            enemy_checkers = WHITE_CHECKERS
        else:
            return moves_list

        for y in range(field.y_size):
            for x in range(field.x_size):
                if (field.type_at(x, y) == friendly_checkers[0]):
                    for offset in MOVE_OFFSETS:
                        if not (field.is_within(x + offset.x * 2, y + offset.y * 2)): continue
                        if field.type_at(x + offset.x, y + offset.y) in enemy_checkers and field.type_at(
                                x + offset.x * 2, y + offset.y * 2) == CheckerType.NONE:
                            moves_list.append(Move(x, y, x + offset.x * 2, y + offset.y * 2))
                elif (field.type_at(x, y) == friendly_checkers[1]):
                    for offset in MOVE_OFFSETS:
                        if not (field.is_within(x + offset.x * 2, y + offset.y * 2)): continue

                        has_enemy_checker_on_way = False

                        for shift in range(1, field.size):
                            if not (field.is_within(x + offset.x * shift, y + offset.y * shift)): continue

                            if (not has_enemy_checker_on_way):
                                if (field.type_at(x + offset.x * shift, y + offset.y * shift) in enemy_checkers):
                                    has_enemy_checker_on_way = True
                                    continue
                                elif (field.type_at(x + offset.x * shift,
                                                    y + offset.y * shift) in friendly_checkers):
                                    break

                            if (has_enemy_checker_on_way):
                                if (field.type_at(x + offset.x * shift,
                                                  y + offset.y * shift) == CheckerType.NONE):
                                    moves_list.append(Move(x, y, x + offset.x * shift, y + offset.y * shift))
                                else:
                                    break

        return moves_list

    def __get_optional_moves_list(self, side: SideType, field: Field = None) -> list[Move]:
        function_with_logging()
        if field is None:
            field = self.__field

        moves_list = []
        if (side == SideType.WHITE):
            friendly_checkers = WHITE_CHECKERS
        elif (side == SideType.BLACK):
            friendly_checkers = BLACK_CHECKERS
        else:
            return moves_list

        for y in range(field.y_size):
            for x in range(field.x_size):
                if field.type_at(x, y) == friendly_checkers[0]:
                    for offset in MOVE_OFFSETS[:2] if side == SideType.WHITE else MOVE_OFFSETS[2:]:
                        if not (field.is_within(x + offset.x, y + offset.y)): continue
                        if field.type_at(x + offset.x, y + offset.y) == CheckerType.NONE:
                            moves_list.append(Move(x, y, x + offset.x, y + offset.y))

                elif (field.type_at(x, y) == friendly_checkers[1]):
                    for offset in MOVE_OFFSETS:
                        if not (field.is_within(x + offset.x, y + offset.y)): continue
                        for shift in range(1, field.size):
                            if not (field.is_within(x + offset.x * shift, y + offset.y * shift)): continue
                            if (field.type_at(x + offset.x * shift,
                                              y + offset.y * shift) == CheckerType.NONE):
                                moves_list.append(Move(x, y, x + offset.x * shift, y + offset.y * shift))
                            else:
                                break

        return moves_list
