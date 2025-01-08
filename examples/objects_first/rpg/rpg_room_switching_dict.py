from miniworldmaker import *

world = TiledWorld()
world.columns = 3
world.rows = 3

r00 = [    "  d",
           "  w",
           "www"]

r01 =     ["w  ",
           "w  ",
           "w  ",
           ]

rooms = {0: r00, 1: r01}

class Player(Actor):
    
    def on_setup(self):
        self.add_costume("knight")
        self.costume.is_rotatable = False
        self.layer = 1
        
    def on_key_down_w(self):
        self.move_up()

    def on_key_down_s(self):
        self.move_down()

    def on_key_down_a(self):
        self.move_left()
    
    def on_key_down_d(self):
        self.move_right()
        
    def on_not_detecting_world(self):
        self.move_back()

    def on_detecting_wall(self, other):
        self.move_back()
        
    def on_key_down(self, keys):
        global r01
        if "SPACE" in keys:
            if self.detect_actor(Wall):
                setup_room(rooms[1])

class Wall(Actor):
    def on_setup(self):
        self.add_costume("wall")

class Door(Actor):
    def on_setup(self):
        self.add_costume("door_closed")


@world.register
def on_setup(self):
    setup_room(r00)
    
def setup_room(room):
    for actor in world.actors:
        if actor != player:
            actor.remove()
    for i, row in enumerate(room):
        for j, column in enumerate(row):
            x = j
            y = i
            if room[i][j] == "w":
                t = Wall(x, y)
            if room[i][j] == "d":
                d = Door(x, y)                
                
player = Player(0, 0)
world.run()
