from miniworlds import TiledWorld, Toolbar, Console, Actor, Button, Label, PagerHorizontal

world = TiledWorld()
world.columns = 8
world.rows = 8
world.tile_size = 24
world.camera.world_size_x = 16
world.camera.world_size_y = 16
world.add_background((255, 255, 255, 255))

toolbar = Toolbar()
@toolbar.register
def on_setup(self):
    self.add_background("images/bg")
    self.background.set_mode(mode="textured", texture_size=(200, 200))

world.toolbar = world.add_right(toolbar, size=180)

console = Console()
world.console = world.add_bottom(console, size=100)
world.console.newline("You enter a new world")

pager = PagerHorizontal(console)
world.add_bottom(pager, size=60)

def create_grass(pos):
    g = Actor(pos)
    g.add_costume("images/grass2.png")
    g.static = True
    g.layer = 0


def create_wall(pos, walls):
    w = Actor(pos)
    w.add_costume("images/wall.png")
    w.static = True
    w.is_blocking = True
    walls.append(w)


@world.register
def on_setup(self):
    for i in range(world.rows):
        for j in range(world.columns):
            create_grass((j, i))
    self.walls = []
    create_wall((0, 4), self.walls)
    create_wall((1, 4), self.walls)
    create_wall((2, 4), self.walls)
    create_wall((3, 4), self.walls)
    create_wall((4, 4), self.walls)
    create_wall((5, 4), self.walls)
    create_wall((6, 4), self.walls)
    create_wall((6, 0), self.walls)
    create_wall((6, 1), self.walls)
    create_wall((6, 3), self.walls)
    

torch = Actor((10, 4))


@torch.register
def on_setup(self):
    torch.layer = 2
    torch.add_costume("images/torch.png")


fireplace = Actor((10, 12))
fireplace.layer = 2


@fireplace.register
def on_setup(self):
    self.costume_not_burned = fireplace.add_costume("images/fireplace_0.png")
    self.burning = False
    self.costume_burned = fireplace.add_costume(
        ["images/fireplace_1.png", "images/fireplace_2.png"]
    )
    fireplace.switch_costume(self.costume_not_burned)


door = Actor((6, 2))

@door.register
def on_setup(self):
    self.add_costume("images/door_closed.png")
    self.closed = True
    self.door_open_costume = door.add_costume("images/door_open.png")
    self.switch_costume(0)
    door.layer = 2


player = Actor((8, 2))


@player.register
def on_setup(self):
    self.add_costume("images/knight")
    self.costume.is_rotatable = False
    self.layer = 3
    self.is_blockable = True


@player.register
def act(self):
    self.world.camera.from_actor(self)



@player.register_message("burn")
def burn_torch(self, sender):
    print("BURN?")
    if not fireplace.burning:
        fireplace.world.play_sound("sounds/fireplace.wav")
        fireplace.switch_costume(fireplace.costume_burned)
        fireplace.costume.is_animated = True


@player.register_message("open_door")
def open(self, sender):
    if door.closed:
        door.switch_costume(door.door_open_costume)
        door.world.play_sound("sounds/olddoor.wav")
        door.closed = False


inventory = []


@player.register
def on_key_down_w(self):
    player.move_up()


@player.register
def on_key_down_s(self):
    player.move_down()


@player.register
def on_key_down_a(self):
    player.move_left()


@player.register
def on_key_down_d(self):
    player.move_right()


@player.register_message("Torch")
def light_fireplace(self, data):
    print("light")
    found_actors = player.detect_all()
    if fireplace in found_actors:
        self.world.console.newline("You light the fireplace.")
        self.send_message("burn")
        self.world.toolbar.remove("Torch")
    else:
        self.world.console.newline("...nothing happens")


@player.register_sensor(door)
def ask_open_door(self, door):
    if door.closed:
        self.undo_move()
        message = "The door is closed - Do you want to open it?"
        reply = self.ask.choices(message, ["Yes", "No"])
        if reply == "Yes":
            self.send_message("open_door")


@player.register_sensor(torch)
def pick_up_torch(self, torch):
    reply = self.ask.choices(
        "You find a torch - Do you want to pick it up?", ["Yes", "No"]
    )
    if reply == "Yes":
        inventory.append("Torch")
        torch.remove()
        l = Label("You pick up the torch")
        line = world.console.add(l)
        
        b = Button("Torch", "images/torch.png")
        world.toolbar.add(b)


world.run()
