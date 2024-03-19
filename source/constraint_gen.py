from random import randrange
import creatures
import itertools

# mob = creatures.RandomMob(self.depth)

# Create and return a list of mobs appropriate to the given dungeon level.
def possibleMobs(depth):
    mobs = [mob for mob in creatures.all if -1 <= depth - mob.level <= 1]
    return mobs

# The heuristic for the amount of damage the mob is expected to deal to the player over
# its lifespan (a.k.a. over the course of the encounter)
def mobDamageHeuristic(mob, diceavg):
    pass


def generateMonsters(LevelObject):
    # find possible mobs
    # generate domain of possible mobs
    # return domain of all rooms
    mobs = creatures.PossibleMobs(LevelObject.depth)
    domains = itertools.combinations_with_replacement(mobs, 3)
    # scoring_tuples = []
    # for mob_set in domain:
    #     score = scoring_mobs(mob_set)
    #     scoring_tuples.append((score, mob_set))
    
    return domains

# Takes in a tuple or set of monsters and scores the expected damage
# output of those monsters
def scoring_mobs(mob_set):
    score = 0
    for mob in mob_set:
        stat_avg = (mob.hp_max + mob.str + mob.int + mob.dex + mob.level) // 5
        # ie. rats floored average of 3, wolves 4
        if mob == creatures.Rat:
            score -= 1
        elif mob == creatures.WimpyKobold:
            score -= 7
        elif mob == creatures.WimpyGoblin:
            score -= 10
        elif mob == creatures.Wolf:
            score -= 3
        elif mob == creatures.Imp:
            score -= 2
        elif mob == creatures.Ogre:
            score -= 65
    return score


# Generates a list of the domains of potion amounts for each room, for the constraint solver.
def potionPossibilities(Level):
    potionDomain = []
    for i in range(len(Level.layout.rooms)):
        potionDomain.append({0, 1, 2})
    return potionDomain

def scoring_potions(num_potions):
    score = num_potions * 5
    return score

# Initializes the domains for the key variable of each room, returning 
def keysPossibilities(Level):
    keyDomains = []
    for i in range(len(Level.layout.rooms)):
        keyDomains.append({0, 1})
    return keyDomains

def scoring_keys(num_keys):
    score = num_keys
    return score

def locksPossibilities(Level):
    lockDomains = []
    for i in range(len(Level.layout.rooms)):
        lockDomains.append({0, 1})
    return lockDomains

def scoring_locks(num_locks):
    score = -1 * num_locks
    return score



#def scoring_keys():
#def scoring_locks():
    

def monsterPossibilities(Level):
    monsterDomain = []
    #First create the standard domain 
    #Initialize with an empty tuple representing no monsters in the room
    defaultDomain = set(tuple())
    # all possible mobs for this layer
    all = possibleMobs(Level.depth)
    # adds the 1s, 2s, and 3s in one fell swoop
    for i in range(len(all)):
        defaultDomain.add(tuple(all[i]))
        for j in range(i,len(all)):
            defaultDomain.add(tuple(all[i], all[j]))
            for k in range(j,len(all)):
                defaultDomain.add(tuple(all[i], all[j], all[k]))

    for i in range(len(Level.rooms)):
        if Level.depth==1 and Level.rooms[i]==Level.up_room:
            monsterDomain[i] = (())
        else:
            monsterDomain[i] = defaultDomain.copy()
            




# mobtest = [None, "Rat", "Wolf"]
# domain = list(itertools.combinations_with_replacement(mobtest, 3))
# print(domain)
    

    