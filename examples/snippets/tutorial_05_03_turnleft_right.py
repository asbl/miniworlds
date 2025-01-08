from miniworlds import World, Actor

world = World(400, 400)
world.add_background("images/grass.jpg")
player = Actor((100, 100))
player.add_costume("images/player.png")
player.orientation = -90

@player.register
def act(self):
    self.move()
    
@player.register
def on_key_down_a(self):
    self.turn_left(30)

@player.register
def on_key_down_d(self):
    self.turn_right(30)


world.run()