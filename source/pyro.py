"""
Pyro: PYthon ROguelike by Eric D. Burgess, 2006
"""


# Pyro modules:
from util import *
import races
import professions
import creatures
import items
import player
import dungeons
import io_curses as io


####################### CLASS DEFINITIONS #######################

class Pyro(BASEOBJ):
    "Main class in charge of running the game."
    def __init__(self):
        # Start a new game:
        self.game = Game(self)
    def Run(self):
        Global.IO.ClearScreen()
        try:
            while True:
                self.game.Update()
        except GameOver:
            Global.IO.DisplayText("Game over.  Character dump will go here when implemented.",
                                  c_yellow)
            log("Game ended normally.")
        
class Game(BASEOBJ):
    "Holds all game data; pickling this should be sufficient to save the game."
    def __init__(self, app):
        self.app = app
        # Create the dungeon and the first level:
        self.dungeon = dungeons.Dungeon(self)
        self.current_level = self.dungeon.GetLevel(1)
        self.current_depth = 1      # TODO: This belongs in the Dungeon class
        # Make the player character:
        self.pc = player.PlayerCharacter()   #TODO: use Global for IO, app
        # Put the PC on the up stairs:
        x, y = self.current_level.stairs_up
        self.current_level.AddCreature(self.pc, x, y)
        self.tick = 0
    def Update(self):
        "Execute a single game turn."
        self.current_level.Update()
        self.tick += 1
        
############################ MAIN ###############################

def StartGame():
    # Initialize the IO wrapper:
    IO = io.IOWrapper()
    Global.IO = IO
    try:
        # Fire it up:
        Global.pyro = Pyro()
        Global.pyro.Run()
    finally:
        IO.Shutdown()

if __name__ == "__main__":
    PROFILE = False
    AUTO = False
    if AUTO or PROFILE:
        Global.KeyBuffer = "a\naaCbRqy "
        Global.KeyBuffer = "a\naaRqy "
        seed(1)
    if PROFILE:
        import hotshot, hotshot.stats
        p = hotshot.Profile("pyro.prof")
        p.runcall(StartGame)
        p.close()
        stats = hotshot.stats.load("pyro.prof")
        stats.strip_dirs()
        stats.sort_stats("time", "calls")
        stats.print_stats(20)
    else:
        StartGame()