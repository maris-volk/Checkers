from checkers.enums import SideType, CheckerType
from checkers.point import Point


def change_mode():
    global constants
    if MULTIPLAYER['value'] == 0.0:
        MULTIPLAYER['value'] = 1.0
    if MULTIPLAYER['value'] == 1.0:
        MULTIPLAYER['value'] = 0.0

CELL_SIZE = 72
BOARD_BORDER = 112
ANIMATION_SPEED = 4
X_SIZE = Y_SIZE = 8

TIMER = {'value': 180.0}
MULTIPLAYER = {'value': 0.0}
MAX_DEPTH = {'value': 1.0}

MOVE_OFFSETS = [
    Point(-1, -1),
    Point(1, -1),
    Point(-1, 1),
    Point(1, 1)
]

PLAYER_SIDE = SideType.WHITE
WHITE_CHECKERS = [CheckerType.WHITE_REGULAR, CheckerType.WHITE_QUEEN]
BLACK_CHECKERS = [CheckerType.BLACK_REGULAR, CheckerType.BLACK_QUEEN]
ENEMY_CHECKERS = {
    SideType.WHITE: BLACK_CHECKERS,
    SideType.BLACK: WHITE_CHECKERS,
}

