#!/usr/bin/python
"""
Find dictionary words matching an encrypted/encoded pattern.

This script finds all words from the system dictionary that could translate
to the given encoded word(s) based on character substitution patterns.
Each character in the encoded word represents a unique letter.

Usage:
  ./findword.py <encoded_word> [<encoded_word2> ...]

Example:
  ./findword.py abbc
  # Finds words like "eels", "door", "book" where the pattern matches
  # (first two chars different, last two chars the same)
"""
import copy, sys
from collections import namedtuple

WORDS = open('/usr/share/dict/american-english', 'r')
WORDS = [w.strip().lower() for w in WORDS.readlines()]
Match = namedtuple('Match', ['word', 'trans'])


def find_matches(eword, init_trans=None):
    matches = []
    init_trans = init_trans or {}
    for dword in WORDS:
        if len(dword) != len(eword):
            continue
        trans = copy.deepcopy(init_trans)
        match = True
        for i in range(len(dword)):
            echar = eword[i]
            dchar = dword[i]
            if echar not in trans:
                trans[echar] = dchar
            elif trans[echar] != dchar:
                match = False
                continue
        if match:
            matches.append(Match(dword, trans))
    return matches


if __name__ == '__main__':
    ewords = [w.lower() for w in sys.argv[1:]]
    for eword in ewords:
        print('--- %s ---' % eword)
        for match in find_matches(eword):
            print(match.word)
