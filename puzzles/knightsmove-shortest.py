#!/usr/bin/env python3
"""
Find the shortest knight path between two chess squares.

Given start and end squares in chess notation (e.g., 'a1', 'h8'), calculates
the minimum number of moves a knight needs to reach the destination. A knight
moves in an "L" shape: 2 squares in one direction and 1 square perpendicular.

Usage: num_moves('a1', 'h8') -> int
Reference: https://py.checkio.org/en/mission/shortest-knight-path/
"""
MOVES = [(1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)]
inbound = lambda p: 0 <= p[0] < 8 and 0 <= p[1] < 8
pos = lambda p: ('abcdefgh'.index(p[0]), int(p[1])-1)


def num_moves(start, end):
    moves = 0
    start, end = pos(start), pos(end)
    visited = set((start,))
    while len(visited) < 64:
        moves += 1
        for p in list(visited):
            newspots = ((p[0]+m[0], p[1]+m[1]) for m in MOVES)
            visited.update(filter(inbound, newspots))
            # if end in visited: break
    return moves


if __name__ == '__main__':
    print(num_moves('a1', 'a1'))
    with open('tests.txt', 'r') as f:
        for line in f.read().splitlines():
            start, end, num = line.split()
            assert num_moves(start, end) == int(num), "%s->%s = %s" % (start, end, num)
    print('All ok')
