import miniworlds

has_key = False
world = miniworlds.TiledWorld(8, 8)
world.tile_size = 64
world.add_background((0,0,0,255))

class Player(miniworlds.Actor):
    def on_setup(self):
        self.add_costume("player")
        self.layer = 1

    def on_key_down(self, keys):
        if "UP" in keys:
            self.y -= 1
        elif "DOWN" in keys:
            self.y += 1
        elif "LEFT" in keys:
            self.x -= 1
        elif "RIGHT" in keys:
            self.x += 1
        if self.detect(Wall):
            self.undo_move()
            
    def on_detecting_key(self, other):
        other.get_key()
        
class Wall(miniworlds.Actor):
    def on_setup(self):
        self.add_costume("wall")
        
class Enemy(miniworlds.Actor):
    def on_setup(self):
        self.add_costume("enemy") # add enemy.png to your images-folder 
        self.velocity = 1
        self.layer = 1
        
    def act(self):
        self.move(self.velocity)
        print(self.detect(Wall), self.position)
        if self.detect(Wall):
            self.undo_move()
            self.velocity = - self.velocity
            self.move(self.velocity)
        if self.detect(Player):
            print("You died")
            exit()

class Door(miniworlds.Actor):
    def on_setup(self):
        self.add_costume("door_closed")
        self.add_costume("door_open")
        self.switch_costume(0)
        self.open = False

    def open_door(self):
        self.open = True
        self.switch_costume(1)

class Key(miniworlds.Actor):
    def on_setup(self):
        self.add_costume("key")
        self.layer = 1
        
    def get_key(self):
        global has_key
        has_key = True
        self.remove()
        
            
tiles = [None, Wall, Player, Enemy, Key, Door]

maze = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 2, 0, 1],
    [1, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 1, 0, 0, 1],
    [1, 0, 1, 0, 1, 0, 0, 1],
    [1, 5, 1, 3, 4, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1]
]

@world.register
def on_setup(self):
    for row in range(len(maze)):
        for column in range(len(maze[row])):
            x = column
            y = row
            actor_cls = tiles[maze[row][column]]
            if actor_cls:
                t = actor_cls((x, y))
            

world.run()
