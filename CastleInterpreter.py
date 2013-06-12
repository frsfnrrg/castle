# -*- coding: utf-8 -*-

import random

from CastleConstants import numberwords
from CastleBaseFunctions import print60, printblock60

import CastleFramework as CF

LOGGING_ENABLED = True
LOGGING_ENABLED = not LOGGING_ENABLED

# (un)comment above to stop/start logging

# NOTE TO FUTURE SELVES: When you import things, import* makes _local_ copies. If you want things to interact, you _must_ import the module
# The others are fine, because they send globally stateless functions/constants

def _adjust(word):
    try:
        c = numberwords[word]
        if c > 0:
            return c
        return word
    except KeyError:
        try:
            c = int(word)
            if c >= 0:
                return c
            return word
        except ValueError:
            return word

def decipher(text):
    return [_adjust(word) for word in text.split()]

def _get_num(prompt, limit):
    annoyance = 0
    while True:
        try:
            i = int(input(prompt).strip())
            if i < 1 or i > limit:
                print60("You have {0} options, from 1 to {0}. Not too tough to understand.".format(limit))
                annoyance += 1
            else:
                return i
        except ValueError:
            if annoyance == 0:
                print60("That isn't a number. Pick one.")
            elif annoyance < 3:
                print60("Choose a number from 1 to {}, inclusive.".format(limit))
            elif annoyance < 4:
                print60("You hear rumblings from above. Choose a number. NOW.")
            elif annoyance < 5:
                print60("CHOOSE ONE FINALLY!!")
            elif annoyance >= 5:
                print60("A thunderbolt comes out of nowhere and kills you. The gods were displeased by your stupidity.")
                CF.print_score()
                quit()
            annoyance += 1

def _pname(gn):
    k = gn.split("_")
    if len(k) > 1 and k[1] == "SELF":
        s = "Your "
    else:
        s = ""
    if len(gn) > 4 and gn[-4:] == "_SUB":
        s += CF.objects[CF.objects[gn[:-4]].subs()].name()
    else:
        s += CF.objects[gn].name()
    return s

def select(choices):
    # the (1) d-- the (2) c-- and the (3) c----- p--
    if len(choices) == 1:
        return choices[0]

    random.shuffle(choices)# why not random.shuffle*d*
    names = [_pname(o) for o in choices]

    s = "Pick one:"
    c = 1
    for name in names:
        s += " ({0}) {1}".format(c, name)
        c += 1
    s += ".\n??? "

    i = _get_num(s, len(choices))
    return choices[i-1]


def do(s):
    # Make obj stuff a function (in interpreter)
    names = CF.get_names()
    # The names of the objects in local scope: me and the room

    s = s.strip().upper()

    # Seek objects referred to
    for n in names:
        j = n.upper()
        k = s.find(j)
        # ? use 'if j in s:' ?
        if k != -1:
            #s = # yes, this double searches (find, replace)

            # When a _SUB is found: refer to its owning group
            chosen = select(names[n])

            # THE ABOVE IS A PROBLEM: take, drop should refer to the more capable one, not a random one (or put that in the actual code command created?)
            # so use (roomtag (base &) (get-room))

            if len(chosen) >= 4 and chosen[-4] == '_':
                action = decipher(s.replace(j, '#'))
                if CF.objects[chosen[:-4]].call(action):
                    return
            # Otherwise, just format and go
            else:
                action = decipher(s.replace(j, '%'))
                if CF.objects[chosen].call(action):
                    return
                # else: You cannot do that to the {}.

    if s in ('I','LIST','INVENTORY'):
        print60('You are carrying:')
        li = []
        for o in CF.rooms['SELF'].get_contents():
            if CF.objects[o].is_visible():
                if CF.objects[o].is_group() and CF.objects[o].count() == 1:
                    li.append(CF.objects[CF.objects[o].subs()].name())
                else:
                    li.append(CF.objects[o].name())
        if li:
            printblock60(li)
        else:
            print60('Nothing')
        if s == 'LIST':
            print()
        else:
            return

    # NOTE: This should be formatted
    # like a table, that goes down for first three, then out to width 60, then down and down.
    # either way, a horizontal y1 list is bad
    # a vertical y(4+) x1 takes up too much space
    if s in ('L','LOOK','LIST','VIEW'):
        if s in ('L','LOOK'):
            CF.look_at_room()
        print60('You can see:')
        li = []
        for o in CF.rooms[CF.current_room].get_contents():
            try:
                if CF.objects[o].is_visible():
                    if CF.objects[o].is_group() and CF.objects[o].count() == 1:
                        li.append(CF.objects[CF.objects[o].subs()].name())
                    else:
                        li.append(CF.objects[o].name())
            except KeyError:
                pass# NOT ADDED TO DATA YET
        if li:
            printblock60(li)
        else:
            print60('Nothing')
        return

    # room specific methods: ex. 'go down', 'dance'
    if CF.rooms[CF.current_room].call(s):
        return
    # globally applicable methods, overridable by room methods
    try:
        t = CF.globalscripts[s]
    except KeyError:
        pass
    else:
        CF.exec_script(t)
        return

    if random.random() > .02:
        print60("Please be more clear, or ask for 'HELP'.")
    elif random.random() > .2:
        print60("You have not been understood. Be more clear, or beg 'DIVINE AID'.")
    else:
        print60("You said what??")



def main():
    print60(CF.introtext[0], adjust='center')
    print60(CF.introtext[1], adjust='left')
    CF.look_at_room()
    if LOGGING_ENABLED:
        lf = make_log()
    while True:
        # insert step: update the daemons, so things like bats can move around, and timed occurences - i.e. torch burning can happen
        CF.update_daemons()
        c = input('>>> ')
        if LOGGING_ENABLED:
            lf.write(c + "\n")
        do(c)

    print60(CF.extrotext)

def make_log():
    import os
    k = 0
    while os.path.exists("logs/{0}.txt".format(k)):
        k += 1
    return open("logs/{0}.txt".format(k),mode='a')

if __name__ == '__main__':
    main()
    #import cProfile
    #cProfile.run('main()')#,'profile.txt')
    # Profiling info shows: on a simple start-look-take candle-quit run
    # exec_script 4 times, 25/21 times rec
    # call 140 times, 2 msec
    # t called 1303 times in the 41 nested-dict-tries; .007 seconds
    # _rfmap @ 212 rec, 4 main, 8 msec
    # nested_map costed .010 sec w/ 571 rec, 41 primary
    # deepcopy is a big drain; it takes 1872 rec, 28 primary, @72 msec total
    #     ^ that may be primarily ugroup expansion
    # eval 140 times at cost 17 msec
    # len called 1465 times, time 3 msec
    # list append; 2353 times, 8 msec
    # dict[key] took 3765 times w/ 6 msec
    # 6959 msec main, 6818 msec input wait, so 141 msec action
else:
    raise ImportError('This file is not for import.')