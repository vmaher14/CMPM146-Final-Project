"professions.py - Pyro professions"


from util import *

class Profession(BASEOBJ):
    "Encapsulates info about player professions."
    desc = "No description is available for this profession."
    def __init__(self, pc):
        self.pc = pc

class Fighter(Profession):
    name = "Fighter"
    desc = """The Fighter is a melee-oriented profession, specializing in whacking
monsters with heavy objects."""
    def GainLevel(self, new_level):
        if new_level == 1:
            # Initialization:
            self.pc.str += 2
            self.pc.con += 2
            self.pc.dex += 1
            self.pc.int = max(MIN_STARTING_STAT, self.pc.int - 5)
        else:
            pass

class Wizard(Profession):
    name = "Wizard"
    desc = """Wizards are physically frail (relative to average members of their
race), but their magical talents help them survive the dangers of the dungeon."""
    def GainLevel(self, new_level):
        if new_level == 1:
            # Initialization:
            self.pc.str -= 2
            self.pc.con -= 3
            self.pc.dex -= 0
            self.pc.int += 5
        else:
            pass

all = [Fighter, Wizard] 