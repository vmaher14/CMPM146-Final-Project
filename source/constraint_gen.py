from random import randrange
import creatures
import itertools

# mob = creatures.RandomMob(self.depth)

def generateMonsters(LevelObject):
    mobs = creatures.PossibleMobs(LevelObject.depth)
    domain = itertools.combinations(mobs)

    