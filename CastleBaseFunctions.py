# -*- coding: utf-8 -*-

__all__ = ['print60','printblock60']

from math import ceil, sqrt
from copy import copy
from random import shuffle

# Well... I prefer a hundred

MAX_LINE_LENGTH = 100
TABLE_SPACER_WIDTH = 3

def print60(*args, **dargs ):
    #print(args, "ARGS")
    if args:
        text = args[0]
    else:
        text = ""
    text = text.split('\n')
    for block in text:
        printt(block, MAX_LINE_LENGTH, **dargs)
    return None

def input60(text):
    print60(text, last='')
    return input()

def printblock60(names):
    _fa(sorted(names, key=len), len(names))

def _fa(n, length):
    for w in reversed(range(1,length+1)):
        if _fll(n, w, length, ceil(length / w)) < MAX_LINE_LENGTH:
            for line in _i(n, w, length, ceil(length / w)):
                print(line)
            return

def _shuffled(l):
    #shuffle(l)
    # NOTE: there is one key problem with this; a single end term can be
    # mixed in and confuse all the others
    return l

def _shuffledrange(*args):
    # yes, bad mem use for several k long lists ;-)
    return _shuffled([k for k in range(*args)])

def _i(n, w, l, h):
    for g in _dg(n, w, l, h, _shuffledrange(0, l, h)):
        yield g

def _dg(sortednames, width, length, height,srh):
    for cd in _shuffledrange(0, height):
        yield _join( _adjstr(sortednames,i+height-1,i + cd) for i in srh)

def _adjstr(sortednames, largest, current):
    try:
        return _a(_lrg_lst(sortednames,largest),sortednames[current])
    except IndexError:
        return " "

def _lrg_lst(sortednames,index):
    try:
        return sortednames[index]
    except IndexError:
        return sortednames[-1]

def _a(lrg, cur):
    return cur + (len(lrg) - len(cur) + TABLE_SPACER_WIDTH)*" "

def _join(iterable):
    # for strings, this is more efficient then all the others.
    s = ""
    for w in iterable:
        s += w
    return s

def _fll(sortednames, width, length, height):
    return sum( (TABLE_SPACER_WIDTH + len(_lrg_lst(sortednames,i+height-1))) for i in range(0,length,height)      )

def _retab(string):
    if string == "\\t":
        return "  "
    return string

def printt(text, length, adjust='left', last='\n'):
    text = text.split()
    if not text:
        print()
    while text:
        s = ""
        while text and len(s) + len(text[0]) + 1 <= length:
            s += _retab(text.pop(0)) + ' '
            # question: what is faster: (s + ' ') + tp0, or
            # s + (' ' + tp0) ?
        if adjust == 'right':
            print(" "*(length - len(s)), end='')
        elif adjust == 'center':
            print(" "*( (length - len(s))//2 + 1 ), end='')
        if text:
            print(s)
        else:
            print(s, end=last)

if __name__ == '__main__':
    c = ['Three Cows', 'Me', 'The interpreter', 'A fool', '99 bottles-of-beer on a wall','Two cinderblocks', 'The cookies', 'One hundred Reasons Why']
    printblock60(c)