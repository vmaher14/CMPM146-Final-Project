"player.py - Player character module for Pyro"


from util import *
import creatures
import races
import professions
import items
import fov
import dungeons

class PlayerCharacter(creatures.Creature):
    "The player character."
    tile = ["player"]
    color = c_White
    can_open_doors = True
    is_pc = True
    AIType = None       # The player makes the calls
    unarmed = items.Punch()
    xp_rate = 1.0   # 2.0 would need 2x the xp to level, 0.8 would need 20% less
    level, xp = 0, 0
    immortal = False
    equipped, unequipped = [], ["head", "torso", "hands", "waist", "feet", "finger",
                                "finger", "neck", "back", "offhand"]
    prev_x, prev_y = None, None
    wielded = None # Wielded weapon
    def __init__(self):
        Global.pc = self
        # Do generic creature initialization:
        creatures.Creature.__init__(self)
        # Set up bag-based inventory:
        self.bag = items.SmallBag()
        self.inventory = PlayerInventory(self)
        # Initialize commands:
        self._init_commands()
        # Let the player customize their character:
        Global.IO.ClearScreen()
        self.name = Global.IO.GetString("What is your name, adventurer? ", noblank=True,
                                 pattr=c_yellow, iattr=c_Yellow)
        Global.IO.ClearScreen()
        god = Global.IO.GetChoice([Krol, Dis], "Which god will you follow, %s?" % self.name)
        rprompt = "Choose your race, %s:" % self.name
        if god == Krol:
            self.archetype = Global.IO.GetChoice([KrolDwarf, KrolElf, KrolHuman], rprompt)(self)
        elif god == Dis:
            self.archetype = Global.IO.GetChoice([DisDwarf, DisElf, DisHuman], rprompt)(self)
        self.archetype.hp, self.archetype.mp = self.str, max(0, self.int - 7)
        self.hp_max, self.mp_max = self.archetype.hp, self.archetype.mp
        self.gain_str, self.gain_dex, self.gain_int = 1, 1, 1   # number of gains needed to go up a notch
        self.hp, self.mp = self.hp_max, self.mp_max
        self.move_speed = 100
        self.attack_speed = 100
        self.cast_speed = 100
        self.melee_tohit, self.melee_todamage = 0, 0
        self.missile_tohit, self.missile_todamage = 0, 0
        self.protection, self.evasion = 0, 0
        self.status = []    # Blind, poisoned, hasted, etc.
        self.GainLevel()    # Gain level 1
        self.heal_timer, self.mana_timer, self.last_timer = 0, 0, 0
        self.running, self.resting = False, False
    def __str__(self):
        # For debugging; allows "print pc" to give some info.
        return "Lv:%s St:%s Dx:%s Co:%s Iq:%s HP:%s MP:%s" % (
            self.level, self.str, self.dex, self.con, self.int, self.hp, self.mp)
    def _init_commands(self): # CMPM 146 | Maybe look into changing movement commands to arrow keys
        self.commands = []
        self.commands.append(Command("Show inventory", 105, self.Inventory))
        self.commands.append(Command("Show equipped items", 73, self.EquippedInventory))        
        self.commands.append(Command("Pick up items", 44, self.Pickup))
        self.commands.append(Command("Drop an item", 100, self.DropItem))
        self.commands.append(Command("Wield a weapon", 119, self.Wield))
        self.commands.append(Command("Wear armor or jewelry", 87, self.Wear))
        self.commands.append(Command("Auto-run", 47, self.BeginAutoRun))
        self.commands.append(Command("Rest until 100 turns or healed", 82, self.BeginAutoRest))
        self.commands.append(Command("Examine an item", 120, self.ExamineItem))
        self.commands.append(Command("Use a item", 46, self.UseItem))
        self.commands.append(Command("Close a door", 99, self.CloseDoor))
        self.commands.append(Command("Ascend staircase", 60, self.AscendStairs))
        self.commands.append(Command("Descend staircase", 62, self.DescendStairs))
        self.commands.append(Command("Detailed character info", 64, self.DetailedStats))
        self.commands.append(Command("List all commands", 63, self.CommandList))
        self.commands.append(Command("Quit (immedately)", 113, self.EndGame))
        self.commands.append(Command("Cheat menu", 67, self.Cheat))
    def XPNeeded(self, level):
        "Return the xp needed to attain the given level."
        if level > 1:
            return int(10 * self.xp_rate * 1.5 ** (level-1) + self.XPNeeded(level - 1))
        elif level == 1:
            return 0
        else: raise ValueError
    def GainXP(self, amount):
        self.xp += amount
    def GainStatPermanent(self, stat):
        if stat == "any":
            while True:
                k = Global.IO.Ask("Improve (S)trength, (D)exterity, or (I)ntelligence?", "sdiSDI", c_yellow)
                if k.upper() == "S":
                    self.GainStatPermanent('str')
                    return
                elif k.upper() == "D":
                    self.GainStatPermanent('dex')
                    return
                elif k.upper() == "I":
                    self.GainStatPermanent('int')
                    return
        if stat == "str":
            if self.gain_str > 0:
                self.gain_str -= 1
            if self.gain_str == 0:
                self.str += 1
                adj = "stronger"
            else:
                adj = "slightly stronger"
            self.gain_str = max(1, int((self.str-1) / 4) - 1)
        elif stat == "dex":
            if self.gain_dex > 0:
                self.gain_dex -= 1
            if self.gain_dex == 0:
                self.dex += 1
                adj = "more agile"
            else:
                adj = "slightly more agile"
            self.gain_dex = max(1, int((self.dex-1) / 4) - 1)
        elif stat == "int":
            if self.gain_int > 0:
                self.gain_int -= 1
            if self.gain_int == 0:
                self.int += 1
                adj = "smarter"
            else:
                adj = "slightly smarter"
            self.gain_int = max(1, int((self.int-1) / 4) - 1)
        else:
            raise ValueError(stat)
        Global.IO.Message("You feel %s!" % adj)
    def GainLevel(self):
        if self.level > 0:
            Global.IO.Message("Welcome to level ^G^%s^0^!" % (self.level+1))
        self.archetype.GainLevel()
        self.xp_for_next_level = self.XPNeeded(self.level + 1)
        if self.level > 1:
            Global.IO.ShowStatus(Global.pyro)
    def Die(self):
        if self.immortal:
            # Allow the player to refuse death:
            if not Global.IO.YesNo("Really die?"):
                self.hp = self.hp_max
                Global.IO.Message("You refuse to die!")
                return
        # PC has died; game is over:
        Global.IO.Message(["You die.", "."])    # 2nd msg forces -more-
        raise GameOver
    def Walk(self, dx, dy):
        "Try to move the specified amounts."
        px, py = self.x, self.y
        success, msg = creatures.Creature.Walk(self, dx, dy)
        if msg:
            Global.IO.Message(msg)
        if success:
            self.prev_x, self.prev_y = px, py
            if dx == dy == 0:
                # Don't describe if we didn't actually move:
                return True
            # Describe anything in the square:
            desc = ""
            for i in self.current_level.ItemsAt(self.x, self.y):
                self.running = False    # Stop if we're autorunning
                if desc:
                    desc = "There are several things lying here."
                    break
                desc = "There is a %s lying here." % i.Name()
            for f in self.current_level.FeaturesAt(self.x, self.y):
                self.running = False    # Stop if we're autorunning
                if desc:
                    break
                if f.describe:
                    desc = "There is a %s here." % f.name
            if desc:
                Global.IO.Message(desc)
            return True
        else:
            return False
    def Attack(self, target):
        "Attack the given creature."
        if self.wielded is None:
            attack = self.unarmed
        else:
            attack = self.wielded.melee_attack
        success = attack.Attempt(self, target)
    def AutoHeal(self):
        # See if the player heals any hp/mp:
        #if self.last_timer > self.timer:
         #   self.last_timer = self.timer
        self.heal_timer -= max(0, (self.timer - self.last_timer))
        self.last_timer = self.timer
        if self.heal_timer <= 0:
            turns = 30 - self.str
            self.heal_timer = 1000 * turns
            if self.hp < self.hp_max:
                self.hp += 1
            if self.hp > self.hp_max:
                self.hp -= 1
        # TODO: Move this to Creature
    def Update(self):
        "Called each turn; get the player's action and execute it."
        if self.hp <= 0:
            self.Die()
        self.AutoHeal()
        # Display the current level:
        Global.pyro.game.current_level.Display(Global.IO, self, is_pc=True)
        Global.IO.ShowStatus(Global.pyro)
        # See if the player has enough xp to gain a level:
        if self.xp >= self.xp_for_next_level:
            self.GainLevel()
        # Finalize display:
        Global.IO.EndTurn(Global.pyro)
        if self.running:
            # If autorunning, don't ask for a command:
            self.AutoRun()
        elif self.resting:
            self.AutoRest()
        else:
            # Get the player's command:
            k = Global.IO.GetKey()
            Global.IO.BeginTurn()
            if 48 < k < 58:
                # Movement key:
                dx, dy = offsets[k-49]
                self.Walk(dx, dy)
            # See if the key belongs to another defined command:
            try:
                [c for c in self.commands if c.key == k][0].function()
            except IndexError:
                pass
    def DescendStairs(self):
        self.UseStairs("descend")
    def AscendStairs(self):
        self.UseStairs("ascend")
    def UseStairs(self, action):
        try:
            stairs = [f for f in self.current_level.FeaturesAt(self.x, self.y)
                      if f.name in ("staircase up", "staircase down")][0]
        except IndexError:
            Global.IO.Message("There are no stairs here.")
            return False
        if action == "ascend":
            success, msg = stairs.Ascend(self)
        elif action == "descend":
            success, msg = stairs.Descend(self)
        else:
            raise ValueError
        if success:
            Global.IO.Message(msg)
        else:
            Global.IO.Message(msg)        
    def CloseDoor(self):
        "Close an adjacent door."
        adj = self.current_level.AdjacentSquares(self.x, self.y)
        doors = []
        for x, y in adj:
            try:
                door = [f for f in self.current_level.FeaturesAt(x, y)
                        if f.name == "door" and not f.closed][0]
                doors.append((x, y, door))
            except IndexError:
                continue
        if len(doors) == 0:
            success, msg = False, "There is nothing nearby to close."
        elif len(doors) == 1:
            # Just one door adjacent; close it:
            success, msg = door.Close(self)
        else:
            # Multiple doors nearby; ask the player which to close:
            k, dx, dy = Global.IO.GetDirection()
            if k == None:
                # cancelled
                return False
            else:
                try:
                    door = [f for f in self.current_level.FeaturesAt(
                        self.x+dx, self.y+dy) if f.name=="door" and not f.closed][0]
                    success, msg = door.Close(self)
                except IndexError:
                    success, msg = False, "There is no door there to close."
        Global.IO.Message(msg)
        return success
    def Inventory(self):
        Global.IO.DisplayInventory(self)
        Global.IO.GetKey()
        Global.IO.ClearScreen()
    def EquippedInventory(self):
        Global.IO.DisplayInventory(self, equipped=True)
        Global.IO.GetKey()
        Global.IO.ClearScreen()
    def Pickup(self):
        "Pick up items(s) at the current position."
        items = self.current_level.ItemsAt(self.x, self.y)
        if len(items) == 0:
            Global.IO.Message("There is nothing here to pick up.")
            return False
        elif len(items) == 1:
            success, msg = self.inventory.Pickup(items[0])
            Global.IO.Message(msg)
            return success
        else:
            any_success = False
            for i in items:
                if Global.IO.YesNo("Pick up the %s?" % i.Name()):
                    success, msg = self.inventory.Pickup(i)
                    Global.IO.Message(msg)
                    any_success = any_success or success
            return any_success
            
    def DropItem(self):
        "Drop an item on the floor."
        item = Global.IO.GetItemFromInventory(self, "Drop which item?")
        if item:
            success, msg = self.inventory.Drop(item)
            Global.IO.Message(msg)
            return success
    def CommandList(self):
        Global.IO.CommandList(self)
    def Wield(self, item=None, silent=False):
        "Let the player choose an item to wield as a weapon."
        if item is None:
            item = Global.IO.GetItemFromInventory(self, "Wield/unwield which item?")
        if item is None: return False  # Cancelled
        if self.wielded == item:
            # Select wielded item to unwield it:
            item = None
        creatures.Creature.Wield(self, item)
        if not silent:
            if item:
                Global.IO.Message("You are now wielding a %s." % item.name)
            else:
                Global.IO.Message("You are now wielding nothing.")
        return True
    def Wear(self):
        "Let the player choose an item to wear as jewelry or armor."
        item = Global.IO.GetItemFromInventory(self, "Wear/remove which item?")
        if item is None: return False   # Cancelled
        try:
            item.armor_slot
        except AttributeError:
            Global.IO.Message("You can't wear that item.")
            return False
        # If it's already equipped, remove it:
        if self.Unequip(item): return False
        # Item isn't equipped; see if there's an open slot:
        if item.armor_slot not in self.unequipped:
            # No slot available; free it up:
            worn = [i for i in self.equipped if i.armor_slot == item.armor_slot]
            if len(worn) == 1:
                self.Unequip(worn[0])
            elif len(worn) == 0:
                Global.IO.Message("That item doesn't fit your body.")
                return False
            else:
                # More than one item in that slot; ask which to remove:
                r = Global.IO.GetChoice(worn, "Remove which item?", nohelp=True)
                if r is None: return False
                self.Unequip(r)
        self.Equip(item)
    def UseItem(self):
        item = Global.IO.GetItemFromInventory(self, "Use which item?")
        if item is None: return False
        if item.type == "Potions":
            self.hp += 5
            if self.hp > self.hp_max:
                dif = self.hp - self.hp_max
                self.hp -= dif
            self.inventory.Remove(item)


    def ExamineItem(self):
        "Show a detailed description of an item."
        item = Global.IO.GetItemFromInventory(self, "Examine which item?")
        if item is None: return False   # Cancelled
        Global.IO.DisplayText(item.LongDescription(), c_yellow)
    def TakeDamage(self, amount, type=None, source=None):
        self.hp -= amount
        Global.IO.ReportDamage(source, self, damage=amount)
        return amount
    def BeginAutoRun(self):
        "Move in the given direction until something interesting happens."
        dir, dx, dy = Global.IO.GetDirection()
        if dir is None:
            return False
        if dx == dy == 0:
            self.BeginAutoRest()
            return
        else:
            self.running = True
        self.run_dx, self.run_dy, self.run_count = dx, dy, 0
        self.ran = [(self.x+x, self.y+y) for (x, y) in offsets if x==0 or y==0]
        try:
            self.ran.remove((self.x+dx, self.y+dy))
        except ValueError:
            pass
        self.run_in_room = False
        for x, y, w, h in self.current_level.layout.rooms:
            if (x <= self.x+dx < x+w) and (y <= self.y+dy < y+h):
                self.run_in_room = True
    def BeginAutoRest(self):
        self.resting = True
        self.run_count = 0
        Global.IO.Message("Resting...", nowait=True)
    def AutoRest(self):
        if self.run_count > 100 or self.FullyRested():
            self.resting = False
            Global.IO.Message("Done resting.")
            return
        if self.can_see_mobs:
            self.resting = False
            Global.IO.Message("You see an enemy and stop resting.")
            return
        self.run_count += 1
        self.Walk(0, 0)
    def FullyRested(self):
        return (True
            and self.hp >= self.hp_max
            and self.mp >= self.mp_max
        )
    def AutoRun(self):
        self.run_count += 1
        self.ran.append((self.x, self.y))
        mx, my = None, None
        if self.run_count > 1:
            for dx, dy in offsets:
                if ((dx == 0 or dy == 0) and (dx != dy )
                    and (self.x+dx != self.prev_x or self.y+dy != self.prev_y)):
                    for F in self.current_level.FeaturesAt(self.x+dx, self.y+dy):
                        if isinstance(F, dungeons.Door):
                            self.running = False
        if self.can_see_mobs:
            self.running = False
        if self.run_in_room:
            if self.SquareBlocked(self.x+self.run_dx, self.y+self.run_dy):
                self.running = False
            else:
                mx, my = self.run_dx, self.run_dy
        else:
            adj = self.AdjacentPassableSquares()
            adj = [s for s in adj if s not in self.ran and (s[0]==self.x or s[1]==self.y)]
            if len(adj) == 1:
                # Only one square we can move to other than the one we were just in:
                mx, my = adj[0][0]-self.x, adj[0][1]-self.y
            else:
                self.running = False
        if self.running:
            self.run_was_in_room = self.run_in_room
            self.run_in_room = False
            for x, y, w, h in self.current_level.layout.rooms:
                if (x <= self.x+mx < x+w) and (y <= self.y+my < y+h):
                    self.run_in_room = True
            if self.run_in_room != self.run_was_in_room and self.run_count > 1:
                self.running = False
                return
            self.Walk(mx, my)
    def AdjacentPassableSquares(self):
        "Return a list of adjacent squares the player can move into."
        adj = []
        for dx, dy in offsets:
            if (dx, dy) != (0, 0) and not self.SquareBlocked(self.x+dx, self.y+dy):
                adj.append((self.x+dx, self.y+dy))
            else:
                for F in self.current_level.FeaturesAt(self.x+dx, self.y+dy):
                    if F.potentially_passable:
                        adj.append((self.x+dx, self.y+dy))
        return adj
    def DetailedStats(self):
        "Show a detailed player stats screen."
        Global.IO.DetailedStats(self)
    def EndGame(self):
        if Global.IO.YesNo("Really quit the game?"):
            raise GameOver
    def Cheat(self):
        class Cheat:
            def __init__(self, name, desc, fn):
                self.name, self.desc, self.fn = name, desc, fn
        def cheat_hp():
            Global.pc.hp += 1000
        def cheat_omni():
            fov.OMNISCIENT_PLAYER = not fov.OMNISCIENT_PLAYER
        def cheat_level():
            Global.pc.GainXP(Global.pc.xp_for_next_level - Global.pc.xp)
        def cheat_immortal():
            Global.pc.immortal = not Global.pc.immortal
            if Global.pc.immortal:
                Global.IO.Message("You are now immortal and cannot die.")
            else:
                Global.IO.Message("You are once again subject to death.")
        def cheat_items():
            for i in range(20): # CMPM 146 | changed xrange to range
                while True:
                    dx, dy = irand(-3, 3), irand(-3, 3)
                    if dx*dx + dy*dy < 16: break
                if self.current_level.IsEmpty(self.x+dx, self.y+dy):
                    lvl = int_range(15, 5, 2)
                    self.current_level.AddItem(items.random_item(lvl), self.x+dx, self.y+dy)
        def cheat_genocide():
            for c in self.current_level.creatures.values():
                if c is not Global.pc:
                    c.Die()
        def cheat_stat():
            self.GainStatPermanent("any")
        cheats = [
            Cheat("Gain 1000 hit points", "", cheat_hp), 
            Cheat("Toggle omniscience", "", cheat_omni), 
            Cheat("Gain a level", "", cheat_level),
            Cheat("Toggle immortality", "", cheat_immortal), 
            Cheat("Items from heaven", "", cheat_items),
            Cheat("Kill all mobs in level", "", cheat_genocide),
            Cheat("Stat gain", "", cheat_stat),
        ]
        cheat = Global.IO.GetChoice(cheats, "Cheat how?", nocancel=False)
        if cheat is not None:
            cheat.fn()
        

class Command(BASEOBJ):
    "Any command the player can give has an instance of this class."
    long_desc = ""
    def __init__(self, desc, key, function):
        self.desc = desc
        self.key = key
        self.function = function
    

class PlayerInventory(creatures.Inventory):
    def TotalWeight(self):
        eq = sum([i.weight for i in self.mob.equipped])
        if self.mob.wielded is not None:
            eq += self.mob.wielded.weight
        pack = sum([i[0].weight for i in self.items if i[0] not in self.mob.equipped
                    and i[0] != self.mob.wielded]) * self.mob.bag.reduction
        return eq + pack
    def CanHold(self, item):
        return item.weight * self.mob.bag.reduction + self.TotalWeight() <= self.Capacity()
    
        
        
################################ GODS AND RACES #########################################

class Diety(BASEOBJ):
    pass
class Krol(Diety):
    name = "Krol"
    desc = """Almighty and vengeful Krol is the god of violent conflict.  Krol is not evil, though many who give him allegiance are.  Krol values strength and aggression, and expects his followers to overcome life's obstacles through overwhelming force.  Krol and his adherents are not known for subtlety or patience."""
class Dis(Diety):
    name = "Dis"
    desc = """Dis rules the shadowy realm of the Underworld.  Subtle and mysterious, he bestows upon his faithful the dark powers of stealth, trickery, and death."""
    
class Race(BASEOBJ):
    pass
class Dwarf(Race):
    name = "Dwarf"
    desc = """The steadfast Dwarves were old when the Elves arrived thousands of years ago."""
    
class Archetype(BASEOBJ):
    def __init__(self, pc):
        self.pc = pc
        self.gain_str, self.gain_dex, self.gain_int, self.gain_any = 0, 0, 0, 0
    def GainLevel(self):
        pc = self.pc
        pc.level += 1
        hp_gain, mp_gain = pc.str / 2, max(0, (pc.int - 7) / 2)
        self.hp += hp_gain
        pc.hp_max = int(self.hp)
        pc.hp += int(hp_gain)
        self.mp += mp_gain
        pc.mp_max = int(self.mp)
        pc.mp += int(mp_gain)
        if pc.level % 2 == 0:
            # Stat gain at even levels:
            stat, self.stat_gains = self.stat_gains[0], self.stat_gains[1:]
            pc.GainStatPermanent(stat)
            self.stat_gains.append(stat)
class KrolDwarf(Archetype):
    name = "Dwarf of Krol (Warrior)"
    cname = "Warrior"
    desc = """The Dwarves were old when the Humans and Elves arrived thousands of years ago, and the Dwarves will remain in their stone halls when the other races have come and gone.  The Warrior embodies the steadfast determination of his Dwarven ancestors.  He can withstand tremendous physical punishment, and his offensive skills are formidable."""
    def __init__(self, pc):
        armor = items.random_armor(-2, items.ChainShirt, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = items.random_melee_weapon(0, items.LongSword, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Wield(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.str, pc.dex, pc.int = 11, 8, 5
        self.stat_gains = ['str', 'dex', 'any', 'str']
class DisDwarf(Archetype):
    name = "Dwarf of Dis (Treasure Hunter)"
    cname = "Treasure Hunter"
    desc = """Dwarves are said to horde vast treasures in their mountan halls.  In keeping with the Dwarves' affinity with the earth, rare gems and precious metals are especially prized.  The Treasure Hunter is a tough-as-nails explorer who braves the dangers of the dungeon to retrieve the raw materials used by Dwarven smiths in their incomparable craftwork.  His skills are focused on observation and survival."""
    def __init__(self, pc):
        armor = items.random_armor(-2, items.Jerkin, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = items.random_melee_weapon(0, items.ShortSword, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Wield(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.str, pc.dex, pc.int = 8, 8, 8
        self.stat_gains = ['dex', 'any', 'str', 'any', 'int', 'any']
class KrolElf(Archetype):
    name = "Elf of Krol (Wizard)"
    cname = "Wizard"
    desc = """It is true that Krol values superior force over subtlety, but it would be a mistake to assume that all his followers are unsophisticated brutes.  The Wizard harnesses his formidable intellect to wield magical energies of tremendous power.  Though physically unimposing, the Wizard is the most powerful destructive force in the natural world."""
    def __init__(self, pc):
        armor = items.random_armor(-2, items.Robe, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = items.random_melee_weapon(0, items.Dagger, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Wield(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.str, pc.dex, pc.int = 5, 7, 12
        self.stat_gains = ['int', 'any', 'int']
class DisElf(Archetype):
    name = "Elf of Dis (Enchanter)"
    cname = "Enchanter"
    desc = """Although the Elves never grow old, they are not quite immortal and can die by violence.  Perhaps this fact, together with the Elves' naturally subtle disposition, explains why so many who choose to risk their lives in the dungeons follow the underworld god Dis.  Enchanters are versatile characters with a wide selection of spells, though not as powerful as those of the Wizard."""
    def __init__(self, pc):
        armor = items.random_armor(-2, items.Jerkin, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = items.random_melee_weapon(0, items.Dagger, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Wield(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.str, pc.dex, pc.int = 7, 7, 10
        self.stat_gains = ['int', 'any']
class KrolHuman(Archetype):
    name = "Human of Krol (Berserker)"
    cname = "Berserker"
    desc = """Humans have the briefest lives of all the natural races, which perhaps explains the fervor with which the Berserker serves his god Krol.  Unmatched in physical ferocity, the Berserker throws himself into battle without hesitation, consumed by the desire to kill for his god."""
    def __init__(self, pc):
        armor = items.random_armor(-2, items.Jerkin, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = items.random_melee_weapon(0, items.BattleAxe, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Wield(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.str, pc.dex, pc.int = 10, 10, 4
        self.stat_gains = ['str', 'dex', 'any', 'str', 'dex']
class DisHuman(Archetype):
    name = "Human of Dis (Assassin)"
    cname = "Assassin"
    desc = """Krol does not have a monopoly on violence--the Humans who follow the underworld god Dis are as deadly, and are perhaps even more feared for their mystery and subtlety.  The Assassin is a master of stealth and treachery, preferring to strike his enemy by surprise, and if possible, to finish the job with the first blow."""
    def __init__(self, pc):
        armor = items.random_armor(-2, items.Jerkin, nospecial=True)
        pc.inventory.Pickup(armor)
        pc.Equip(armor, silent=True)
        weapon = items.random_melee_weapon(0, items.Dagger, nospecial=True)
        pc.inventory.Pickup(weapon)
        pc.Wield(weapon, silent=True)
        Archetype.__init__(self, pc)
        pc.str, pc.dex, pc.int = 8, 11, 5
        self.stat_gains = ['dex', 'any', 'dex', 'str']

    
    
    
    