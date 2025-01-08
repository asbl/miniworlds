from miniworlds import World, Actor

world = World()
world.add_background("images/grass.jpg")
player = Actor()
player.add_costume("images/player.png")
player.orientation = -90 # correct image orientation
@player.register
def act(self):
    self.direction = "right"
    self.move()

world.run()