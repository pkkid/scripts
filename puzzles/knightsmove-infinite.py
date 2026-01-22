#!/usr/bin/env python3
"""
Calculate knight moves on an infinite chessboard.

Given start and end coordinates on an infinite board, calculates the minimum
number of moves a knight needs to reach the destination. Uses a heuristic
approach: moves toward the target, then uses a lookup table for the final moves.

Usage: ./knights_move_infinite.py x1 y1 x2 y2
Example: ./knights_move_infinite.py 0 0 11 10
"""
import math

MOVES = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
MOVESLEFT = {(0,0):0, (1,1):2, (0,1):3, (2,2):4, (1,2):1, (0,2):2, (3,3):2,
    (2,3):3, (1,3):2, (0,3):3, (3,4):3, (2,4):2, (1,4):3, (0,4):2,
    (2,5):3, (1,5):4, (0,5):3, (1,6):3, (0,6):4, (7,0):5}
distance = lambda p1,p2: abs(p2[0]-p1[0]) + abs(p2[1]-p1[1])


def next_pos(p1, p2):
    deg = math.degrees(math.atan2(p2[1]-p1[1], p2[0]-p1[0]))
    deg += 0 if deg >= 0 else 360
    move = MOVES[int((deg)/45)]
    return (p1[0]+move[0], p1[1]+move[1])


def moves_left(p1, p2):
    diff = (abs(p2[0]-p1[0]), abs(p2[1]-p1[1]))
    diff = diff[::-1] if diff[0] > diff[1] else diff
    return MOVESLEFT[diff]


def num_moves(p1, p2):
    count = 0
    dist = distance(p1, p2)
    while dist > 7:
        count += 1
        p1 = next_pos(p1, p2)
        print(f"{count}: {p1}")
        dist = distance(p1, p2)
    movesleft = moves_left(p1, p2)
    print(f"We're close! {movesleft} moves left.")
    return count + movesleft


if __name__ == '__main__':
    import sys
    args = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [0, 0, 11, 10]
    result = num_moves((args[0], args[1]), (args[2], args[3]))
    print(result)
