"items.py - Pyro items"

from util import *
import creatures

types = [
    ("Melee Weapons", "("),
    ("Armor", "["),
    ("Missile Weapons", "{"),
    ("Ammunition/Thrown Weapons", "|"),
    ("Potions", "!"),
    ("Wands", "/"),
    ("Scrolls", "?"),
    ("Books", "+"),
    ("Rings", "="),
    ("Amulets", '"'),
    ("Tools", "~"),
    ("Comestibles", "%"),
    ("Valuables", "$"),
    ("Other", "-"),
]

class AttackType(BASEOBJ):
    "Any mode of attack."
    name = ">>Generic Attack<<"
    verbs = ["attacks"]
    speed = 100

class MeleeAttackType(AttackType):
    "Some mode of melee attack."
    damage_type = "physical"
    speed = 100
    damage = "1d3"
    tohit, todamage = 0, 0
    def __init__(self, damage=None, speed=None, tohit=None, todamage=None):
        if damage is not None: self.damage = damage
        if speed is not None: self.speed = speed
        if tohit is not None: self.tohit = tohit
        if todamage is not None: self.todamage = todamage
    def Attempt(self, attacker, target):
        "Attempt this attack on the given target."
        attacker.timer += delay(self.speed)
        hit = attacker.MeleeHitBonus() + self.tohit
        evade = target.EvasionBonus()
        differential = hit - evade
        chance = hit_chance(differential, target.level)
        log("%s (%s to hit) attacks %s (%s evade, level %s) with %s%% chance to hit." %
            (attacker.name, hit, target.name, evade, target.level, int(chance*100)))
        # TODO: Roll everything into MeleeHitBonus()
        if successful_hit(differential, target.level):
            # The attack landed; calculate damage:
            damage_roll = d(self.damage) + self.todamage + attacker.MeleeDamageBonus()
            protection_roll = quantize(target.ProtectionBonus())
            # Successful attack always does at least 1d2 damage:
            damage = max(d("1d2"), damage_roll - protection_roll)
            damage_taken = target.TakeDamage(damage, self.damage_type, source=attacker)
            # If the PC can see the attack, describe it:
            if not seen(attacker) and not seen(target):
                return True, []
            #Global.IO.ReportDamage(attacker, target, damage=damage)
            if damage_taken > 0:
                if attacker.is_pc:
                    Global.IO.Message("You ^G^%s^0^ %s. [^G^%s^0^]" % (self.verbs_fp[1],
                        target.ArticleName("the"), damage_taken))
                    if target.dead:
                        Global.IO.Message("^G^You have killed %s! (%s xp)" % (target.ArticleName("the"),
                                                                       target.kill_xp))
                elif target.is_pc:
                    Global.IO.Message("%s ^R^%s^0^ you. [^R^%s^0^]" % (attacker.ArticleName("The"),
                        self.verbs[1], damage_taken))
                else:
                    Global.IO.Message("%s ^Y^%s^0^ %s." % (attacker.ArticleName("The"),
                        self.verbs[1], target.ArticleName("the")))
            elif damage_taken == 0:
                if attacker.is_pc:
                    Global.IO.Message("You %s %s, but do no damage." % (self.verbs_fp[0],
                        target.ArticleName("the")))
                elif target.is_pc:
                    Global.IO.Message(("%s %s you, but does no damage." %
                           (attacker.ArticleName("The"),self.verbs[0])))
                else:
                    Global.IO.Message("%s %s %s." % (attacker.ArticleName("The"),
                        self.verbs[0], target.ArticleName("the")))
            if target.is_pc:
                Global.IO.ShowStatus(Global.pyro)
            return True
        else:
            # The attack missed; if the PC can see, describe it:
            if not seen(attacker) and not seen(target):
                return False, []
            Global.IO.ReportDamage(attacker, target, result="miss")
            if attacker.is_pc:
                Global.IO.Message("You try to %s %s, but miss." % (self.verbs_fp[1],
                    target.ArticleName("the")))
            elif target.is_pc:
                Global.IO.Message(("%s tries to %s you, but misses." %
                       (attacker.ArticleName("The"), self.verbs_fp[1])))
            else:
                Global.IO.Message("%s tries to %s %s, but misses." % (attacker.ArticleName("The"),
                      self.verbs_fp[1], target.ArticleName("the")))
            return False

class DefaultAttack(MeleeAttackType):
    name = "attack"
    verbs = ["attacks", "hits", "whacks"]
    verbs_fp = ["attack", "hit", "whack"]
    damage = "1d2"
    
class Item(BASEOBJ):
    "Inanimate objects"
    name = ">>Generic Item<<"
    type = "Other"
    weight = 1.0
    rarity = 1.0    # How often the item will be generated; 1.0 is standard.
    identified = False
    melee_attack = DefaultAttack()
    melee_twohand = False
    material, prefix, suffix = None, None, None
    def __init__(self):
        self.x, self.y, self.current_level = 0, 0, None
    def Name(self):
        name = self.name
        if self.material:
            name = "%s %s" % (self.material, name)
        if self.prefix:
            name = "%s %s" % (self.prefix, name)
        if self.suffix:
            name = "%s %s" % (name, self.suffix)
        try:
            bonus = self.BonusString()
        except AttributeError:
            bonus = ""
        try:
            ap = " (%s)" % self.armor_points
        except AttributeError:
            ap = ""
        return "%s%s%s (%ss)" % (name, bonus, ap, self.weight)
    def LongDescription(self):
        "Long description of the item."
        desc = "%s" % self.desc
        desc += "\n\nIt weighs %s stones.\n\n" % self.weight
        try:
            desc += self.MeleeStats()
        except AttributeError: pass
        try:
            desc += self.ArmorStats()
        except AttributeError: pass        
        return desc

# Weapon attack types:
class Punch(MeleeAttackType):
    name = "punch"
    verbs = ["swings at", "punches", "clocks"]
    verbs_fp = ["swing at", "punch", "clock"]
    speed = 150
    damage = "1d2"
class Slash(MeleeAttackType):
    name = "slash"
    verbs = ["swings at", "slashes", "slices"]  # no damage, hit, crit
    verbs_fp = ["swing at", "slash", "slice"]
class Stab(MeleeAttackType):
    name = "stab"
    verbs = ["pokes at", "stabs", "impales"]
    verbs_fp = ["poke at", "stab", "impale"]
class Lash(MeleeAttackType):
    name = "lash"
    verbs = ["lashes at", "whips", "scourges"]
    verbs_fp = ["lash at", "whip", "scourge"]
class Bludgeon(MeleeAttackType):
    name = "bludgeon"
    verbs = ["swings at", "clubs", "bludgeons"]
    verbs_fp = ["swing at", "club", "bludgeon"]
class Chop(MeleeAttackType):
    name = "chop"
    verbs = ["hacks at", "chops", "cleaves"]
    verbs_fp = ["hack at", "chop", "cleave"]

class Weapon(Item):
    is_weapon = True
       
class MeleeWeapon(Weapon):
    # Although any item can be wielded in melee, this class is for
    # items that are designed to be used in melee combat.
    is_melee_weapon = True
    type = "Melee Weapons"
    tile = ["melee_weapon"]
    color = c_Cyan
    min_str = 1     # Minimum strength to wield
    def BonusString(self):
        bonus = ""
        if self.melee_attack.tohit == self.melee_attack.todamage == 0:
            return ""
        else:
            if self.melee_attack.tohit >= 0:
                hit = "+%s" % self.melee_attack.tohit
            else:
                hit = str(self.melee_attack.tohit)
            if self.melee_attack.todamage > 0:
                dam = "+%s" % self.melee_attack.todamage
            else:
                dam = str(self.melee_attack.todamage)
            bonus = " [%s %s]" % (hit, dam)
            return bonus
    def MeleeStats(self):
        desc = ""
        if self.melee_attack.todamage == 0:
            dam = ""
        elif self.melee_attack.todamage > 0:
            dam = "+%s" % self.melee_attack.todamage
        elif self.melee_attack.todamage < 0:
            dam = "%s" % self.melee_attack.todamage
        if self.melee_attack.tohit == 0:
            hit = ""
        elif self.melee_attack.tohit > 0:
            hit = "+%s" % self.melee_attack.tohit
        elif self.melee_attack.tohit < 0:
            hit = "%s" % self.melee_attack.tohit
        desc += "In melee combat, it %s for %s damage " % (self.melee_attack.verbs[1], 
                                                           self.melee_attack.damage+dam)
        desc += "with speed %s" % self.melee_attack.speed
        if hit:
            desc += " and %s to hit" % hit
        desc += ".\n"
        if self.melee_twohand:
            desc += "It requires both hands to wield.\n"
        return desc

        
class MissileWeapon(Weapon):
    is_missile_weapon = True
    type = "Missile Weapons"
    tile = ["missile_weapon"]
    color = c_Cyan
    min_str = 1

# Melee weapon subtypes:
class Sword(MeleeWeapon):
    subtype = "swords"
    min_str = 5
    desc = "A bladed weapon designed for slashing."
class TwohandSword(MeleeWeapon):
    subtype = "two-handed swords"
    melee_twohand = True
    min_str = 10
    desc = "A huge sword requiring both hands to wield."
class ShortBlade(MeleeWeapon):
    subtype = "short blades"
    desc = "A small bladed weapon for slashing and stabbing."
class Blunt(MeleeWeapon):
    subtype = "maces"
    desc = "A blunt weapon designed for bludgeoning the enemy."
class Axe(MeleeWeapon):
    subtype = "axes"
    desc = "A heavy, hacking weapon."

# Specific melee weapon types:
class ShortSword(Sword):
    name = "short sword"
    weight = 3.0
    desc = "A sword about eighteen inches long with a sharp tip, designed for slashing and stabbing."
    def __init__(self):
        Sword.__init__(self)
        self.melee_attack = Slash("1d6", 100)
class LongSword(Sword):
    name = "long sword"
    weight = 4.0
    desc = "A long sword, slightly over two feet long.  It is mostly used for slashing attacks, and is somewhat slower and more powerful than a short sword."
    def __init__(self):
        Sword.__init__(self)
        self.melee_attack = Slash("1d7", 80)
class GreatSword(TwohandSword):
    name = "greatsword"
    weight = 8.0
    desc = "A huge, heavy sword with a blunt tip, used for slashing and crushing.  It is slow but very powerful."
    def __init__(self):
        TwohandSword.__init__(self)
        self.melee_attack = Slash("2d6", 65)    
class BattleAxe(Axe):
    name = "battle axe"
    weight = 5.0
    desc = "A large, heavy, two-bladed axe used for hacking at the foe."
    def __init__(self):
        Axe.__init__(self)
        self.melee_attack = Chop("1d8", 80)
class Dagger(ShortBlade):
    name = "dagger"
    weight = 1.0
    desc = "A small blade about a foot long with a sharp tip, used for stabbing.  It is very quick, but doesn't do much damage."
    def __init__(self):
        ShortBlade.__init__(self)
        self.melee_attack = Stab("1d4", 130)
class Whip(MeleeWeapon):
    name = "whip"
    weight = 1.0
    color = c_yellow
    desc = "This weapon does little damage, and is somewhat slow to attack with.  However, it is relatively easy to hit the target."
    def __init__(self):
        MeleeWeapon.__init__(self)
        self.melee_attack = Lash("1d4", 90, tohit=2)
class Club(Blunt):
    name = "club"
    weight = 4.0
    color = c_yellow
    desc = "A stout length of wood, heavier at one end.  About as low-tech as it gets."
    def __init__(self):
        Blunt.__init__(self)
        self.melee_attack = Bludgeon("1d4", 100)

armor_prefixes = [
    ("tattered", -4),
    ("decrepit", -3),
    ("shabby", -2),
    ("worn", -1),
    (None, 0),
    ("sturdy", 1),
    ("strong", 2),
    ("formidable", 3),
    ("impenetrable", 4),
]
armor_mats = {
    "cloth": [
        ("burlap", 0),
        ("linen", 5),
        ("silk", 10),
        ("ironweave", 15),
        ("highcloth", 20),
    ],
    "leather": [
        ("leather", 0),
        ("thick leather", 5),
        ("hard leather", 10),
        ("basilisk leather", 15),
        ("dragonscale", 20),
    ],
    "metal": [
        ("iron", 0),
        ("steel", 5),
        ("mithril", 10),
        ("adamantium", 15),
        ("divinium", 20),
    ]
}
    
class Armor(Item):
    is_armor = True
    type = "Armor"
    tile = ["armor"]
    color = c_yellow
    material, prefix, suffix = None, None, None
    def ArmorStats(self):
        desc = "When equipped on your %s, it grants %s armor points." % (self.armor_slot, self.armor_points)
        return desc
class BodyArmor(Armor):
    armor_slot = "torso"
class Helm(Armor):
    armor_slot = "head"
class Boots(Armor):
    armor_slot = "feet"
class Gloves(Armor):
    armor_slot = "hands"
class ClothArmor(Armor): pass
class LeatherArmor(Armor): 
    color = c_yellow
class ChainArmor(Armor):
    color = c_cyan
class PlateArmor(Armor):
    color = c_Cyan

class Robe(BodyArmor, ClothArmor):
    name = "robe"
    armor_points = 5
    weight = 1.0
    desc = "This long, flowing robe does not hinder the wearer's movements, but the cloth provides only very minimal protection against physical attack."
    def __init__(self):
        self.color = choice([c_yellow, c_Yellow, c_White, c_white, c_Blue, c_cyan, c_Cyan])
        Item.__init__(self)
class Jerkin(BodyArmor, LeatherArmor):
    name = "jerkin"
    armor_points = 7
    weight = 3.0
    desc = "This leather jerkin provides protection from physical attack, while giving the wearer freedom of movement."
class ChainShirt(BodyArmor, ChainArmor):
    name = "chain shirt"
    armor_points = 9
    weight = 6.0
    desc = "A long shirt of interlocking metal rings covering the torso and legs."
class PlateMail(BodyArmor, PlateArmor):
    name = "plate armor"
    armor_points = 12
    weight = 10.0
    desc = "A very heavy suit of metal plates.  It provides excellent protection, but limits movement significantly."
class ClothGloves(Gloves, ClothArmor):
    name = "gloves"
    armor_points = 2
    weight = 0.5
    desc = "A pair of cloth gloves offering slight protection."
    def __init__(self):
        self.color = choice([c_yellow, c_Yellow, c_White, c_white, c_Blue, c_cyan, c_Cyan])
        Item.__init__(self)
    
    
    
class Tool(Item):
    tile = ["tool"]
    color = c_yellow
class SmallBag(Tool):
    type = "Tools"
    name = "small bag"
    reduction = 0.05
    slots = 10    
    

class Jewelry(Item):
    is_jewelry = True
    type = "Jewelry"
    protect, evade = 0, 0
class Ring(Jewelry):
    tile = ["ring"]
    type = "Ring"
    armor_slot = "finger"
class Amulet(Jewelry):
    tile = ["amulet"]
    type = "Amulet"
    armor_slot = "neck"


class RandomStone(Item):
    def __init__(self):
        Item.__init__(self)
        c = choice(colors.keys())
        self.name = "%s stone" % c
        self.color = colors[c]
        self.type = "Valuables"
        self.tile = ["stone"]
        self.weight = irand(10, 200) / 10.0
        if self.weight < 6:
            self.name = "small %s" % self.name
        elif self.weight > 10:
            self.name = "heavy %s" % self.name
        self.desc = "A %s.  It's kind of pretty, not useful for much else." % self.name

        
all_melee_weapons = [ShortSword, LongSword, GreatSword, Dagger, Whip, Club]
all_armor = [Robe, Jerkin, ChainShirt, PlateMail]

def random_bonus(level):
    "Return a bonus appropriate to the given level."
    bonus = norm(0, level / 4.0)
    # Make negative bonus rare:
    if bonus < 0:
        if rnd(0, 1) > 0.3:
            bonus = abs(bonus)
    return int(bonus)

def random_melee_weapon(level, w=None, nospecial=False):
    "Return a random melee weapon suitable for the given character level."
    if w is None:
        w = choice(all_melee_weapons)
    w = w()
    if level < 0:
        level = abs(level)
        mod = -1
    else:
        mod = 1
    for i in xrange(level-1):
        if rnd(0, 1) < 0.5:
            w.melee_attack.tohit += mod
        else:
            w.melee_attack.todamage += mod
    return w

def random_armor(level, a=None, nospecial=False):
    "Return a random piece of armor for the given level."
    if a is None:
        a = choice(all_armor)
    a = a()
    a.armor_points = quantize(a.armor_points * 1.1487 ** level)    # Doubles every five levels
    if isinstance(a, ClothArmor):
        mats = armor_mats["cloth"]
    elif isinstance(a, LeatherArmor):
        mats = armor_mats["leather"]
    elif isinstance(a, ChainArmor):
        mats = armor_mats["metal"]
    elif isinstance(a, PlateArmor):
        mats = armor_mats["metal"]
    p = []
    for mat, mat_lv in mats:
        for mod, mod_lv in armor_prefixes:
            if mat_lv + mod_lv == level:
                p.append((mat, mod))
    m = choice(p)
    a.material, a.prefix = m
    if nospecial: return a
    if rnd(0, 1) < 0.5:  # TODO: reduce this a lot!
        # Armor "of lightness":
        a.weight *= 0.75
        a.suffix = "of lightness"
    return a
    
        
def random_item(level):
    "Return a random item suitable for the given character level."
    item = choice([random_melee_weapon, random_armor])(level)
    return item