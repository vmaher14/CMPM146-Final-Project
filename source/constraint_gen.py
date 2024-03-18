from random import randrange
import creatures
import itertools

# mob = creatures.RandomMob(self.depth)

def generateMonsters(LevelObject):
    mobs = creatures.PossibleMobs(LevelObject.depth)
    domain = itertools.combinations_with_replacement(mobs, 3)
    print(domain)
    # find possible mobs
    # generate domain of possible mobs
    

mobtest = [None, "Rat", "Wolf"]
domain = list(itertools.combinations_with_replacement(mobtest, 3))
print(domain)
    