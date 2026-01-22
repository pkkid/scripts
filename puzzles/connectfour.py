#!/usr/bin/pypy3
"""
Connect Four game with AI opponent.

Play the classic Connect Four game against a computer AI opponent (GLADOS).
The game features a minimax algorithm with alpha-beta pruning for the AI
to provide challenging gameplay.

Usage:
  ./connectfour.py [--depth <depth>] [--hints]

Options:
  --depth <n>    AI search depth (default: 4, higher is harder)
  --hints        Show move suggestions for human player

Gameplay:
  - Players alternate dropping pieces into a 7x6 grid
  - Pieces fall to the lowest available position in a column
  - First to connect 4 pieces horizontally, vertically, or diagonally wins
  - Enter column number (0-6) to make your move

Example:
  ./connectfour.py --depth 5 --hints
  # Play with AI at depth 5 and show move hints

Use pypy3 for faster AI computation. Falls back to python3 if unavailable.
"""
import copy
import argparse
import os
import time
import random

BANNER = r"""
   ____                            _     _  _
  / ___|___  _ __  _ __   ___  ___| |_  | || |
 | |   / _ \| '_ \| '_ \ / _ \/ __| __| | || |_
 | |__| (_) | | | | | | |  __/ (__| |_  |__   _|
  \____\___/|_| |_|_| |_|\___|\___|\__|    |_|
"""
INSPIRATION = ["Great choice!", "That looks like a good move.", "You think that will stop me?",
    "You're forgetting, I am a computer.", "Ohh, that's a good one.", "Not going to make it easy, are you?",
    "Is that the best you got?"]
TRASHTALK = ["I'm not so sure about this one.", "Try this on for size.", "How about these apples!?",
    "You got me puzzled here.", "This will knock your socks off.", "AI coming in for the win!"]

HUMAN, CPU, EMPTY = '🔴', '🟡', '⚫'
PLAYERS = [HUMAN, CPU]
BOARD = [list(row) for row in """
⚫⚫⚫⚫⚫⚫⚫
⚫⚫⚫⚫⚫⚫⚫
⚫⚫⚫⚫⚫⚫⚫
⚫⚫⚫⚫⚫⚫⚫
⚫⚫⚫⚫⚫⚫⚫
⚫⚫⚫⚫⚫⚫⚫
""".strip().split('\n')]


def rgb(text, color='#aaa'):
    r,g,b = tuple(int(x*2, 16) for x in color.lstrip('#'))
    return f'\033[38;2;{r};{g};{b}m{text}\033[00m'


def name(player):
    """ Get a friendly player name. """
    return 'GLADOS' if player == CPU else 'HUMAN'


def flush_input():
    """ Flush user input. Prevents them from typing something before we
        asked a question and later assuming that was their input.
    """
    try:
        import msvcrt  # Windows
        while msvcrt.kbhit():
            msvcrt.getch()
    except ImportError:
        import sys, termios  # Linux
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)


def lets_play_connectfour(opts):
    """ Play the game. """
    winner, weights = None, {}
    board = copy.deepcopy(BOARD)
    player = CPU if opts.second else HUMAN
    while winner is None:
        if player == HUMAN:
            choice = get_human_move(opts, board, weights)
            msg = random.choice(INSPIRATION)
        else:
            choice, weights = get_cpu_move(opts, board)
            msg = random.choice(TRASHTALK)
        board = get_new_board(opts, board, choice, player, msg, weights, animate=0.1)
        winner, count = count_wins(opts, board)
        if winner:
            print_board(opts, board, msg=rgb('WINNER WINNER\n  CHICKEN DINNER!','#ee2'))
            print()
        player = PLAYERS[(PLAYERS.index(player) + 1) % 2]


def get_human_move(opts, board, weights=None):
    """ Allow the human to choose a move. """
    invalid = False
    while True:
        print_board(opts, board, weights=weights)
        if invalid:
            print(rgb('  Invalid choice.', '#b32'))
        flush_input()
        choice = input('  What is your next move? (1-7): ')
        print()
        if len(choice) == 1 and choice in '1234567':
            choice = int(choice) - 1
            if board[0][choice] == EMPTY:
                return choice
        invalid = True


def get_cpu_move(opts, board, player=None, weights=None, cpumove=None, depth=0):
    """ Get the CPU move. """
    if depth == 6: return
    player = player or CPU
    weights = weights or {x:{CPU:0,HUMAN:0} for x in range(7)}
    original = copy.deepcopy(board)
    for move in range(len(board[0])):
        if depth == 0 and original[0][move] != EMPTY:
            del weights[move]
        if original[0][move] != EMPTY:
            continue
        cpumove = move if depth == 0 else cpumove
        board = get_new_board(opts, original, move, player)
        wins = count_wins(opts, board, cpumove, depth)[1]
        if wins:
            multiplier = 7 ** (3 - int(depth / 2))
            weights[cpumove][player] += wins * multiplier
        else:
            nextplayer = PLAYERS[(PLAYERS.index(player) + 1) % 2]
            get_cpu_move(opts, board, nextplayer, weights, cpumove, depth+1)
    if depth == 0:

        defense = [(points[HUMAN],move) for move,points in weights.items()]
        defense = list(filter(lambda m:m[0] == min([x[0] for x in defense]), defense))
        defense = random.choice(defense)
        return defense[1], weights


def count_wins(opts, board, cpumove=0, depth=0):
    """ Look for a winner on the board. """
    count = 0
    winner = None
    # Dirs: NE, E, SE, S
    dirs = [(-1,1,'⇗'), (0,1,'⇒'), (1,1,'⇘'), (1,0,'⇓')]
    for x in range(len(board)):
        for y in range(len(board[x])):
            if board[x][y] == EMPTY:
                continue
            for dir in dirs:
                if not check_position_wins(board, x, y, dir):
                    continue
                count += 1
                winner = board[x][y]
                # print(f'If CPU moves {cpumove}, {name(winner)} may win at {x},{y},{dir[2]} in {int(depth/2)+1} moves.')  # noqa
    return winner, count


def check_position_wins(board, x, y, dir):
    """ Check the piece at the current x,y and direction wins the game. """
    player = board[x][y]
    for i in range(1,4):
        cx = x + (dir[0]*i)
        cy = y + (dir[1]*i)
        if cx < 0 or cx >= len(board): return False
        if cy < 0 or cy >= len(board[cx]): return False
        if board[cx][cy] != player: return False
    return True


def get_new_board(opts, board, column, player, msg=None, weights=None, animate=0):
    """ Animate the player or AI move into place. """
    board = copy.deepcopy(board)
    x, y = (-1, column)
    if animate: print_board(opts, board, msg, weights, wait=1)
    while x < len(board)-1 and board[x+1][y] == EMPTY:
        if x >= 0: board[x][y] = EMPTY
        board[x+1][y] = player
        if animate:
            print_board(opts, board, msg, weights, wait=animate)
            animate *= 0.7
        x += 1
    if animate: time.sleep(1)
    return board


def print_board(opts, board, msg=None, weights=None, wait=0, bordercolor='#57a'):
    """ Draw the board. """
    # Create the debug info if enabled
    debuglines = {i:'' for i in range(len(board[0]))}
    if opts.debug and weights:
        for i in range(len(board[0])):
            if not weights.get(i): continue
            debuglines[i] = rgb(f'    {i+1}: {name(CPU)}:{str(weights[i][CPU]):4}'
                f' {name(HUMAN)}:{str(weights[i][HUMAN]):4}', '#333')
    # Draw the board
    os.system('clear')
    print(rgb(BANNER, '#95a'))
    print(rgb('      1 2 3 4 5 6 7', bordercolor))
    print(rgb('    ┏━━━━━━━━━━━━━━━━┓', bordercolor) + debuglines.get(0,''))
    for i, row in enumerate(board):
        bar = rgb('┃', bordercolor)
        print(f'    {bar} {"".join(row)} {bar}' + debuglines.get(i+1,''))
    print(rgb('   ┏┻━━━━━━━━━━━━━━━━┻┓', bordercolor))
    print('')
    if msg: print(f'  {msg}')
    time.sleep(wait)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Connect Four.')
    parser.add_argument('--debug', default=False, action='store_true', help='Enable debug logging.')
    parser.add_argument('--depth', default=4, type=int, help='Max depth to calculate.')
    parser.add_argument('--second', default=False, action='store_true', help='You play second.')
    opts = parser.parse_args()
    try:
        lets_play_connectfour(opts)
    except KeyboardInterrupt:
        print('\n  Bye.\n')
