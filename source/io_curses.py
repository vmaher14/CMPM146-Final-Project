"io_curses.py - IO routines for Pyro, using curses."

# Ideally, this module could be replaced with a tile-graphics or other
# IO module without changing any of the rest of the Pyro code.

from util import *
import curses
import items

OPTIMIZE_OUTPUT = True      # Whether to buffer curses output (False won't work yet)
MESSAGE_LINES = 2

# Check what OS we're running under; keycodes differ:
WINDOWS = False
try:
    WINDOWS = 'WCurses' in curses.__version__
except AttributeError:
    pass


tiles = {
    # Terrain/features:
    "floor":            ".",
    "wall":             "#",
    "door_open":        "/",
    "door_closed":      "+",
    "trap":             "^",
    "stairs_up":        "<",
    "stairs_down":      ">",
    "fire":             "#",
    # Mobs:
    "player":           "@",
    "mob":              "x",    # The most generic mob tile, shouldn't be seen
    "ape":              "a",
    "ant":              "a",
    "bat":              "b",
    "centipede":        "c",
    "canine":           "d",
    "dragon":           "D",
    "eye":              "e",
    "feline":           "f",
    "goblin":           "g",
    "golem":            "G",
    "humanoid":         "h",
    "imp":              "i",
    "jelly":            "j",
    "kobold":           "k",
    "lizard":           "l",
    "mold":             "m",
    "ogre":             "O",
    "rodent":           "r",
    "spider":           "s",
    "snake":            "s",
    "troll":            "T",
    "undead":           "z",
    "lurker":           ".",
    "demon":            "&",
    # Items:
    "wand":             "/",
    "ring":             "=",
    "amulet":           '"',
    "stone":            "*",
    "armor":            "[",
    "melee_weapon":     "(",
    "missile_weapon":   "{",
    "tool":             "~",
    "scroll":           "?",
    "book":             "+",
    "potion":           "!",
    "food":             "%",
    "corpse":           "%",
    "ammunition":       "|",
    "money":            "$",
    # Misc:
    "unknown":          ";",
    "blank":            " ",
}

class IOWrapper(BASEOBJ):
    "Class to handle all input/output."
    def __init__(self):
        "Initialize the IO system."
        self.width, self.height = 80, 25
        # Initialize curses:
        self.screen = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(1)
        curses.curs_set(1)
        # Set up the color pairs:
        self.colors = [curses.color_pair(0)]
        for i in range(1, 16):
            curses.init_pair(i, i % 8, 0)
            if i < 8:
                self.colors.append(curses.color_pair(i))
            else:
                self.colors.append(curses.color_pair(i) | curses.A_BOLD)
        # Message area:
        self.message_lines = 2
        self.message_position = 0
        self.more_prompt = " ^Y^[more]^0^"
        self.any_key_prompt = "^Y^[Press any key]^0^"
        self.messages = []
        self.attack_ticker = []
        self.message_wait = False
        if OPTIMIZE_OUTPUT:
            # Optimize the screen output:
            self.screen = OptimizedScreen(self.screen, self.width,
                                          self.height, self.colors)
    def Shutdown(self):
        "Shut down the IO system."
        # Restore the terminal settings:
        self.screen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
    def _tile(self, tile_path):
        for tile in tile_path:
            try:
                return tiles[tile]
            except KeyError:
                continue
        return tiles["unknown"]
    def Refresh(self):
        return self.screen.refresh()
    def PutTile(self, x, y, tile, color):
        self.screen.PutChar(y+MESSAGE_LINES, x, self._tile(tile), color)
    def GetKey(self):
        "Return the next keystroke in queue, blocking if none."
        if Global.KeyBuffer:
            # Take the keystroke from the buffer if available
            # (for automated testing and maybe macros)
            k, Global.KeyBuffer = Global.KeyBuffer[0], Global.KeyBuffer[1:]
            return ord(k)
        k = 0
        while not 0 < k < 256:
            k = self.screen.getch()
        if WINDOWS or k != 27:
            return k
        else:
            k = self.screen.getch()
            if k != 79:
                raise ValueError("Unexpected escape sequence (27, %s)" % k)
            else:
                k = self.screen.getch()
                return k - 64
    def GetString(self, prompt, x=0, y=0, pattr=None, iattr=None,
                  max_length=999, noblank=False, nostrip=False):
        "Prompt the user for a string and return it."
        pattr = pattr or self.colors[0]
        iattr = iattr or self.colors[0]
        str = ""
        self.screen.addstr(y, x, prompt, pattr)
        x += len(prompt)
        while True:
            self.screen.move(y, x + len(str))
            self.screen.refresh()
            k = self.GetKey()
            if chr(k) in " 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
                str += chr(k)
            elif k == 8:
                # Backspace
                str = str[:-1]
            elif k in (10, 13):
                # Enter
                if str.strip() or not noblank:
                    if nostrip:
                        return str
                    else:
                        return str.strip()
            self.screen.addstr(y, x, str+" ", iattr)
    def GetDirection(self):
        "Ask the player for a direction."
        self.screen.addstr(0, 0, "Which direction? [1-9, or space to cancel]", c_yellow)
        self.screen.refresh()
        while True:
            k = self.GetKey()
            if k in range(49, 58):
                dx, dy = offsets[k-49]
                return k, dx, dy
            if k == 32:
                return None, None, None
    def ClearScreen(self):
        self.screen.clear()
    def ReportAttack(self, attacker, target, success, damage):
        "Report an attack."
        # success is true if the attack hit, even if damage is zero.
    def MorePrompt(self):
        if self.messages_displayed > 0:
            self.screen.addstr(0, self.wait_x, "[more]", c_Yellow)
            self.screen.refresh()
            self.GetKey()        
    def Message(self, msg, attr=c_yellow, nowait = False):
        "Display a message to the player, wrapping and pausing if necessary."
        if isinstance(msg, str):
            msg = [msg]
        for m in msg:
            if not m.strip():
                raise ValueError
            self.MorePrompt()
            self.screen.addstr(0, 0, " " * self.width, c_white)
            self.screen.addstr_color(0, 0, m, attr)
            self.screen.refresh()
            self.wait_x = clen(m) + 1
            if not nowait:
                self.messages_displayed += 1
    def ShowMessages_delete_me(self):
        # Show all messages from the previous turn:
        while self.messages:
            msg, attr = self.messages.pop(0)
            if self.messages:
                # Still some in the queue, so we need the more prompt:
                msg += self.more_prompt
                more = True
            else:
                more = False
            self.screen.addstr(0, 0, " " * self.width, c_white)
            self.screen.addstr_color(0, 0, msg, attr)
            self.screen.refresh()
            if more:
                self.GetKey()
    def CommandList(self, pc, lattr=c_yellow, hattr=c_Yellow):
        "Display the keyboard commands to the player."
        y = 1
        self.ClearScreen()
        self.screen.addstr(0, 5, "- Keyboard Commands -", hattr)
        for c in pc.commands:
            self.screen.addstr(y, 0, chr(c.key), hattr)
            self.screen.addstr(y, 2, "- %s" % c.desc, lattr)
            y += 1
        self.screen.addstr(y, 7, "[Press any key]", hattr)
        self.screen.refresh()
        self.GetKey()
        self.ClearScreen()
        return
    def Menu(self, items=[], x=0, y=0, doublewide=False, extra_opts="",
             prompt="Choose an option $opts$: ", question="", attr=None,
             key_attr=None, prompt_attr=None):
        "Display a list of choices to the user and get their choice."
        if not items:
            raise IndexError("Empty option list")
        attr = attr or self.colors[0]
        key_attr = key_attr or attr
        prompt_attr = prompt_attr or key_attr
        num = len(items)
        opts = ["a-%s" % letters[num-1]]
        opts.extend(extra_opts)
        disp_opts = []
        for o in opts:
            if o == ' ':
                disp_opts.append('space')
            else:
                disp_opts.append(o)
        prompt = prompt.replace('$opts$', "[%s]" % ", ".join(disp_opts))
        self.ClearScreen()
        if question:
            self.screen.addstr(y, x, question, prompt_attr)
            y += 1
        max_y = 0
        for i in range(num):
            if doublewide:
                max_item_width = (self.width - x) / 2 - 4
                if i < num / 2 + num % 2:
                    # left side
                    X = x
                    Y = y+i
                else:
                    # right side
                    X = self.width / 2
                    Y = y + i - num / 2 - num % 2
            else:
                max_item_width = self.width - x - 4
                X = x
                Y = y + i
            self.screen.addstr(Y, X, letters[i], key_attr)
            self.screen.addstr(Y, X+1, " - %s" % items[i][:max_item_width], attr)
            max_y = max(max_y, Y)
        self.screen.addstr(max_y+1, x, prompt, prompt_attr)
        self.screen.refresh()
        while True:
            try:
                ch = chr(self.GetKey())
            except ValueError:
                continue
            if ch in letters[:num] + extra_opts:
                return ch
    def BeginTurn(self):
        "Called right after input is taken from the player."
        self.screen.addstr(0, 0, " " * self.width, c_white)
        self.screen.addstr(1, 0, " " * self.width, c_white)
        self.messages_displayed = 0
    def EndTurn(self, pyro):
        "Called right before input is taken from the player."
        # Put the cursor on the @:
        self.screen.move(MESSAGE_LINES + pyro.game.pc.y, pyro.game.pc.x)
        self.screen.refresh()
    def ShowTicker(self):
        "Display the combat ticker."
        # First clear out old items:
        tick = Global.pyro.game.tick
        timeout = 10
        self.attack_ticker = [r for r in self.attack_ticker if tick - r[1] < timeout]
        s = ""
        for report in self.attack_ticker:
            r = report[0]
            if len(s) + len(r) + 1 <= self.width:
                if s:
                    s += " %s" % r
                else:
                    s = r
            else: break
        if s:
            self.screen.addstr(0, 0, " " * self.width, c_white)
            self.screen.addstr_color(0, 0, s, c_white)
    def ShowStatus(self, pyro, color=c_yellow):
        "Show key stats to the player."
        p = Global.pc
        exp_to_go = p.xp_for_next_level - p.xp
        if float(p.hp)/p.hp_max < 0.15:
            hp_col = "^R^"
        elif float(p.hp)/p.hp_max < 0.25:
            hp_col = "^Y^"
        else:
            hp_col = "^G^"
        if p.mp_max == 0 or float(p.mp)/p.mp_max < 0.2:
            mp_col = "^M^"
        else:
            mp_col = "^B^"
        stats = "Lvl:%s(%s) Str:%s Dex:%s Int:%s" % (p.level, exp_to_go, p.str, p.dex, p.int)
        hp = "%sHP:%s/%s^0^" % (hp_col, p.hp, p.hp_max)
        if p.mp_max > 0:
            mp = " %sMP:%s/%s^0^" % (mp_col, p.mp, p.mp_max)
        else:
            mp = ""
        if p.EvasionBonus() < p.RawEvasionBonus():
            ecolor = "^R^"
        else:
            ecolor = "^0^"
        armor = "Pr:%s Ev:%s%s^0^" % (p.ProtectionBonus(), ecolor, p.EvasionBonus())
        dlvl = "DLvl:%s" % p.current_level.depth
        line = "[%s]  [%s%s]  [%s]  [%s]" % (stats, hp, mp, armor, dlvl)
        self.screen.addstr(MESSAGE_LINES+p.current_level.height, 0,
                           " "*self.width, c_white)
        self.screen.addstr_color(MESSAGE_LINES+p.current_level.height, 0, line, color)
    def DisplayInventory(self, mob, norefresh=False, equipped=False):
        "Display inventory."
        self.ClearScreen()
        y = 0
        if equipped:
            title = "Equipped items"
        else:
            title = "Items in backpack"
        hattr, lattr, sattr = c_Yellow, c_yellow, c_White
        if mob.inventory.Num() == 0:
            # No items in the inventory:
            if mob.is_pc:
                self.screen.addstr(y, 0, "You are not carrying anything.", hattr)
            else:
                self.screen.addstr(y, 0, "The creature has no items.", hattr)
            self.screen.refresh()
            return y+1
        if mob.is_pc:
            weight = "(Total: %ss, Capacity: %ss)" % (
                mob.inventory.TotalWeight(), mob.inventory.Capacity())
        else:
            weight = ""
        self.screen.addstr(y, 0, "%s: %s" % (title, weight), hattr)
        y += 1
        for type, symbol in items.types:
            itemlist = [i for i in mob.inventory.ItemsOfType(type)
                        if (equipped and (i[0]==mob.wielded or i[0] in mob.equipped))
                        or (not equipped and not (i[0]==mob.wielded or i[0] in mob.equipped))]
            if itemlist:
                self.screen.addstr(y, 0, symbol, sattr)
                self.screen.addstr(y, 2, "%s:" % type, hattr)
                y += 1
                for i, letter in itemlist:
                    self.screen.addstr_color(y, 4, "^Y^%s^0^: %s" % 
                                             (letter, i.Name()), lattr)
                    y += 1
        if not norefresh:
            self.screen.refresh()
        return y
    def GetItemFromInventory(self, mob, prompt=None, equipped=False):
        "Ask the player to choose an item from inventory."
        hattr, lattr, sattr = c_Yellow, c_yellow, c_White
        need_refresh = True
        while True:
            if mob.inventory.Num() == 0: 
                y = self.DisplayInventory(mob, norefresh=True)
                self.screen.addstr(y, 0, "Press any key.", hattr)
                item = None
                self.screen.refresh()
                self.GetKey()
                break
            elif need_refresh:
                if prompt is None:
                    prompt = "Choose an item"
                if equipped:
                    other = "backpack"
                else:
                    other = "equipped items"
                y = self.DisplayInventory(mob, norefresh=True, equipped=equipped)
                pr = "%s (/ for %s, space to cancel): " % (prompt, other)
                self.screen.addstr(y, 0, pr, hattr)
                self.screen.refresh()
                need_refresh = False
            k = self.GetKey()
            if k == 32:
                item = None     # Cancelled by user; return None.
                break
            if k == 47:    # "/"
                equipped = not equipped
                need_refresh = True
            try:
                item = mob.inventory.GetItemByLetter(chr(k))
                if item is None:
                    continue
                break
            except ValueError:
                continue
        self.ClearScreen()
        return item
    def YesNo(self, question, attr=c_yellow):
        "Ask the player a yes or no question."
        self.MorePrompt()
        self.screen.addstr(0, 0, " " * self.width, c_white)
        self.screen.addstr(0, 0, "%s [y/n]: " % question, attr)
        self.screen.refresh()
        while True:
            k = self.GetKey()
            if k in (121, 89):
                answer = True
                break
            elif k in (110, 78):
                answer = False
                break
        self.screen.addstr(0, 0, " " * self.width, c_white)
        self.messages_displayed = 0
        return answer
    def Ask(self, question, opts, attr=c_yellow):
        "Ask the player a question."
        self.MorePrompt()
        self.screen.addstr(0, 0, " " * self.width, c_white)
        self.screen.addstr(0, 0, question, attr)
        self.screen.refresh()
        while True:
            k = self.GetKey()
            if chr(k) in opts:
                answer = chr(k)
                break
        self.screen.addstr(0, 0, " " * self.width, c_white)
        self.messages_displayed = 0
        return answer
    def WaitPrompt(self, y, attr=c_white, prompt="[Press Space]"):
        self.screen.addstr(y, 0, prompt, attr)
        self.screen.refresh()
        self.GetKey()
    def GetChoice(self, item_list, prompt="Choose one: ", nohelp=False, nocancel=True):
        "Allow the player to choose from a list of options with descriptions."
        # item_list must be a list of objects with attributes 'name' and 'desc'.
        if nohelp:
            ex = ""
        else:
            ex = "?"
        if not nocancel:
            ex += " "
            prompt += " (space to cancel) "
        choice = None
        while True:
            r = self.Menu([r.name for r in item_list],
                question=prompt, attr=c_yellow, key_attr=c_Yellow,
                doublewide=True, extra_opts=ex)
            if r == ' ':
                choice = None
                break
            if r in letters:
                # An item was chosen:
                choice = item_list[letters.index(r)]
                break
            if r == "?":
                # Show a description:
                r = self.Menu([r.name for r in item_list],
                    question="View description for which item? ",
                    attr=c_yellow, key_attr=c_Yellow,
                    doublewide=True)
                if r in letters:
                    self.ClearScreen()
                    y = 0
                    for line in wrap(item_list[letters.index(r)].desc, self.width-1):
                        self.screen.addstr(y, 0, line, c_yellow)
                        y += 1
                    self.WaitPrompt(y, c_Yellow)
        self.screen.clear()
        return choice
    def DisplayText(self, text, attr=c_white):
        "Display multiline text (\n separated) and wait for a keypress."
        self.ClearScreen()
        text = "\n".join(wrap(text, self.width-2))
        y = self.screen.addstr_color(0, 0, text, attr)
        self.screen.addstr_color(y+1, 0, self.any_key_prompt)
        self.screen.refresh()
        self.GetKey()
        self.ClearScreen()
    def CreatureSymbol(self, mob):
        "Return a message code for a mob's symbol."
        tile = self._tile(mob.tile)
        color = "^0^"
        for k in msg_colors:
            if msg_colors[k] == mob.color:
                color = "^%s^" % k
        return "%s%s^0^" % (color, tile)
    def ReportDamage(self, attacker, target, damage=0, result="hit"):
        "Report the results of an attack."
        att, tar = self.CreatureSymbol(attacker), self.CreatureSymbol(target)
        if attacker.is_pc: att = ""
        if target.is_pc: tar = ""
        if result == "hit":
            if attacker.is_pc:
                damage = "^G^%s^0^" % damage
            elif target.is_pc:
                damage = "^R^%s^0^" % damage
            else:
                damage = "^Y^%s^0^" % damage
            if damage == 0:
                damage = "^w^0^0^"
        elif result == "miss":
            damage = "^w^-^0^"
        report = ("%s%s%s" % (att, damage, tar), Global.pyro.game.tick)
        self.attack_ticker.insert(0, report)
    def DetailedStats(self, pc):
        "Show a detailed player stats screen."
        self.screen.clear()
        L = []
        L.append("^B^%s the level %s %s" % (pc.name, pc.level, pc.archetype.cname))
        L.append("")
        b = pc.MeleeDamageBonus()
        if b >= 0:
            b = "+%s" % b
        L.append("^Y^STR: %2s^0^  %s melee damage" % (pc.str, b))
        L.append("         %.2fs carried, eSTR: %2s" % (pc.inventory.TotalWeight(), pc.eSTR()))
        L.append("")
        b = pc.MeleeHitBonus()
        if b >= 0:
            b = "+%s" % b
        L.append("^Y^DEX: %2s^0^  %s to hit" % (pc.dex, b))
        b = pc.EvasionBonus()
        if b >= 0:
            b = "+%s" % b
        if pc.dex - 8 > pc.eSTR():
            limit = "^R^ [limited by eSTR]^0^"
        else:
            limit = ""
        L.append("         %s evasion%s" % (b, limit))
        L.append("")
        L.append("^Y^INT: %2s^0^  %s%% spell failure" % (pc.int, max(0, min(100, 25*(10-pc.int)))))
        L.append("         %s%% item use failure" % max(0, min(100, 25*(8-pc.int))))
        L.append("")
        y = 0
        for line in L:
            self.screen.addstr_color(y, 0, line, c_yellow)
            y += 1
        self.screen.addstr_color(y+1, 0, "^Y^[Press Space]")
        self.screen.refresh()
        self.GetKey()
        self.screen.clear()

class OptimizedScreen(BASEOBJ):
    "Optimized (buffered) wrapper for curses screen."
    def __init__(self, screen, width, height, colors):
        self.screen, self.width, self.height = screen, width, height
        self.colors = colors
        self.clear()
    def addstr(self, y, x, s, attr=c_white):
        strs = s.split("\n")
        for s in strs:
            self.screen.addstr(y, x, s, self.colors[attr])
            y += 1
        return y - 1
    def addstr_color(self, y, x, text, attr=c_white):
        "addstr with embedded color code support."
        # Color codes are ^color^, for instance,
        # "This is ^R^red text^W^ and this is white."
        buff = ""
        base_attr = attr
        while text:
            ch, text = text[0], text[1:]
            if ch == "^":
                if text[:2] == "0^":
                    text = text[2:]
                    y = self.addstr(y, x, buff, attr)
                    x += len(buff)
                    buff, ch = "", ""
                    attr = base_attr
                    continue
                for color in msg_colors.keys():
                    code = "%s^" % color
                    if text[:2] == code:
                        text = text[2:]
                        y = self.addstr(y, x, buff, attr)
                        x += len(buff)
                        buff, ch = "", ""
                        attr = msg_colors[color]
                        break
                else:
                    buff += ch
            else:
                buff += ch
        if buff:
            y = self.addstr(y, x, buff, attr)
        return y
    def clear(self):
        self.dattr = self.colors[0]
        self.chars = [[" "] * self.width for i in xrange(self.height)]
        self.attrs = [[self.colors[0]] * self.width for i in xrange(self.height)]
        self.cursor = [0, 0]
        self.screen.clear()
        self.screen.refresh()
        Global.FullDungeonRefresh = True
    def move(self, y, x):
        self.cursor = [y, x]
        self.screen.move(y, x)
    def getch(self):
        return self.screen.getch()
    def keypad(self, arg):
        return self.screen.keypad(arg)
    def refresh(self):
        self.screen.refresh()
        return
    def PutChar(self, y, x, ch, attr):
        if True or self.chars[y][x] != ch or self.attrs[y][x] != attr:
            self.addstr(y, x, ch, attr)
                    

        