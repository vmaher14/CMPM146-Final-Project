"dungeons.py - Dungeon code for Pyro"

from util import *
import dungeon_gen
import fov
import creatures
from functools import cmp_to_key

class Dungeon(BASEOBJ):
    "An entire multilevel dungeon."
    def __init__(self, game):
        self.game = game
        self.levels = dict()
    def GetLevel(self, i):
        "Returns a Level object for the i'th level of this dungeon."
        try:
            return self.levels[i]
        except KeyError:
            self.levels[i] = self.NewLevel(i)
            return self.levels[i]
    def NewLevel(self, i):
        "Generate the i'th level of the dungeon."
        L = Level(self, i)
        return L

class Level(BASEOBJ):
    "A single level of a dungeon."
    def __init__(self, dungeon, depth):
        self.dungeon, self.depth = dungeon, depth
        self.creatures = {}
        self.items = []
        self.features = {}
        self.mob_actions = []
        self.dirty = {}
        self.layout = dungeon_gen.Level()
        self.width, self.height = self.layout.level_width, self.layout.level_height
        self.memento = [[[["blank"], c_white]] * self.width
                        for i in range(self.height)]
        self._add_doors()
        self._add_stairs()
        self._add_mobs()
        # Add some fire because I promised I would:
        x, y = self.RandomSquare()
        self.AddFeature(SmallFire(), x, y)
        self.fov = fov.FOVMap(self, self.width, self.height, self.BlocksVision)
    def _add_doors(self):
        "Remove the door terrain and put door features in its place."
        for x in range(self.layout.level_width):
            for y in range(self.layout.level_height):
                if self.layout.data[y][x] == DOOR:
                    self.layout.data[y][x] = FLOOR
                    self.AddFeature(Door(), x, y)
    def _add_stairs(self):
        "Add at least one up and one down staircase, not in the same room."
        self.up_room = choice(self.layout.rooms)
        self.down_room = choice([r for r in self.layout.rooms if r != self.up_room])
        x, y, w, h = self.up_room
        i, j = x + irand(1, w - 2), y + irand(1, h - 2)
        if self.depth == 1:
            self.AddFeature(TopStairs("up"), i, j)
        else:
            self.AddFeature(Staircase("up"), i, j)
        self.stairs_up = (i, j)
        x, y, w, h = self.down_room
        i, j = x + irand(1, w - 2), y + irand(1, h - 2)
        self.AddFeature(Staircase("down"), i, j)
        self.stairs_down = (i, j)
    def _add_mobs(self):
        "Add mobs to the level."
        # Add a random number of mobs to each room:
        # (Don't add in the first room of the first level)
        rooms = [room for room in self.layout.rooms 
                 if not(self.depth==1 and room==self.up_room)]
        for (x, y, w, h) in rooms:
            mobs = d("3d2-3")
            for m in range(mobs): # CMPM 146 | changed xrange to range
                for n in range(5):  # Try at most 5 times to find a spot:
                                    # CMPM 146 | changed xrange to range
                    i, j = irand(x, x+w-1), irand(y, y+h-1)
                    if not (self.CreaturesAt(i, j) or self.FeaturesAt(i, j)):
                        mob = creatures.RandomMob(self.depth)
                        self.AddCreature(mob, i, j)
                        break
                else:
                    log("Mob bailout on level %s" % self.depth)

    

    def compare(self, a, b):
        return (b.timer > a.timer) - (b.timer < a.timer)
    
    def Update(self):
        "Execute a single game turn."
        # Pull off the first mob, update it, stick it back in, sort:
        mob = self.mob_actions.pop()
        mob.Update()
        self.mob_actions.append(mob)
        # self.mob_actions.sort(lambda a, b: cmp(b.timer, a.timer))
        # self.mob_actions = sorted(self.mob_actions, key=lambda a: a.timer, reverse=True)
        # self.mob_actions = sorted(self.mob_actions, key=lambda a: a.timer) # CMPM 146 | sort by next lowest action timer
        self.mob_actions = sorted(self.mob_actions, key=lambda a: a.timer, reverse=True)

    def Dirty(self, x, y):
        "Mark the given square as needing to be repainted."
        self.dirty[(x, y)] = True
    def PaintSquare(self, x, y):
        # Start with the floor tile:
        if self.layout.data[y][x] == WALL:
            tile = ["wall"]
            color = c_white
        elif self.layout.data[y][x] == FLOOR:
            tile = ["floor"]
            color = c_white
        else:
            tile = ["unknown"]
        if self.fov.Lit(x, y):
            # Currently visible; display items/mobs:
            self.memento[y][x] = [tile, color]
            # Check for dungeon features:
            for feature in self.FeaturesAt(x, y):
                tile, color = feature.tile, feature.color
            # See if there are items:
            for item in self.ItemsAt(x, y):
                tile, color = item.tile, item.color
            self.memento[y][x] = [tile, color]
            # Check for mobs on the spot:
            for mob in self.CreaturesAt(x, y):
                tile = mob.tile
                color = mob.color
            if self.memento[y][x][0][0] == "floor":
                # Don't remember floor tiles; it makes the FOV more apparent:
                self.memento[y][x] = [["blank"], c_white]
        else:
            # Not in view; show memento:
            tile, color = self.memento[y][x]
        Global.IO.PutTile(x, y, tile, color)        
    def Display(self, IO, pov, is_pc=False):
        "Display the level on screen."
        # Figure out which squares are visible:
        self.fov.Update(pov.x, pov.y, 4, is_pc)
        # Display the level:
        painted = 0
        if Global.FullDungeonRefresh:
            Global.FullDungeonRefresh = False
            for x in range(self.width): # CMPM 146 | changed xrange to range
                for y in range(self.height): # CMPM 146 | changed xrange to range
                    painted += 1
                    self.PaintSquare(x, y)
        else:
            for x, y in self.dirty:
                self.PaintSquare(x, y)
                painted += 1
        #print "Painted %s dungeon squares." % painted
    def FeaturesAt(self, x, y):
        "Return a list of features at x, y."
        try:
            return [self.features[(x, y)]]
        except KeyError:
            return []
        #return [f for f in self.features if f.x == x and f.y == y]
    def CreaturesAt(self, x, y):
        "Return a list of creatures at x, y."
        try:
            return [self.creatures[(x, y)]]
        except KeyError:
            return []   # TODO: change this to None
    def AllCreatures(self):
        return self.creatures.values()
        # TODO: see where this is being used; might be inefficient.
    def ItemsAt(self, x, y):
        "Return a list of items at x, y."
        return [i for i in self.items if i.x == x and i.y == y]
    def BlocksVision(self, x, y):
        "Return whether the square at (x, y) blocks vision."
        if not (0 <= x < self.layout.level_width
        and 0 <= y < self.layout.level_height):
            # Squares outside the level are considered to block light:
            return True
        if self.layout.data[y][x] == WALL:
            return True
        for f in self.FeaturesAt(x, y):
            if f.block_type == WALL:
                return True
        return False
    def AdjacentSquares(self, x, y):
        "Return *coordinates of* the 8 adjacent squares to x, y."
        adj = []
        for i in range(x-1, x+2):
            for j in range(y-1, y+2):
                if (0 <= i < self.layout.level_width
                and 0 <= j < self.layout.level_height
                and not (i==x and j==y)):
                    adj.append((i, j))
        return adj
    def AddCreature(self, mob, x, y):
        "Add a mob to the level at position x, y."
        # Make sure the space isn't already occupied by a mob:
        try:
            self.creatures[(x, y)]
            raise ValueError("Tried to add a mob where one already was.")
        except KeyError:
            self.creatures[(x, y)] = mob
        mob.x, mob.y, mob.current_level = x, y, self
        if self.mob_actions:
            mob.timer = min([m.timer for m in self.mob_actions]) - 1
        else:
            mob.timer = 1000
        self.mob_actions.append(mob)
        self.Dirty(x, y)
    def MoveCreature(self, mob, new_x, new_y):
        "Move the creature to the specified place within the level."
        # Make sure the destination isn't occupied by another mob:
        try:
            self.creatures[(new_x, new_y)]
            raise ValueError("Tried to move a mob where one already was.")
        except KeyError:
            self.Dirty(mob.x, mob.y)
            del self.creatures[(mob.x, mob.y)]
            self.creatures[(new_x, new_y)] = mob
            mob.x, mob.y = new_x, new_y
            self.Dirty(mob.x, mob.y)
    def RemoveCreature(self, mob):
        "Remove the mob from the level."
        keys = [k for k in self.creatures if self.creatures[k] == mob]
        for k in keys:
            self.Dirty(self.creatures[k].x, self.creatures[k].y)
            del self.creatures[k]
        try:
            self.mob_actions.remove(mob)
        except ValueError: pass
    def AddFeature(self, feature, x, y):
        "Add a feature to the level at position x, y."
        # Make sure the space isn't already occupied:
        try:
            self.features[(x, y)]
            raise ValueError("Tried to add a feature where one already was.")
        except KeyError:
            self.features[(x, y)] = feature
        feature.x, feature.y, feature.current_level = x, y, self
        self.Dirty(x, y)
    def AddItem(self, item, x=None, y=None):
        "Add an item to the level at position x, y."
        if item not in self.items:
            if x is None or y is None:
                # Randomly place it somewhere in the level:
                x, y = self.RandomSquare()
            self.items.append(item)
        item.x, item.y, item.current_level = x, y, self
        self.Dirty(x, y)
    def RandomSquare(self):
        "Return coords of a non-wall, non-feature, non-corridor square."
        while True:
            room = choice(self.layout.rooms)
            x = irand(room[0], room[0]+room[2]-1)
            y = irand(room[1], room[1]+room[3]-1)
            if not self.FeaturesAt(x, y):
                return x, y
    def IsEmpty(self, x, y):
        "Return true if there is only empty floor at (x, y)."
        return (self.layout.data[y][x] == FLOOR
                and not self.FeaturesAt(x, y)
                and not self.CreaturesAt(x, y)
                and not self.ItemsAt(x, y))
        
class Feature(BASEOBJ):
    name = ">>no name<<"
    describe = True
    "Dungeon features (stairs, fountains, doors, etc)."
    block_type = FLOOR  # By default features do not block movement.
    tile = ["unknown"]
    color = c_red
    potentially_passable = True
    def __init__(self):
        self.x, self.y, self.current_level = None, None, None

class Door(Feature):
    name = "door"
    describe = False
    def __init__(self):
        Feature.__init__(self)
        self.closed = True
        self.tile = ["door_closed"]
        self.color = c_yellow
        self.block_type = WALL  # Impassable while closed.
    def FailedMove(self, mob):
        self.Open(mob)
    def Open(self, mob):
        if mob.can_open_doors and self.closed:
            self.closed = False
            self.tile = ["door_open"]
            self.block_type = FLOOR
            # Opening is faster than closing to prevent an open-close dance with mobs
            mob.timer += delay(mob.move_speed * 1.5)
            if mob == Global.pc:
                Global.IO.Message("You open the door.")
            elif mob.pc_can_see:
                Global.IO.Message("%s opens the door." % mob.ArticleName())
            self.current_level.Dirty(self.x, self.y)
            return True
        return False
    def Close(self, mob):
        if mob.can_open_doors and not self.closed:
            for creature in self.current_level.CreaturesAt(self.x, self.y):
                return False, "The %s is blocking the door." % creature.name
            for item in self.current_level.ItemsAt(self.x, self.y):
                return False, "An item is keeping the door from closing."
            self.closed = True
            self.tile = ["door_closed"]
            self.block_type = WALL
            mob.timer += delay(mob.move_speed)
            self.current_level.Dirty(self.x, self.y)
            if mob.is_pc:
                return True, "You close the door."
class Staircase(Feature):
    color = c_white
    block_type = FLOOR
    name = "staircase"
    def __init__(self, direction):
        Feature.__init__(self)
        self.direction = direction
        if direction == "up":
            self.tile = ["stairs_up"]
            self.name = "staircase up"
        elif direction == "down":
            self.tile = ["stairs_down"]
            self.name = "staircase down"
        else:
            raise ValueError()  # CMPM 146 | changed ValueErrror() to ValueError.
                                # Not sure why there was a typo here, checked to see if it was defined but doesn't seem like it.
    def Ascend(self, mob):
        if self.direction != "up":
            return False, "These stairs do not lead up."
        d = self.current_level.dungeon
        L = d.GetLevel(self.current_level.depth - 1)    # Level the stairs lead to
        mob.current_level.RemoveCreature(mob)
        x, y = L.stairs_down
        L.AddCreature(mob, x, y)
        Global.pyro.game.current_level = L     # Can I get rid 
        Global.pyro.game.current_depth -= 1    # of these two?
        Global.FullDungeonRefresh = True
        return True, "You ascend the stairs."
    def Descend(self, mob):
        if self.direction != "down":
            return False, "These stairs do not lead down."
        d = self.current_level.dungeon
        L = d.GetLevel(self.current_level.depth + 1)    # Level the stairs lead to
        mob.current_level.RemoveCreature(mob)
        x, y = L.stairs_up
        L.AddCreature(mob, x, y)
        Global.pyro.game.current_level = L     # Can I get rid 
        Global.pyro.game.current_depth += 1    # of these two?
        Global.FullDungeonRefresh = True
        return True, "You descend the stairs."
            
class TopStairs(Staircase):
    def Ascend(self, mob):
        return False, "You can't leave without the widget!"

class SmallFire(Feature):
    color = c_Red
    tile = ["fire"]
    name = "small fire"