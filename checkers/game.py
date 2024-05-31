import os
import sys
import logging
import tkinter
from time import sleep
from tkinter import Canvas, Event, Label, Button, messagebox
from random import choice
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
    pass


class Game:
    def __init__(self, canvas, x_field_size, y_field_size, main_window, menu_canvas):
        self.__current_player = SideType.WHITE if MULTIPLAYER['value'] == 1.0 else PLAYER_SIDE
        self.running = True
        self.selected_if_has_killed = []
        self.in_main = False
        self.in_thread = False
        self.calc = False
        self.optimal_moves_list = []
        self.__hover_animation_in_progress = False
        self.__gif_select_item = None
        self.__gif_hover_item = None
        self.test_field = Field(x_field_size, y_field_size)
        self.__animation_in_progress = False
        self.menu_canvas = menu_canvas
        self.main_window = main_window
        self.__canvas = canvas
        self.__init_images()
        self.background = None
        self.__create_background()
        self.game_over = False
        self.child_window = tkinter.Widget
        self.__field = Field(x_field_size, y_field_size)
        self.__player_turn = True
        self.ok_not_clicked = True
        self.__hovered_cell = Point()
        self.__selected_cell = Point()
        self.__animated_cell = Point()
        self.__draw()
        self.__gif_select_started = False
        self.__gif_hover_started = False

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
        elements_to_keep = [self.background]
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
                        self.test_field = self.__field
                        thread_calc = self.handle_enemy_turn_calc_async()
                        while thread_calc.is_alive():
                            self.__canvas.update()
                        moves = self.optimal_moves_list
                        self.__handle_enemy_turn(moves)

    def __handle_move(self, move: Move, field_for_check: Field = None, draw: bool = True) -> bool:
        '''Совершение хода'''
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

            event = Event()
            event.x = (self.selected_if_has_killed[0] * CELL_SIZE) + BOARD_BORDER
            event.y = (self.selected_if_has_killed[1] * CELL_SIZE) + BOARD_BORDER
            self.mouse_down(event)
            self.__selected_cell = Point(self.selected_if_has_killed[0], self.selected_if_has_killed[1])
        else:

            self.selected_if_has_killed = []
            self.__selected_cell = Point()

    def __check_for_game_over(self):
        game_over = False
        self.ok_not_clicked = True
        white_moves_list = self.__get_moves_list(SideType.WHITE)

        if not (white_moves_list):
            messagebox.showinfo("Игра окончена", "Чёрные выиграли")
            game_over = True

        black_moves_list = self.__get_moves_list(SideType.BLACK)
        if not (black_moves_list):
            messagebox.showinfo("Игра окончена", "Белые выиграли")
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

    def __handle_enemy_turn(self, moves):
        function_with_logging()
        if not self.running:
            return
        for move in moves:
            self.__handle_move(move, self.__field)
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
        if (current_moves_list):
            all_moves_list.append(current_moves_list)
        else:
            all_moves_list.clear()

        if (required_moves_list):
            moves_list = required_moves_list
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

    def __get_moves_list(self, side: SideType, field: Field = None) -> list[Move]:
        function_with_logging()
        if field is None:
            field = self.__field
        moves_list = self.__get_required_moves_list(side, field)
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
