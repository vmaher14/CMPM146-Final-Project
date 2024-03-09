"fov.py - FOV calculation for Pyro."

from util import *
# from sets import Set
    # CMPM 146 | sets is deprecated in py3. the function set() is now a built-in class in py3 and can be used without import.
    # This may break "dirty" square generation, might need to look into it

FOV_RADIUS = 6
OMNISCIENT_PLAYER = False

class FOVMap(BASEOBJ):
    # Multipliers for transforming coordinates to other octants:
    mult = [
                [1,  0,  0, -1, -1,  0,  0,  1],
                [0,  1, -1,  0,  0, -1,  1,  0],
                [0,  1,  1,  0,  0, -1, -1,  0],
                [1,  0,  0,  1, -1,  0,  0, -1]
            ]
    def __init__(self, level, width, height, blocked_function):
        # map should be a list of strings, one string per row of the map.
        self.level = level
        self.Blocked = blocked_function
        self.width, self.height = width, height
        self.lit_now, self.was_lit = set(), set()
    def Lit(self, x, y):
        return (x, y) in self.lit_now
    def _set_lit(self, x, y, is_pc):
        self.lit_now.add((x, y))
        if is_pc:
            # This is the PC's FOV; do some other stuff:
            for c in [m for m in self.level.CreaturesAt(x, y) if m != Global.pc]:
                c.can_see_pc = True
                c.pc_can_see = True
                Global.pc.can_see_mobs = True
                # TODO: Account for mob vision radius != pc's radius
    def _cast_light(self, cx, cy, row, start, end, radius,
                    xx, xy, yx, yy, id, is_pc):
        "Recursive lightcasting function"
        if start < end:
            return
        radius_squared = (radius+0.5)*(radius+0.5)
        for j in range(row, radius+1): # CMPM 146 | changed xrange to range
            dx, dy = -j-1, -j
            blocked = False
            while dx <= 0:
                dx += 1
                # Translate the dx, dy coordinates into map coordinates:
                X, Y = cx + dx * xx + dy * xy, cy + dx * yx + dy * yy
                # l_slope and r_slope store the slopes of the left and right
                # extremities of the square we're considering:
                l_slope, r_slope = (dx-0.5)/(dy+0.5), (dx+0.5)/(dy-0.5)
                if start < r_slope:
                    continue
                elif end > l_slope:
                    break
                else:
                    # Our light beam is touching this square; light it:
                    if dx*dx + dy*dy < radius_squared:
                        self._set_lit(X, Y, is_pc)
                    if blocked:
                        # we're scanning a row of blocked squares:
                        if self.Blocked(X, Y):
                            new_start = r_slope
                            continue
                        else:
                            blocked = False
                            start = new_start
                    else:
                        if self.Blocked(X, Y) and j < radius:
                            # This is a blocking square, start a child scan:
                            blocked = True
                            self._cast_light(cx, cy, j+1, start, l_slope,
                                             radius, xx, xy, yx, yy, id+1, is_pc)
                            new_start = r_slope
            # Row is scanned; do next row unless last square was blocked:
            if blocked:
                break
    def Update(self, x, y, radius, is_pc=False):
        "Calculate visible squares from the given location and radius"
        if is_pc:
            Global.pc.can_see_mobs = False
            for c in self.level.AllCreatures():
                c.can_see_pc = False
        self.was_lit, self.lit_now = self.lit_now, set()
        self._set_lit(x, y, is_pc)
        for oct in range(8): # CMPM 146 | changed xrange to range
            self._cast_light(x, y, 1, 1.0, 0.0, radius,  
                             self.mult[0][oct], self.mult[1][oct],
                             self.mult[2][oct], self.mult[3][oct], 0, is_pc)
        if OMNISCIENT_PLAYER:
            for i in range(self.width): # CMPM 146 | changed xrange to range
                for j in range(self.height): # CMPM 146 | changed xrange to range
                    self._set_lit(i, j, False)
        #print "Was lit: %s, Lit now: %s, Newly lit: %s" % (len(self.was_lit.keys()), len(self.lit_now.keys()), len(self.newly_lit.keys()))
        # The set symmetric difference (a^b) gives members in one set but not both,
        # Which corresponds to newly-lit and newly-unlit squares; mark them dirty:
        for s in self.was_lit ^ self.lit_now:
            self.level.Dirty(*s)
