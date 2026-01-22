#!/usr/bin/python3
"""
Quicksort algorithm implementation with visual output.

This script implements the quicksort sorting algorithm with an optional visual
representation of the sorting process. The visualization uses colored terminal
output to show the current state of the array during each step of the algorithm.

Algorithm:
  Quicksort is a divide-and-conquer sorting algorithm that:
  1. Selects a pivot element (first element in this implementation)
  2. Partitions the array so elements < pivot are on the left
  3. Recursively sorts the left and right partitions

Visualization:
  When draw=True, displays each step with color coding:
  - Yellow: Current pivot element
  - Blue: Left pointer scanning from start
  - Red: Right pointer scanning from end
  - Green: Elements in current partition being sorted
  - Gray: Elements outside current partition

Note:
  The script generates 20 random numbers (0-29) for demonstration.
  Modify the main block to sort different data.
"""


def rgb(text, color='#aaa'):
    r,g,b = tuple(int(x*2, 16) for x in color.lstrip('#'))
    return f'\033[38;2;{r};{g};{b}m{text}\033[00m'


def _draw(items, pivot=None, start=None, end=None, p1=None, p2=None, msg='', **kwargs):
    """ Draw whats going in the quicksorter. """
    print('[', end='')
    for i, item in enumerate(items):
        color = '#5d3'
        if pivot is not None and i == pivot: color = '#cc5'
        elif p1 is not None and i == p1: color = '#47e'
        elif p2 is not None and i == p2: color = '#e54'
        elif start is not None and i < start: color = '#555'
        elif end is not None and i > end: color = '#555'
        print(rgb(item, color), end='')
        if i != len(items)-1: print(', ', end='')
    msg = rgb(msg, '#555')
    print(f']  {msg}')


def swap(items, p1, p2):
    items[p1], items[p2] = items[p2], items[p1]


def quicksort(items, p1=None, p2=None, depth=0, draw=False):
    # Setup and break out early
    p1 = p1 or 0
    p2 = p2 or len(items)-1
    if p1 == p2: return None
    # Save the original p1 and p2
    start, end, pivot, p1 = p1, p2, p1, p1+1  # noqa
    if draw: _draw(msg=f'quicksort({start},{end})', **locals())
    
    if p1 == p2:
        if items[start] > items[p1]:
            swap(items, start, p1)
            if draw: _draw(msg=f'{items[p2]} ↔ {items[start]}', **locals())
            return None

    while p1 < p2:
        if items[p1] > items[pivot] and items[p2] <= items[pivot]:
            swap(items, p1, p2)
            if draw: _draw(msg=f'{items[p2]} ↔ {items[p1]}', **locals())
        if items[p1] <= items[pivot]:
            p1 += 1
        if items[p2] >= items[pivot]:
            p2 -= 1
    
    if items[p2] < items[pivot]:
        swap(items, p2, pivot)
        if draw: _draw(msg=f'{items[pivot]} ↔ {items[p2]} pivot', **locals())
    
    if start + 1 < end:
        quicksort(items, start, p2, depth+1, draw)
        quicksort(items, p1, end, depth+1, draw)


if __name__ == '__main__':
    import random
    items = []
    for x in range(20):
        items.append(random.randrange(0, 30))
    result = quicksort(items, draw=True)
    _draw(items, msg='DONE')
