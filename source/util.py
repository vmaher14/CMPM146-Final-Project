"util.py - Pyro utility functions"

# Attempt to import and use Psyco, the Python specializing compiler:
try:
    #raise ImportError   # Disable Psyco for now # CMPM 146 | This still raises in ImportError in python3, the except branch will follow so no changes.
    import psyco
    psyco.full()
    BASEOBJ = psyco.compact
except ImportError:
    BASEOBJ = object
    
import curses
import functools # CMPM 146 | reduce was moved to functools in python3 rather than built-in.
from random import choice, randint, uniform as rnd, normalvariate as norm, seed
from math import ceil

class GameOver(Exception): pass

############################## GLOBALS ##########################
class Global(BASEOBJ):
    KeyBuffer = ""
    FullDungeonRefresh = True

############################ CONSTANTS ##########################

MIN_STARTING_STAT = 2
letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Dungeon layout characters (data, not display, though they may be the same)
# These are the characters used by the dungeon generator to represent each square
WALL = "#"
FLOOR = "."
DOOR = "+"
LOCKED_DOOR = "X"
DUNGEON_CHARS = (WALL, FLOOR, DOOR, LOCKED_DOOR)

# Literal colors:
c_black = curses.COLOR_BLACK
c_blue = curses.COLOR_BLUE
c_cyan = curses.COLOR_CYAN
c_green = curses.COLOR_GREEN
c_magenta = curses.COLOR_MAGENTA
c_red = curses.COLOR_RED
c_white = curses.COLOR_WHITE
c_yellow = curses.COLOR_YELLOW
c_Black = curses.COLOR_BLACK + 8
c_Blue = curses.COLOR_BLUE + 8
c_Cyan = curses.COLOR_CYAN + 8
c_Green = curses.COLOR_GREEN + 8
c_Magenta = curses.COLOR_MAGENTA + 8
c_Red = curses.COLOR_RED + 8
c_White = curses.COLOR_WHITE + 8
c_Yellow = curses.COLOR_YELLOW + 8

colors = {
    'black':        c_black,
    'blue':         c_blue,
    'light blue':   c_Blue,
    'cyan':         c_cyan,
    'green':        c_green,
    'purple':       c_magenta,
    'red':          c_red,
    'gray':         c_white,
    'white':        c_White,
    'brown':        c_yellow,
    'yellow':       c_Yellow,
    'pink':         c_Red,
    'magenta':      c_Magenta,
    'shiny':        c_Cyan,
    'clear':        c_Cyan,
    'blood red':    c_red,
    'lime green':   c_Green,
}

msg_colors = {
    "k":    c_black,
    "b":     c_blue,
    "g":    c_green,
    "c":     c_cyan,
    "r":      c_red,
    "m":  c_magenta,
    "y":  c_magenta,
    "w":    c_white,
    "K":    c_Black,
    "B":     c_Blue,
    "G":    c_Green,
    "C":     c_Cyan,
    "R":      c_Red,
    "M":  c_Magenta,
    "Y":   c_Yellow,
    "W":    c_White,
}

# Keycodes:
k_up = 56
k_upright = 57
k_right = 54
k_downright = 51
k_down = 50
k_downleft = 49
k_left = 52
k_upleft = 55
k_center = 53

offsets = ((-1, 1), (0, 1), (1, 1), (-1 ,0),(0, 0),
           (1, 0), (-1, -1), (0, -1), (1, -1))
####################### CLASS DEFINITIONS #######################

class Logger(BASEOBJ):
    def __init__(self, filename):
        try:
            self.file = open(filename, "w")
            self.AddEntry("Log initialized.")
        except IOError:
            # Couldn't open the log file:
            self.file = None            
    def __call__(self, entry):
        self.AddEntry(entry)
        #print(entry)
    def __del__(self):
        if self.file:
            self.file.close()
    def AddEntry(self, entry):
        if self.file:
            self.file.write("%s\n" % entry)


####################### GLOBAL FUNCTIONS ########################

def cmp(a, b):
    return (a > b) - (a < b) 

def d(p1, p2=None):
    "Roll dice"
    try:
        num, kind, mod = p1+0, p2+0, 0  # Numeric parameters
    except TypeError:
        # String parameter in p1 like "2d6"
        num, kind = [s for s in p1.split("d")]
        num = int(num)
        L1 = kind.split("+")
        L2 = kind.split("-")
        if len(L1) > 1:
            kind = int(L1[0])
            mod = int(L1[1])
        elif len(L2) > 1:
            kind = int(L2[0])
            mod = -int(L2[1])
        else:
            kind = int(kind)
            mod = 0
    roll = 0
    for i in range(num):
        roll += irand(1, kind)
    return roll + mod

def seen(mob):
    "Return whether the mob is seen by the PC"
    return mob.is_pc or mob.pc_can_see

def delay(speed):
    "Return the delay for a given speed."
    # 100 is normal speed, resulting in 1000 delay.
    # 200 is twice as fast, 500 delay.
    # 50 is twice as slow, 2000 delay.
    return int(1000 * (100.0 / speed))

def irand(a, b, n=1):
    if a > b:
        a, b = b, a
    t = 0
    for i in range(n): # CMPM 146 | changed xrange to range
        t += randint(a, b)
    return int(round(t / n))

try:
    sum([])
except NameError:
    from operator import add
    def sum(data):
        if len(data) == 0:
            return 0
        return functools.reduce(add, data) # CMPM 146 | changed reduce to functools.reduce

def wrap(text, width):
    """
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).
    """
    return functools.reduce(lambda line, word, width=width: '%s%s%s' % # CMPM 146 | changed reduce to functools.reduce
                  (line,
                   ' \n'[(len(line)-line.rfind('\n')-1
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 ).split('\n')

def weighted_choice(lst):
    """
    Given a list like [[item1, wieght1], ..., [itemN, weightN]], with weights
    given as real numbers, return one of the items randomly according to weights.
    """
    n = rnd(0, sum([x[1] for x in lst]))
    for item, weight in lst:
        if n < weight:
            break
        n -= weight
    return item

def adjacent(a, b):
    """
    Return whether a is 8-way adjacent to b.  a and b need to have 
    .x and .y members.  Sitting on the same spot counts as adjacent.
    """
    return abs(a.x - b.x) < 2 and abs(a.y - b.y) < 2

def quantize(r):
    "Quantize a real number.  Returns int(r), and adds 1 if rnd(0, 1) < frac(r)."
    return int(r + rnd(0, 1))

def int_range(mean, std_dev=None, max_std_dev=2):
    "Return an random integer normally distributed around mean, with the given std dev."
    if std_dev is None:
        std_dev = mean / 4.0
    mean += 0.5
    return int(min(mean+std_dev*max_std_dev, max(norm(mean, std_dev), mean-std_dev*max_std_dev)))

def hit_chance(differential, level=1):
    "Return the chance to hit a target."
    # differential is attacker's to-hit bonus minus defender's evade bonus
    # level is the target's level; bonuses are diminished in effectiveness with higher levels
    # decay controls how fast the effectiveness of a hit/evade differential diminishes
    # with level.  
    # 0.933 = 1/2 at 10 and 1/4 at 20
    # 0.966 = 71% at 10, 1/2 at 20
    decay = 0.933
    mod = decay ** (level - 1) * 0.05 * (0.9 ** abs(differential) - 1) / -0.1
    if differential >= 0:
        return 0.5 + mod
    else:
        return 0.5 - mod
    
def successful_hit(differential, level=1):
    return rnd(0, 1) < hit_chance(differential, level)

def clen(s):
    "Return the length of a string, excluding embedded color codes."
    for c in list(msg_colors) + ["0"]: # CMPM 146 | dict_keys and list TypeError, changed to represent dict_keys as list
        s = s.replace("^"+c+"^", "")
    return len(s)
    
####################### INITIALIZATION ##########################

log = Logger("pyro.log")
