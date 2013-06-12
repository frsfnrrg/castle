# -*- coding: utf-8 -*-

SCRIPT_DEBUG = False
# enables execution time traces of scripts

def enableDebug():
    global SCRIPT_DEBUG
    SCRIPT_DEBUG = True

def toggleDebug():
    global SCRIPT_DEBUG
    SCRIPT_DEBUG = not SCRIPT_DEBUG

def disableDebug():
    global SCRIPT_DEBUG
    SCRIPT_DEBUG = False

from CastleBaseFunctions import print60, input60
import random
from copy import deepcopy, copy
from collections import defaultdict
# deepcopy works on classes too! YAY!
# Using for instance duplication works, and wondefully

datafolder = "world/"

def LoadCastleData():
    # Read, then execute CastleData.level and linked files


   # why not globalize in there?

    make_real(_ll('CastleData.level'))

    global running_daemons
    global daemon_kill_queue
    daemon_kill_queue = []
    running_daemons = {}

def _ll(path, opened=[]):
    if path not in opened:
        opened.append(path)
    else:
        return []

    try:
        data = open(datafolder+path, 'r')
    except FileNotFoundError:
        print60('File >{}< does not exist: cannot load.'.format(path))
        return []

    D = []
    L = ''
    for line in data.read().split('\n'):
        line = line.lstrip()# bye,bye, indents

        if len(line) > 0:
            # 'import' file
            if line[0] == '$':
                D += _ll(line[1:])
            # comments excluded
            elif line[0] is ';':
                pass
            else:
                L += line + ' '

    L = [i for i in  L.split(' ')]

    # First, clean things up: get rid of newlines, spaces greater that 1

    D += nested_map(clean, get_llist(L, levelname=path))

    return D

def clean(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    elif s == 'None':
        return None
    try:
        if int(float(s)) == float(s):
            return int(s)
        return float(s)
    except ValueError:
        return s.replace('\\n','\n').replace('\\"','\"').replace('\\t',' \\\\t ')
        # Yep, it semi-evaluates tabs. Nice...

def nested_map(function, a):
    for i in range(len(a)):
        if type(a[i]) == list:
            a[i] = nested_map(function, a[i])
        else:
            a[i] = function(a[i])
    return a

# Cannot handle the empty string. otherwise exemplary
def get_llist(L, levelname='unknown'):
    datastructures = []
    recdepth = 0# the amount of [-1]'s there are :-)
    current = datastructures
    next = None
    while L:
        while len(L[0]) > 0 and L[0][0] == '(':# up a level
            recdepth += 1
            current.append([])
            current = current[-1]
            L[0] = L[0][1:]

        strflag = False
        if len(L[0]) > 0 and L[0][0] == '"':# if we quote, we wrap up strings until we match it

            L[0] = L[0][1:]
            string = ''
            while L and not is_end(L[0]):
                string += L[0] + ' '
                del L[0]
            if L:
                c = is_end(L[0])#is the start of the true "
                string += L[0][:c]
                strflag = True

            L.insert(1, string)

        while L and len(L[0]) > 0 and  L[0][-1] == ')':# down a level
            recdepth -= 1
            if recdepth < 0:
                raise Warning('Too many closing parentheses, too few opening ones. File: {}'.format(levelname))
            next = _sarray(datastructures, recdepth)# move up a level
            L[0] = L[0][:-1]

        if strflag:# may be buggy
            del L[0]

        if L[0] != '':
            current.append(L[0])
        del L[0]

        if next is not None:
            current = next
            next = None

    if recdepth > 0:
        raise Warning('Not all parentheses have been closed. File: {}'.format(levelname))

    return datastructures

def is_end(string):
    for i in range(len(string)):
        if string[i] == '"':
            if string[i-1] != '\\':
                return i
    return False

def _sarray(a, depth):
    if depth == 0:
        return a
    if depth == 1:
        return a[-1]
    return _sarray(a[-1], depth - 1)

def make_real(D):
    global introtext, rooms, objects, extrotext, current_room, score, globalscripts, defaultcommands, callables

    rooms, objects = {},{}
    introtext,extrotext,current_room,score = [],[],'',0
    globalscripts, defaultcommands = {},{}

    callables = {}

    print60('The string of the parsed file is '+str(len(repr(D)))+' characters long.')


    # DARN: How to organize these?
    # Classes: Must be loaded before objects; recursively do so..
    # Objects, Rooms, Self: after classes

    # functions, intro/extro/pos/score stuff to be done later.
    # Now, once the entire thing is loaded, we can shuffle/split things!

    # 4 locals, all in make-real
    # classes = [ghash]; keyword Class
    # things = [bhash]; Object,Room,Self, (derivatives as per classes); marked by first letter caps!

    # gamestuff = [shash]; intro,extro,pos,score
    # scripts = [mhash]; methods, defcoms, anything that is executable. scripts are just instructions, and thus have no class

    # Step 1: seperate things

    classes = {}
    things = []
    # clear out rest
    for block in D:
        # class
        if block[0] == 'Class':
            # Class Type (extends Things) (counter magical? True)
            classes[block[1]] = (block[2][1:], block[3:])
        # gamespecs
        if block[0] == 'introtext':
            introtext = block[1:]
        elif block[0] == 'extrotext':
            extrotext = block[1:]
        elif block[0] == 'position':
            current_room = block[1]
        elif block[0] == 'score':
            score = block[1]
        # functions
        elif block[0] == 'pyf':
            callables[block[1][0]] = PyF(block[1][0], block[2])
        elif block[0] == 'pyq':
            callables[block[1][0]] = PyQ(block[1][0], block[2])
        # Just unify Func and Ques into ... Script? Function?; just func!, and make exec,eval be builtin!; and add tco, lists, etc.pp.
        elif block[0] in ('func','ques'):
            callables[block[1][0]] = Func(block[1][0], block[1][1:], block[2:])
        # commands
        elif block[0] == 'defcom':
            defaultcommands[block[1]] = block[1:]
        elif block[0] == 'globalmethod':
            for c in block[1:-1]:
                globalscripts[c] = block[-1]
        # daemons
        elif block[0] == 'daemon':
            temp = Daemon(_ddictify(block[1:]))
            callables[temp.get_label()] = temp

        # the Things
        elif block[0][0].isupper():
            things.append(block)
        else:
            print('"{}" not understood in "make_real".'.format(block))


    for tb in things:
        if tb[0] == "Room":
            key, dd = _dictify(tb[1:])
            rooms[key] = Room(key, dd)
        elif tb[0] == "Self":
            key, dd = _dictify(tb[1:])
            tmp = Self(key, dd)
            rooms[key] = tmp
            objects[key] = tmp
        elif tb[0] == "Object":
            key, dd = _dictify(tb[1:])
            objects[key] = Object(key,dd)
        elif tb[0] in classes:
            key, dd = _dictify(tb[1:])
            dd = _ac(dd, classes[tb[0]], classes)
            objects[key] = Object(key, dd)

    print("There are", len(callables.keys()), "functions.")
    print("There are", len(objects), "objects.")
    print("There are", len(rooms), "rooms.")
    print("There are", len(classes), "classes.")

# TODO make, instead of (counter flumsy True), just (flumsy True)

def _ac(dd, added, classes):
    for thing in added[1]:
        if thing[0] in ('counter'):# adders
            # Don't override higher level counters
            if thing[1] not in (j[0] for j in dd['counter']):
                dd[thing[0]] += [thing[1:]]
        elif thing[0] == 'method':
            if 'method' not in dd:
                dd['method'] += [thing[1:]]
                continue
            for i in thing[1:-1]:
                if i in (j for k in dd['method'] for j in k[1:-1] ):
                    continue
                dd['method'] += [thing[1:]]

        else:# overwriters, ex. desc, name, weight, hidden, takeable False
            if thing[0] not in dd:
                dd[thing[0]] += [thing[1:]]

    if len(added[0]) > 0:
        for c in added[0]:
            if c != 'Object':
                # Object has no biases
                dd = _ac(dd, classes[c], classes)
    return dd

def _ddictify(b, seed=None):
    if seed is None:
        dd = defaultdict(list)
    else:
        dd = seed
    for obj in b:
        dd[obj[0]] += [obj[1:]]
    return dd

def _dictify(be, seed=None):
    if seed is None:
        dd = defaultdict(list)
    else:
        dd = seed

    for obj in be:
        if type(obj) == str:
            key = obj
        else:
            dd[obj[0]] += [obj[1:]]
    return key, dd

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Above we have the domain of parsing and loading

__all__ = ['Do Not Import * This File']# from CF import * is designed to fail

# Below we have the domain of scripting for the game

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class PythonScript():
    def __init__(self, name, body):
        self.body = body
        self.name = name

class PyF(PythonScript):
    def call(self, args):
        if SCRIPT_DEBUG:
            print("\'{}\' has been called with body \'{}\' and args \'{}\'.".format(self.name,self.body, args))
            exec(self.body.format(*args))
            print("\'{}\' is done.".format(self.name))
        else:
            exec(self.body.format(*args))
        return None

class PyQ(PythonScript):
    def call(self, args):
        if SCRIPT_DEBUG:
            print("\'{}\' has been called with body \'{}\' and args \'{}\'.".format(self.name,self.body, args))
            c = eval(self.body.format(*args))
            print('\'{}\' returns: '.format(self.name),c, type(c))
            return c
        else:
            return eval(self.body.format(*args))

class CompoundScript():
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = _badjust(body)


def _badjust(ist):
    # This is entry level adjustment: on script call or func/ques creation
    # If only a single command is called, unnest
    if len(ist) == 1 and type(ist[0]) is list:
        return ist[0]
    elif len(ist[0]) is not list:
        return ist
    # Otherwise, implicitly convert to one function
    else:
        print('ist', ist)
        return ['chain'] + ist

class Func(CompoundScript):
    def call(self, args):
        if SCRIPT_DEBUG:
            d = dict(zip(self.args, args))
            print("\'{}\' has been called with body \'{}\' and args \'{}\'.".format(self.name,self.body, d))
            c = exec_script(self.body, d)
            print('\'{}\' returns: '.format(self.name),c, type(c))
            return c
        else:
            return exec_script(self.body, dict(zip(self.args, args)))

def nested_dict_try(tree, d):
    """Maps a dictionary to a tree, only changing parts of the tree that are keys to the dictionary."""
    def t(s):
        try:
            return d[s]
        except KeyError:
            return s
    return nested_map(t, tree)


def _rfmap(l):
    """ Script execution function """

    global SCRIPT_DEBUG

    # while there are ... control flow items governed by questions
    # control flow does not move down a functional level
    while type(l) is list and l[0] in ('if','let','or','and'):
        if l[0] == 'if':
            j = 1
            while j < len(l) - 1:
                if (type(l[j]) is list and _rfmap(l[j])) or (type(l[j]) is not list and l[j]):
                    break
                j += 2

            if j + 1 == len(l):
                l =  l[j]
            elif j == len(l):
                return None
            else:
                l = l[j+1]
        elif l[0] == 'let':
            #if SCRIPT_DEBUG:
                #print("'let'-ting '{}' become '{}' over section '{}'.".format(l[1],l[2],l[3]))
            l = nested_dict_try(l[3], {l[1]:_rfmap(l[2])})
            #if SCRIPT_DEBUG:
                #print("'let' is done, with section altered to '{}'.".format(l))
        elif l[0] == 'and':
            for i in l[1:]:
                if (type(i) is list and not _rfmap(i)) or (type(i) is not list and not i):
                    return False
            return True
        elif l[0] == 'or':
            for i in l[1:]:
                if (type(i) is list and _rfmap(i)) or (type(i) is not list and i):
                    return True
            return False
    if type(l) is not list:
        return l

    #if SCRIPT_DEBUG:
        #if l[0] == 'chain':
            #print("'chain'-ing begins with body: '{}'.".format(l[1:]))

    # Reduce free contents
    for i in range(1,len(l)):
        if type(l[i]) == list:
            l[i] = _rfmap(l[i])

    # Kill 'chain' operator: the items have func'ed out
    if l[0] == 'chain':
        if SCRIPT_DEBUG:
            #print("'chain'-ing is done", end='')
            if len(l) > 1:
                #print(" and returns: ", l[-1], type(l[-1]))
                return l[-1]# return the last thing, usually None
            #print(".")
            return None
        else:
            if len(l) > 1:
                return l[-1]# return the last thing, usually None
            return None


    # builtins: yay!

    # string-concat with spaces inserted
    if l[0] == 'join':
        if SCRIPT_DEBUG:
            print("'join' is called with args '{}'".format(l[1:]))
        st = ""
        for sst in l[1:]:
            if sst is not None:
                st += sst + " "
        if SCRIPT_DEBUG:
            print("'join' is done and returns '{}'.".format(st[:-1]))
        return st[:-1]

    # string format; formats 1st with rest of args
    if l[0] == 'format':
        if SCRIPT_DEBUG:
            print("'join' is called on '{}' with args '{}'".format(l[1], l[2:]))
        l = l[1].format(*l[2:])
        if SCRIPT_DEBUG:
            print("'join' is done and returns '{}'.".format(l))
        return l

    # choose one of the args (if a value)
    elif l[0] == 'randomc':
        return random.choice([st for st in l[1:] if st is not None])

    if l[0] in callables:
        return callables[l[0]].call(l[1:])
    print(l[0], 'does not exist. (It was called anyway.)')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Above we have scripting

class Daemon():
    def __init__(self, dd):
        n = []
        self.counters = []
        self.step = [['pass']]
        for key in dd:
            if key == 'counter':
                self.counters = dd['counter']
            elif key == 'step':
                self.step = dd['step'][0]
            else:
                self.label = key
                self.args = dd[key][0]

    def get_label(self):
        return self.label

    def call(self, args):
        if len(self.args) != len(args):
            raise Warning('Daemon called with incorrect number of arguments.')
        # ADD A SCRIPT_DEBUG to this
        d = dict(zip(self.args, args))
        if SCRIPT_DEBUG:
            print("'{0}' has been created with args '{1}'.".format(self.label, d))
        c = nested_dict_try( deepcopy(self.counters), d)
        s = nested_dict_try( deepcopy(self.step), d)

        key = args[0]#args[0] is reserved for the tag. integer tags or similar are always also _possible_, bt whatever

        running_daemons[key] = RunningDaemon(key, c, s)

        return None

# and all that really distinguishes _dmap is ... (set!, which works on local variables. all else is copy and paste
class RunningDaemon():
    def __init__(self, key, counters, step):
        self.key = key
        self.counters = dict(counters)
        # you see, [step, [com], [com], [com]]
        # needs 'chain' to hold them all together.
        # however, [step, [chain blah]] is too nested for code
        # so I add it in later
        self.step = ['chain'] + step

    def set_counter(self, name, value):#
        if name in self.counters:
            self.counters[name] = value
        else:
            print("Counter '{}' does not exist for daemon '{}'.".format(name, self.key))
    def get_counter(self, name):
        try:
            return self.counters[name]
        except IndexError:
            print("Counter '{}' does not exist for daemon '{}'.".format(name, self.key))


    def poll(self):
        if SCRIPT_DEBUG:
            print("'{0}' has been polled with counters '{1}' and body '{2}'.".format(self.key, self.counters, self.step))
        self._dmap(deepcopy(self.step))
        if SCRIPT_DEBUG:
            print("'{0}' is done.".format(self.key))

    # ### dmap
    # if; sret
    # chain; sret
    # let; sret
    # x command
    #
    def _dmap(self, s):

        # while there are ... control flow items governed by questions
        # control flow does not recall rfmap
        while type(s) is list and s[0] in ('if','let'):
            if s[0] == 'if':
                j = 1
                while j < len(s) - 1:
                    if (type(s[j]) is list and self._dmap(s[j])) or (type(s[j]) is not list and s[j]):
                        break
                    j += 2

                if j + 1 == len(s):
                    s =  s[j]
                elif j == len(s):
                    return None
                else:
                    s = s[j+1]
            elif s[0] == 'let':
                s = nested_dict_try(s[3], {s[1]:self._dmap(s[2])})

        if type(s) is not list:
            return s

        # the lazy or
        if s[0] == 'or':
            for i in s[1:]:
                if type(i) == list:
                    if self._dmap(i):
                        return True
                else:
                    try:
                        i = self.counters[i]
                    except KeyError:
                        pass
                    if i:
                        return True
            return False

        # the lazy and
        if s[0] == 'and':
            for i in s[1:]:
                if type(i) == list:
                    if (not self._dmap(i)):
                        return False
                else:
                    try:
                        i = self.counters[i]
                    except KeyError:
                        pass
                    if not i:
                        return False
            return True

        # chain
        for i in range(1,len(s)):
            if type(s[i]) == list:
                s[i] = self._dmap(s[i])
        if s[0] == 'chain':
            return s[-1]

        # set! var value
        if s[0] == 'set!':
            # s2 has already been evaluated by the depth-first loop
            self.counters[s[1]] = s[2]
            return None

        # string concat with spaces
        if s[0] == 'join':
            st = ""
            for sst in s[1:]:
                if sst is not None:
                    st += sst + " "
            return st[:-1]

        if s[0] == 'randomc':
            return random.choice([st for st in s[1:] if st is not None])

        # command (with counters subbed in, as these are just labels)
        try:
            return callables[s[0]].call(dict_try(self.counters, s[1:]))
        except KeyError:
            print("'{}' does not exist. By extension, it cannot be called.".format(s[0]))

def dict_try(d, l):
    for i in range(len(l)):
        try:
            l[i] = d[l[i]]
        except KeyError:
            pass
    return l

# Below we have classes

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class Thing():
    def name(self):
        return self.names[0]

    def any_name(self):
        return random.choice(self.names)
    def remove_name(self, name):
        self.names.remove(name)
    def add_name(self, name):
        self.names.append(name)
    def get_names(self):
        for n in self.names:
            yield n

    def reset_key(self, k):
        self.key = k
    def change_description(self, newdesc):
        self.description
    def replace_desc(self, i, o):
        self.description = _desc_replace(self.description, i,o)

    def describe(self):
        return exec_script(['join'] + deepcopy(self.description),{'&':self.key})


class Container(Thing):
    def remove(self, obj, c=None):
        # c: count; None implies a unique object, a numeral one of a group
        if c is None:
            self.O.remove(obj)
        else:
            for o in self.O:
                if o.startswith(obj):
                    robj = o
            if objects[robj].count() <= c:
                self.O.remove(robj)
                del objects[robj]
                # the group disappears (memory saving: 2 groups, or 34?)
            else:
                objects[robj].decrease_amount(c)

    def add(self, obj, c=None):
        if c == None:
            self.O.append(obj)
        else:
            cname = base(obj)

            match = None
            t = self.key
            for o in self.O:
                if o.split('_') == [cname, t] or o == cname:
                    match = o

            if match is None:
                e = None
                for o2 in objects:
                    if o2.startswith(cname):
                        e = o2
                object_clone = deepcopy(objects[e])
                object_clone.set_amount(c)
                new_name = cname + '_' + self.key
                object_clone.reset_key(new_name)
                objects[new_name] = object_clone
                self.O.append(new_name)
            else:
                objects[match].increase_amount(c)

    def get_contents(self):
        for o in self.O:
            yield o

    def get_adj_contents(self):
        for o in self.O:
            yield base(o)

    # game access function. Alas, we have no lists
    def get_random_item(self):
        if len(self.O) > 0:
            return random.choice(self.O)
        return "NONE"


class Self(Container):
    # alas, extension sucks
    # The self effectively is a room (and an object, but it isn't visible) Room is good: it holds, but has extras

    def __init__(self, key, dd):
        self.key = key
        self.O = dd['objects'][0]

        if dd['desc']:
            self.description = dd['desc'][0]
        elif dd['description']:
            self.description = dd['description'][0]
        else:
            self.description = ['[insert description here]']

        self.maxstrength = dd['maxstrength'][0][0] + .95
        self.strength = dd['strength'][0][0] + .95
        self.speed = dd['speed'][0][0]

        self.names = dd['names'][0]

        self.methods = []
        if dd['method']:
            self.methods = dd['method']

        self.defcoms = []

        # 'self._calculate_load()' is delayed after all objects are loaded

    def is_takeable(self):
        return False
    def get_weight(self):
        return 0
    def get_nutritive_value(self):
        return False
    def is_key(self):
        return False
    def key_works(self):
        return False
    def is_visible(self):
        return False
    def count(self):
        return 1
    def is_group(self):
        return False
    def _expand_methods(self):
        self.defcoms = [k for k in defaultcommands.keys()]
        for com in self.methods:
            try:
                try:
                    self.defcoms.remove(com[0])
                except ValueError:
                    pass
            except IndexError:
                print("A method of '{}' is not fully created.".format(self.key))
                quit()
    def _expand_ugroup(self):
        return []
    def call(self, command):
        for m in self.methods:
            if self.trycommand(command, m[:-1], m[-1]):
                return True
        for d in self.defcoms:
            if self.trycommand(command, defaultcommands[d][:-1], defaultcommands[d][-1]):
                return True
        return False
    def trycommand(self, command, hooks, script):
        for hook in hooks:
            args = _match(copy(command), hook.split())
            if args is not False:
                args['%'] = self.names[0].upper()
                args['&'] = self.key
                exec_script(_badjust(script), args)
                return True
        return False

    def _calculate_load(self):
        self.current_load = 0
        for o in self.O:
            if objects[o].is_group():
                self.current_load += objects[objects[o].subs()].get_weight()*objects[o].count()
            else:
                self.current_load += objects[o].get_weight()

    def get_carrying_capacity(self):
        return int(self.strength) - self.current_load

    def decrease_load(self, amount):
        self.current_load -= amount

    def increase_load(self, amount):
        self.current_load += amount


    def feed(self, amount):
        self.strength += amount
        if self.strength > self.maxstrength:
            self.strength = self.maxstrength


    def get_strength(self):
        return int(self.strength)
    def set_strength(self, i):
        self.strength = int(i) + .95
    def set_max_strength(self, i):
        self.maxstrength = int(i) + .95
    def get_speed(self):
        return self.speed
    def set_speed(self, i):
        self.speed = int(i)

    def weaken(self, amount):
        old = int(self.strength)
        self.strength -= amount
        if self.strength <= 3:
            self.strength = 3.95
        new = int(self.strength)
        if old > new:
            print60("You are tiring. Your strength is now {}.".format(new))

    def sda(self):
        self.d = (i for i in (self.O + ['NONE']))
    def gda(self):
        return next(self.d)

    # tiring
    def sdl(self):# creates a new list
        self.c = self._drop_list()
    def gdl(self):# feeds in names to recursive function
        d = next(self.c)
        return d
    def _drop_list(self):
        wdiff = -self.get_carrying_capacity()
        while wdiff <= 0:
            yield "NONE"

        # create one: sort contents by objects (groups = 1 obj);
        # do .. start at small, iterate until right size/end
        # then append; do the recursive matcher in gamecode
        def tw(obj):
            c = objects[obj]
            if c.is_group():
                return obj, objects[c.subs()].get_weight() * c.count()
            return obj, c.get_weight()
        # sort by name term using weight
        slist = sorted([tw(o) for o in self.O], key=lambda x: x[1])
        # create droplist
        droplist = []
        while wdiff >= 0:
            f = False
            for i in slist:
                if i[1] > wdiff:
                    droplist.append(i[0])
                    wdiff -= i[1]
                    del i
                    f = True
                    break
            if not f:
                droplist.append(slist[-1][0])
                wdiff -= slist[-1][1]
                del slist[-1]

        while droplist:
            yield droplist.pop()
        yield "NONE"

class Room(Container):
    def __init__(self, key, dd):
        self.key = key

        self.O = []
        if dd['objects']:
            self.O = dd['objects'][0]
        random.shuffle(self.O)

        if dd['desc']:
            self.description = dd['desc'][0]
        elif dd['description']:
            self.description = dd['description'][0]
        else:
            self.description = ['[insert description here]']

        self.names = dd['names'][0]

        #                      n        e        s        w
        self.connections = [["WALL"],["WALL"],["WALL"],["WALL"],['CEILING'],['FLOOR']]

        if dd['north']:
            self.connections[0] = dd['north'][0]
        if dd['east']:
            self.connections[1] = dd['east'][0]
        if dd['south']:
            self.connections[2] = dd['south'][0]
        if dd['west']:
            self.connections[3] = dd['west'][0]
        if dd['up']:
            self.connections[4] = dd['up'][0]
        if dd['down']:
            self.connections[5] = dd['down'][0]

        self.entryscript = None
        if dd['entryscript']:
            self.entryscript = dd['entryscript'][0][0]
        self.methods = {}
        if dd['method']:
            for m in dd['method']:
                for c in m[:-1]:
                    self.methods[c] = m[-1]


    def describe(self):
        stfl = exec_script(['join'] + deepcopy(self.description),{'&':self.key})
        for obj in self.O:
            c = objects[obj].tagtext()
            if c is not None and self.key not in objects[obj].tag_avoid():
                stfl += '\n' + c
        return stfl


    # script to be executed on entry, if it exists
    def enter(self):
        if self.entryscript is not None:
            exec_script(self.entryscript)
        return

    # 'wander "HAPPY YARGLE"' uses this
    def random_connection(self):
        for i in random_shuffled([j for j in range(6)]):
            if len(self.connections[i]) == 2:
                if self.connections[i][1] in rooms and self.connections[i][0] in ('DOOR OPEN','DOOR CLOSED'):
                    return self.connections[i][1]
        return "NONE"

    def get_door(self, direction):
        return self.connections[{'NORTH':0,"EAST":1,"SOUTH":2,"WEST":3,"UP":4,"DOWN":5}[direction]][0]

    # unlock door, open door, x door and so on need these
    def door_locked(self, d):
        i = {'NORTH':0,"EAST":1,"SOUTH":2,"WEST":3}[d]
        return (self.connections[i][0] == 'DOOR LOCKED')
    def neighbor(self, d):
        i = {'NORTH':0,"EAST":1,"SOUTH":2,"WEST":3}[d]
        return self.connections[i][1]
    def set_door(self, d, thing):
        i = {'NORTH':0,"EAST":1,"SOUTH":2,"WEST":3}[d]
        self.connections[i][0] = thing

    # local, called by (go dir) on a different room
    def _set_door(self, i, thing):
        self.connections[i][0] = thing

    def go(self, direction):
        c = {'NORTH':0,"EAST":1,"SOUTH":2,"WEST":3,"UP":4,"DOWN":5}[direction]

        if self.connections[c][0] in ('OPEN','DOOR OPEN'):
            print60('You go {}.'.format(direction.lower()))
            set_room(self.connections[c][1])
            look_at_room()

        elif self.connections[c][0] == "DOOR LOCKED":
            print60("You can't go through a locked door.")

        elif self.connections[c][0] == "DOOR OPEN":
            print60("You go {}.".format(direction.lower()))
            set_room(self.connections[c][1])
            look_at_room()

        elif self.connections[c][0] == "DOOR CLOSED":
            self.connections[c][0] = 'DOOR OPEN'
            rooms[self.connections[c][1]]._set_door({0:2,2:0,1:3,3:1}[c], 'DOOR OPEN')

            print60('You open the door and go {}.'.format(direction.lower()))
            set_room(self.connections[c][1])
            look_at_room()

        elif self.connections[c][0] == 'WALL':
            print60("You embrace the wall, but it does not yield.")

        elif self.connections[c][0] == 'FREE':
            if len(self.connections[c]) == 2:
                print60("You go {}.".format(direction.lower()))
            else:
                print60(self.connections[c][2])
            set_room(self.connections[c][1])
            look_at_room()

        else:
            if len(self.connections[c]) <= 2:
                print60('The {} is in the way.'.format(self.connections[c][0].lower()))
            else:
                print60(self.connections[c][2])

    # room based commands! (no arguments)
    def call(self, cs):
        try:
            exec_script( self.methods[cs] )
            return True
        except KeyError:
            pass
            return False

def random_shuffled(l):
    random.shuffle(l)
    return l


class Object(Thing):

    def __init__(self, key, dd, gameclass=None):
        self.key = key

        if dd['desc']:
            self.description = dd['desc'][0]
        elif dd['description']:
            self.description = dd['description'][0]
        else:
            self.description = ['[insert description here]']

        if dd['names']:
            self.names = dd['names'][0]
        else:
            self.names = [self.key.title()]

        self.group = None
        self.ugroup = None
        if dd['group']:
            self.group = dd['group'][0]
        if dd['ugroup']:
            self.ugroup = dd['ugroup'][0]

        self.keyo = None
        # could change to allow a multi-use key
        # I doubt it necessary
        if dd['key']:
            self.keyo = dd['key']


        self.takeable = True
        self.food = False
        self.weight = 1
        if dd['takeable']:
            self.takeable = dd['takeable'][0][0]
        if dd['food']:
            self.food = dd['food'][0][0]
        if dd['weight']:
            self.weight = dd['weight'][0][0]

        self.counters = {}
        self.methods = []
        if dd['counter']:
            for s in dd['counter']:
                self.counters[s[0]] = s[1]
        if dd['method']:
            self.methods = dd['method']

        self.visible = True
        if dd['hidden']:
            self.visible = False

        self.tag = None
        self.tagx = []
        if dd['tag']:
            self.tag = dd['tag'][0][0]
            self.tagx = dd['tag'][0][1:]

        self.defcoms = []


    # Post load method
    def _expand_ugroup(self):
        if self.ugroup is None:
            return []
        objlist = []
        k = []
        for i in range(self.ugroup[0]):
            object_clone = deepcopy(objects[self.ugroup[1]])
            new_name = self.ugroup[1] + '_' + str(i)
            object_clone.reset_key(new_name)
            k.append((new_name,object_clone))
            objlist.append(new_name)
        self.ugroup.append(objlist)
        return k

    # Post load method
    def _expand_methods(self):

        # should be a faster implementation method:
        # counting up, then down is baaad
        self.defcoms = [k for k in defaultcommands.keys()]
        for com in self.methods:
            try:
                try:
                    self.defcoms.remove(com[0])
                except ValueError:
                    pass
            except IndexError:
                print("A method of '{}' is not fully created.".format(self.key))
                quit()

    def is_takeable(self):
        return self.takeable
    def get_weight(self):
        return self.weight
    def set_weight(self, val):
        self.weight = val

    def get_nutritive_value(self):
        return self.food

    def tagtext(self):
        return self.tag
    def tag_avoid(self):
        return self.tagx

    def is_key(self):
        return (self.keyo is not None)
    def key_works(self, room1, room2):
        if self.keyo is None:
            return False
        for s in self.keyo:
            if (s[0] == room1 and s[1] == room2) or (s[1] == room1 and s[0] == room2):
                return True
        return False


    def is_visible(self):
        return self.visible
    def show(self):
        self.visible = True
    def hide(self):
        self.visible = False

    # 'group' and 'ugroup'
    def count(self):
        if self.group:
            return self.group[0]
        if self.ugroup:
            return self.ugroup[0]
        return 1
    def is_group(self):
        return ((self.group is not None) or (self.ugroup is not None))
    def subs(self):
        if self.is_ugroup():
            return self.ugroup[1]
        else:
            return self.group[1]
    # 'group'
    def decrease_amount(self, amount):
        self.group[0] -= amount
    def set_amount(self, amount):
        self.group[0] = amount
    def increase_amount(self, amount):
        self.group[0] += amount

    # 'ugroup'
    def get_group_objects():
        return self.ugroup[2]
    def is_ugroup(self):
        return (self.ugroup is not None)
    def set_ugroup(self, count, name, liste):
        self.ugroup = [count,name,liste]
    def remove(self, amount):
        if self.group is not None:
            self.group[0] -= amount
            if self.group[0] <= 0:
                return True
            return False
        if self.ugroup is not None:
            for i in range(amount):# Kill off the lowest u-numbers first
                del objects[self.ugroup[2][i]]
                del self.ugroup[2][i]
                self.ugroup[0] -= 1

            if self.ugroup[0] <= 0:
                return True
            return False
        return True
    def is_ugroup_member(self, name):
        return (name in self.ugroup[2])


    # counter interface
    def get_counter(self, name):
        try:
            return self.counters[name]
        except KeyError:
            print('Counter of name \'{}\' does not exist.'.format(name))

    def set_counter(self, name, value):# yes, this can create
        try:
            self.counters[name] = value
        except KeyError:
            print('Counter of name \'{}\' does not exist.'.format(name))

    # changes
    def set_action(self, key, action):
        for m in self.methods:
            if key in m[:-1]:
                m[-1] = action
                return
    def remove_action(self, key):
        for m in self.methods:
            if key in m[:-1]:
                del m
                return

    # Call center
    def call(self, command):
        # This can be one-linered: _smile_ :-)
        for m in self.methods:
            if self.trycommand(command, m[:-1], m[-1]):
                return True
        for d in self.defcoms:
            if self.trycommand(command, defaultcommands[d][:-1], defaultcommands[d][-1]):
                return True

        return False

    def trycommand(self, command, hooks, script):
        for hook in hooks:
            args = _match(copy(command), hook.split())
            if args is not False:
                args['%'] = self.names[0].upper()
                args['&'] = self.key
                if self.is_group():
                    args['#'] = self.subs()
                exec_script(_badjust(script), args)
                return True
        return False

# External Internal Functions :-) 'cause they are so abstract, I decouple them

def _match(given, wanted):
    # A length check does not work: things like $ on a multi-word
    # label would mess it up
    narray = {}

    for i in range(len(wanted)):
        if i == len(given):
            # wanted < given
            return False

        if wanted[i] == '@' and type(given[i]) == int:
            if given[i] == 1:
                return False
            narray['@'] = given[i]
        elif type(given[i]) == int and wanted[i] == str(given[i]):
            pass
        elif wanted[i][0] == '!':
            narray[wanted[i]] = given[i]

        elif wanted[i][0] == '$':# this allows $1, $2, $3,  $monkey, etc
            names = get_names()
            # trying names
            found = False

            for h in sorted( names.keys(), key=lambda x: len(x.split()), reverse=True):
                n = h.upper().split()
                lf = True

                if len(given) < i + len(n):
                    continue

                for w in range(len(n)):
                    if n[w] != given[i+w]:
                        lf = False
                        break

                if lf == True:
                    found = h
                    break

            # no names found
            if found is False:
                return False
            # match!
            given[i:i+len(n)] = [wanted[i]]
            narray[wanted[i]] = names[h][0]
        elif wanted[i] != given[i]:
            return False

    if len(wanted) != len(given):
        # wanted > given
        return False

    return narray

def _desc_replace(tree, k, j):
    for i in range(len(tree)):
        if type(tree[i]) == list:
            tree[i] = _desc_replace(tree[i], k, j)
        else:
            tree[i] = tree[i].replace(k, j)
    return tree

def get_names():

    # TODO: find out why, why partitives have: [['OBJ_SUB']*5] !

    # Very Important NOTE: THE SELF's OBJECTS ARE CHECKED FIRST
    # so that is the preference if there are, say, 15 cookies
    # on me and 5 in the room, I'll eat my cookies first:
    # if I drop cookies, I'll spawn  a 'COOKIES_ROOMNAME' object by the
    # same name (but in a different place). the underscore
    # is an escape char.

    # also, adjust so it has a preference order or disambiguation for several objects with the same name
    # ie. golden sword-sword, paper rapier->sword

    # and lastly, partitives create a '_SUB' tail, so no room may be called that :). MONKEYS_CHICKEN HOUSE_SUB can exist

    # create a name - OBJECTNAME mapping
    table = {}
    for o in rooms['SELF'].get_contents():
        for n in objects[o].get_names():
            if objects[o].is_group():
                for s in objects[objects[o].subs()].get_names():
                    table = _tableadd(table, s, o+'_SUB')
                if objects[o].count() > 1:
                    table = _tableadd(table, n, o)
            else:
                table = _tableadd(table, n, o)
    for o in rooms[current_room].get_contents():
        try:
            for n in objects[o].get_names():
                if objects[o].is_group():
                    for s in objects[objects[o].subs()].get_names():
                        table = _tableadd(table, s, o+'_SUB')
                    if objects[o].count() > 1:
                        table = _tableadd(table, n, o)
                else:
                    table = _tableadd(table, n, o)
        except KeyError:
            pass# The try, except exists only because the level ain't done yet
    return table

def _tableadd(table, key, val):
    # equivilant to defaultdict: replace
    if key in table:
        if val not in table[key]:
            table[key] += [val]
    else:
        table[key] = [val]
    return table

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def exec_script(script, argdict={}):
    return _rfmap( nested_dict_try(deepcopy(script), argdict))

def base(complexname):
    return complexname.split('_')[0]

def tail(complexname):
    return complexname.split('_')[-1]

def inl(obj, loc):
    return (obj in rooms[loc].get_contents())

def inn(obj, num, loc):
    rname = obj + "_" + loc
    try:
        if objects[rname].count() >= num:
            return True
        return False
    except KeyError:
        return False

def get_current_room():
    return current_room

def catch(thing):
    print('catching: ', thing, type(thing))
    return thing

def wait(t):
    try:
        time.sleep(t)
    except NameError:
        import time
        time.sleep(t)

def removen(obj, num, loc):
    rname = obj + "_" + loc
    if num <= objects[rname].count():
        if objects[rname].remove(num):
            rooms[loc].remove(rname)
            # no bytext; removen is designed to be purely functional, like the others

def move(obj, sork, dest, num=None):
    rooms[dest].add(obj, num)
    rooms[sork].remove(obj, num)

def set_room(room):
    global current_room
    current_room = room
    if current_room not in rooms:
        print('Room',current_room,'does not exist. Quitting.')
        quit()
    rooms[current_room].enter()
    return None

def look_at_room():
    try:
    # WAIT, then CLEAR
        print60()
        print60(rooms[current_room].name(), adjust='center')
        print60(rooms[current_room].describe())
    except KeyError:
        print('Room',current_room,'does not exist. Quitting.')
        quit()

def move_ugroup(st, dt, s, d, n):
    # Direct access ... injecting dissolved sugar straight to the heart of the problem

    # Create a new group if needed
    _make_dt(st, dt, d)

    # randomize sub-object order
    random.shuffle(objects[dt].ugroup[2])
    random.shuffle(objects[st].ugroup[2])

    # transfer n objects
    for i in range(n):
        objects[dt].ugroup[2] += [objects[st].ugroup[2].pop()]
        objects[dt].ugroup[0] += 1
        objects[st].ugroup[0] -= 1

    # remove source group if empty
    _empty_st(st, s)

def _make_dt(st, dt, d):
    if dt not in objects:
        object_clone = deepcopy(objects[st])
        object_clone.set_ugroup(0,objects[st].subs(),[])
        object_clone.reset_key(dt)
        objects[dt] = object_clone
        rooms[d].O.append(dt)

def _empty_st(st, s):
    if objects[st].count() == 0:
        del objects[st]
        rooms[s].O.remove(st)

def move_indiv_ugroup(moved, st, dt, sour, dest):
    _make_dt(st, dt, d)

    try:
        objects[st].ugroup[2].remove(moved)
        objects[st].ugroup[0] -= 1
        objects[dt].ugroup[0] += 1
        objects[dt].ugroup[2].append(moved)
    except ValueError:
        print('The sub-object to be moved was not in the source.')

    _empty_st(st, s)

def increase_score(amount):
    global score
    score += amount
    print_score()

def decrease_score(amount):
    global score
    score -= amount
    print_score()

def print_score():
    print60("Your score is {} out of 10.".format(score))
    print60("You have reached the rank of '{}'.".format(_rank(score)))

def _rank(s):
    if s <= 0:# less than 0 score dne, but whatever
        return "POND SCUM"
    elif s == 1:
        return "SERF"
    elif s <= 3:
        return "CRAFTSPERSON"
    elif s <= 5:
        return "MERCHANT"
    elif s <= 7:
        return "MERCENARY"
    elif s <= 9:
        return "KNIGHT"
    elif s == 10:
        return "LORD"
    else:
        return "CRAZY DEBUGGING GOD"
        # keep on placing yorgles; since these are stateless, there is not a problem

def stop_daemon(name):
    global daemon_kill_queue
    daemon_kill_queue.append(name)

def empty_daemons():
    global daemon_kill_queue
    for name in daemon_kill_queue:
        try:
            del running_daemons[name]
        except KeyError:
            print('We regret to inform you that \'{}\' could not be terminated. It never existed.'.format(name))
    daemon_kill_queue = []

def update_daemons():
    empty_daemons()
    for daemon in running_daemons.values():
        daemon.poll()
    empty_daemons()

#- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Post-load initializations:

LoadCastleData()# part of import process
# These can only be called once access to objects is available
rooms['SELF']._calculate_load()
nobjs = []
for o in objects:
    nobjs += objects[o]._expand_ugroup()
    objects[o]._expand_methods()

for pair in nobjs:# new objects created (uitems)
    objects[pair[0]] = pair[1]