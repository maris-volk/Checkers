

def change_mode():
    global constants
    if MULTIPLAYER['value'] == 0.0:
        MULTIPLAYER['value'] = 1.0
    if MULTIPLAYER['value'] == 1.0:
        MULTIPLAYER['value'] = 0.0


X_SIZE = Y_SIZE = 8
TIMER = {'value': 180.0}
MULTIPLAYER = {'value': 0.0}
MAX_DEPTH = {'value': 1.0}



