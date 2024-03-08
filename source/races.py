"races.py - Pyro races"


from util import *
import creatures

class Race(BASEOBJ):
    "Encapsulates info about player races."
    def __init__(self, pc):
        self.pc = pc

class Human(Race):
    name = "Human"
    desc = """Humans are generic.  For now."""
    def GainLevel(self, new_level):
        if new_level == 1:
            # Initialization:
            self.pc.str = 8 + d(1, 4)
            self.pc.dex = 8 + d(1, 4)
            self.pc.con = 8 + d(1, 4)
            self.pc.int = 8 + d(1, 4)
        else:
            pass

class Troll(Race):
    name = "Troll"
    desc = """Trolls are nasty, ugly, green, halitotic brutes.  They have great
strength and even more exceptional constitution.  Their dexterity is
somewhat poor, and their intelligence is practically nonexistant."""
    def __init__(self, pc):
        Race.__init__(self, pc)
        pc.unarmed = creatures.Claw("1d4", 150)
        pc.xp_rate = 1.5
    def GainLevel(self, new_level):
        if new_level == 1:
            # Initialization:
            self.pc.str += 8 + d(2, 4)
            self.pc.dex += 6 + d(1, 3)
            self.pc.con += 8 + d(3, 4)
            self.pc.int += 2 + d(1, 4)
        else:
            pass

all = [Human, Troll]        

