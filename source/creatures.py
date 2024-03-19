"creatures.py - Pyro creatures"

from util import *
import items
import dungeons
import astar
        
class Bite(items.MeleeAttackType):
    name = "bite"
    verbs = ["nibbles at", "bites", "chomps"]  # no damage, hit, crit
    verbs_fp = ["nibble at", "bite", "chomp"]
    damage = "1d4"
class Claw(items.MeleeAttackType):
    name = "claw"
    verbs = ["scratches at", "claws", "rends"]
    verbs_fp = ["scratch at", "claw", "rend"]
    damage = "1d4"


class AI(BASEOBJ):
    "Artificial intelligence for mobs."
    def __init__(self, mob):
        self.mob = mob

class Berserker(AI):
    """
    This AI routine wanders aimlessly until it sees the @.  Then it charges
    and fights to the death.
    """
    def __init__(self, mob):
        AI.__init__(self, mob)
        self.target = None
        self.tx, self.ty, self.dir = None, None, None
        self.state = "wander"
    def Update(self):
        "Take one action"
        pc = Global.pc
        #TODO: Generalize this to follow any mob, not just PC.
        if self.state == "wander":
            if self.dir == None:
                self.PickNewDirection()
            if self.mob.can_see_pc:
                self.state = "chase"
                return
            else:
                blocker = self.mob.SquareBlocked(self.mob.x+self.dx, self.mob.y+self.dy)
                if blocker is None:
                    self.mob.Walk(self.dx, self.dy)
                    return
                # The square is blocked; see if it's an openable door:
                if isinstance(blocker, dungeons.Door):
                    if self.mob.can_open_doors:
                        if not blocker.Open(self.mob):
                            # Tried and failed to open the door; waste some time:
                            self.mob.Walk(0, 0)
                        return
                self.PickNewDirection()
                return
        elif self.state == "chase":
            if adjacent(self.mob, pc):
                self.mob.Attack(pc)
                return
            if self.mob.can_see_pc:
                self.tx, self.ty = pc.x, pc.y
            else:
                if (self.mob.x, self.mob.y) == (self.tx, self.ty):
                    # We're at the last place we saw the @, and we still can't see him:
                    log("%s lost sight of its prey." % self.mob.name)
                    self.state = "wander"
                    return
            # We can see the PC, but are not in melee range: use A*:
            path = astar.path(self.mob.x, self.mob.y, self.tx, self.ty, 
                              self.mob.PathfindPass, max_length=10)
            if path:
                dx, dy = path[0][0] - self.mob.x, path[0][1] - self.mob.y
                self.mob.Walk(dx, dy)
                log("%s found a path from (%s, %s) to (%s, %s) %s." % 
                    (self.mob.name, self.mob.x, self.mob.y, self.tx, self.ty, path))
                return
            else:
                log("%s failed pathfinding." % self.mob.name)
                # Pathfinding failed, but we can see the @...just sit there and be mad:
                self.mob.Walk(0, 0)
                return
    def PickNewDirection(self):
        try:
            self.dir = choice([d for d in range(9) if d != 4
                              and not self.mob.SquareBlocked(
                                  self.mob.x+offsets[d][0],
                                  self.mob.y+offsets[d][1])])
            self.dx, self.dy = offsets[self.dir]
            return True
        except IndexError:
            # No options for movement:
            self.mob.Walk(0, 0)
            return False

class Creature(BASEOBJ):
    "An animate object."
    name = "Generic Creature"   # If this is seen in-game, it's a bug.
    can_open_doors = False
    is_pc, can_see_pc, pc_can_see = False, False, False
    # Default stats:
    str, dex, int = 8, 8, 8
    hp_max, mp_max = 10, 0
    tile = ["x"]
    color = c_Red
    AIType = Berserker
    unique = False
    dead = False
    level = 9999    # By default won't be generated
    wielded = None
    rarity = 1.0
    natural_armor = 0
    equipped, unequipped = [], []   # By default, no equip slots
    def __init__(self):
        self.x, self.y, self.current_level = 0, 0, None
        self.inventory = Inventory(self)
        if self.AIType:
            self.AI = self.AIType(self)
        self.move_speed = 100
        self.attack_speed = 100
        self.cast_speed = 100
        self.hp = self.hp_max
        self.kill_xp = int(max(self.level+1, 1.5 ** self.level))
        if not self.is_pc:
            # For now, have every mob drop a level-appropriate item:
            self.inventory.Pickup(items.random_item(int_range(self.level, self.level/4.0, 2)))
    def TakeDamage(self, amount, type=None, source=None):
        # This method can be overridden for special behavior (fire heals elemental, etc)
        self.hp -= amount
        Global.IO.ReportDamage(source, self, damage=amount)
        # Check for death:
        if self.hp <= 0:
            self.Die()
            if source is Global.pc:
                Global.pc.GainXP(self.kill_xp)
        return amount
    def Die(self):
        # Creature has been reduced to <=0 hp, or otherwise should die:
        self.inventory.DropAll()
        self.current_level.RemoveCreature(self)
        self.dead = True
    def ArticleName(self, article="the"):
        "Return the name with an appropriate article, if any."
        if self.unique:
            return self.name
        else:
            return "%s %s" % (article, self.name)
    def FailedMove(self, mob):
        # Something tried to move onto the mob; initiate an attack:
        mob.TryAttack(self)
    def CanOccupyTerrain(self, terrain):
        "Return whether the mob can enter a square with the given terrain."
        if terrain == FLOOR:
            return True
        return False
    def SquareBlocked(self, x, y):
        "Return the first thing, if any, blocking the square."
        L = self.current_level
        if not (0 <= x < L.layout.level_width
        and 0 <= y < L.layout.level_height):
            # Can't occupy squares outside the level no matter what:
            return WALL
        # Check whether another creature is there:
        for creature in L.CreaturesAt(x, y):
            return creature
        # Check whether the terrain type is passable:
        terrain = L.layout.data[y][x]
        if not self.CanOccupyTerrain(terrain):
            return WALL
        # Check whether there's an impassable feature (e.g. closed door):
        for feature in L.FeaturesAt(x, y):
            if not self.CanOccupyTerrain(feature.block_type):
                return feature
        return None
    def PathfindPass(self, x, y):
        "Return whether the square is passable for the pathfinder."
        b = self.SquareBlocked(x, y)
        return b is None or (isinstance(b, dungeons.Door) and self.can_open_doors)
    def Walk(self, dx, dy):
        "Try to move the specified amounts."
        msg = ""
        if dx == dy == 0:
            self.timer += delay(self.move_speed)
            return True, msg
        blocker = self.SquareBlocked(self.x+dx, self.y+dy)
        if blocker:
            # Something blocked the mob from moving--
            try:
                # Let the blocker respond if it can:
                msg = blocker.FailedMove(self)    
            except AttributeError:
                pass
            return False, msg
        else:
            self.current_level.MoveCreature(self, self.x + dx, self.y + dy)
            self.timer += delay(self.move_speed)
            return True, ""
    def Update(self):
        if self.dead:
            raise ValueError("Dead creature (%s) updated!" % self.name)
        self.AI.Update()
    def TryAttack(self, target):
        # Mob has tried to move onto another mob; possibly attack.
        # This would be the place to abort an attack on a friendly mob, etc.
        # TODO: implement the above so mobs won't attack each other
        # For now it's hacked:
        if self.is_pc or target.is_pc:
            self.Attack(target)
    def Attack(self, target):
        # If a weapon is wielded, attack with it:
        if self.wielded is not None:
            attack = self.wielded.melee_attack
        else:
            # Otherwise, randomly choose a natural attack and use it:
            attack = weighted_choice(self.attacks)
        success = attack.Attempt(self, target)
    def Wield(self, item):
        "Wield the item as a melee weapon."
        self.wielded = item
    def Equip(self, item, silent=False):
        # Equip the given item if possible:
        if item.armor_slot in self.unequipped:
            self.equipped.append(item)
            self.unequipped.remove(item.armor_slot)
            if self.is_pc and not silent:
                Global.IO.Message("You put on the %s." % item.Name())
            # TODO: equip hook
            return True
        else:
            return False
    def Unequip(self, item):
        # Unequip the given item if equipped:
        try:
            self.equipped.remove(item)
            self.unequipped.append(item.armor_slot)
            if self.is_pc:
                Global.IO.Message("You take off the %s." % item.Name())
            # TODO: unequip hook
            return True
        except ValueError:
            return False
    def MeleeDamageBonus(self):
        return self.str - 8
    def MeleeHitBonus(self):
        return self.dex - 8
    def ProtectionBonus(self):
        return (self.natural_armor + sum([a.armor_points for a in self.equipped])) / 10.0
        # TODO: include armor in the calculation
    def eSTR(self):
        "Return the excess strength stat."
        return int(max(0, self.str - ceil(self.inventory.TotalWeight())))
    def RawEvasionBonus(self):
        return self.dex - 8
    def EvasionBonus(self):
        return min(self.eSTR(), self.RawEvasionBonus())
                
class Inventory(BASEOBJ):
    "Inventory class for creatures and the player."
    def __init__(self, mob):
        self.mob = mob
        self.items = []
        self.capacity = mob.str * 10
    def Num(self):
        "Number of items in the inventory."
        return len(self.items)
    def TotalWeight(self):
        return sum([i[0].weight for i in self.items])
    def Capacity(self):
        return self.capacity
    def Add(self, item):
        letter = self.NextLetter()
        self.items.append((item, letter))
        return letter
    def Remove(self, item):
        self.items = [i for i in self.items if i[0] != item]
    def GetItemByLetter(self, letter):
        items = [i[0] for i in self.items if i[1] == letter]
        if len(items) == 0:
            return None
        elif len(items) == 1:
            return items[0]
        else:
            raise IndexError
    def NextLetter(self):
        "Return the first free letter."
        taken = [item[1] for item in self.items]
        for L in letters:
            if L not in taken:
                return L
        return None
    def CanHold(self, item):
        "Return whether the item can be picked up."
        return item.weight + self.TotalWeight() <= self.Capacity()
    def Pickup(self, item):
        if self.CanHold(item):
            # Add to inventory:
            letter = self.Add(item)
            # If it's sitting on the floor of a level, remove it from there:
            try:
                item.current_level.items.remove(item)
                item.current_level.Dirty(item.x, item.y)
            except AttributeError:
                pass
            item.current_level = None
            return True, "You pick up the %s (%s)." % (item.Name(), letter)
        else:
            return False, "You can't carry that much weight."
    def Drop(self, item):
        # If the item was wielded, unwield it first:
        if item == self.mob.wielded:
            self.mob.wielded = None
            unwield = "unwield and "
        else:
            unwield = ""
        # Put the item on the floor:
        self.mob.current_level.AddItem(item, self.mob.x, self.mob.y)
        # Remove it from inventory:
        self.Remove(item)
        return True, "You %sdrop the %s." % (unwield, item.Name())
    def DropAll(self):
        # Drop all inventory items--e.g. when the mob dies:
        for i in self.items:
            self.Drop(i[0])
    def ItemsOfType(self, type):
        # This should raise IndexError if an invalid type is given:
        [t for t in items.types if t[0] == type][0]
        # Return the list of items:
        it = [i for i in self.items if i[0].type == type]
        #it.sort(lambda a, b: cmp(a[1], b[1]))  # CMPM 146 | sort items using cmp, not present in py3. Explicitly defined globally in utils.
                                                # CMPM 146 | possible workaround: it = sorted(it)
        it = sorted(it, key=lambda a: a[1])
        return it
        
######################### CREATURE FAMILIES ############################
class Humanoid(Creature):
    tile = ["humanoid"]
    color = c_White
class Rodent(Creature):
    tile = ["rodent"]
    color = c_red
class Kobold(Creature):
    tile = ["kobold"]
    color = c_Green
class Goblin(Humanoid):
    tile = ["goblin"]
    color = c_green
    
####################### SPECIFIC CREATURE TYPES ########################

class Rat(Rodent):
    name = "rat"
    color = c_red
    hp_max = 5
    str, dex, int = 6, 6, 0
    level = 1
    attacks = [
        [Claw("1d2", 100), 2],
        [Bite("1d3", 100), 1],
    ]
    desc = """This rodent is definitely of an unusual size--you estimate it weighs
at least twenty pounds.  Its red eyes stare at you with no trace of fear."""
    
class WimpyKobold(Kobold):
    name = "kobold"
    can_open_doors = True
    hp_max = 6
    str, dex, int = 2, 6, 3
    level = 1
    attacks = [[items.Punch("1d3", 100), 1]]
    desc = """Kobolds are a vile race of dimunitive lizard-men with mottled
brownish-green scaly skin, dozens of small, sharp teeth.  They are not known for
their intellectual or physical prowess, although in groups they can be dangerous
(mostly due to their obnoxious odor)."""
    def __init__(self):
        Kobold.__init__(self)
        # Some kobolds carry weapons:
        if irand(0, 10) < 7:
            weapon = weighted_choice([
                (items.ShortSword(), 1),
                (items.Dagger(), 2),
                (items.Club(), 3),
                (items.Whip(), 0.5)])
            self.inventory.Pickup(weapon)
            self.wielded = weapon
    
class WimpyGoblin(Goblin):
    name = "goblin"
    can_open_doors = True
    hp_max = 7
    level = 2
    str, dex, int = 3, 6, 3
    desc = """You can just stretch the word "humanoid" to cover Goblins, if you're feeling
generous.  Short, stocky, fugly, green, and nasty pretty much fills in the rest."""
    def __init__(self):
        Goblin.__init__(self)
        # Goblins always carry weapons:
        weapon = weighted_choice([
            (items.ShortSword(), 3),
            (items.Club(), 4),
            (items.LongSword(), 1)])
        self.inventory.Pickup(weapon)
        self.wielded = weapon
        
class Wolf(Creature):
    name = "wolf"
    tile = ["canine"]
    color = c_White
    hp_max = 7
    level = 2
    str, dex, int = 5, 7, 1
    attacks = [(Bite("1d6", 100), 1)]
    move_speed = 110
    desc = """Your generic two-hundred-pound wolf.  Don't run; he's faster than you."""
    
class Imp(Creature):
    name = "imp"
    tile = ["imp"]
    color = c_Red
    hp_max = 4
    str, dex, int = 2, 10, 9
    move_speed = 110
    attacks = [(Claw("1d3", 160), 1)]
    level = 3
    desc = """Though small and weak, imps are phenomenally quick and very difficult to hit."""
        
class Ogre(Humanoid):
    name = "ogre"
    tile = ["ogre"]
    color = c_Yellow
    can_open_doors = True
    hp_max = 15
    str, dex, int = 14, 6, 3
    level = 4
    move_speed = 80
    attacks = [[items.Punch("1d3", 80), 1]]
    desc = """Ogres are gigantic humanoids, seven to nine feet tall and weighing up to 
eight hundred pounds.  Muscular and fat in roughly equal measure, they are deadly opponents 
in combat.  Luckily, they are rather slow."""
    
all = [Rat, WimpyKobold, WimpyGoblin, Wolf, Imp, Ogre]

def RandomMob(level):
    "Create and return a mob appropriate to the given dungeon level."
    mobs = [(mob, mob.rarity) for mob in all if -1 <= level - mob.level <= 1]
    mob = weighted_choice(mobs)
    return mob()

def PossibleMobs(level):
    possible = [(mob, mob.rarity) for mob in all if -1 <= level - mob.level <= 1]
    possible.append(None)
    return possible