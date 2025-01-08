from miniworlds import *

world = world(400, 400)
world.add_background("images/grass.jpg")
player = Actor()
player.add_costume("images/player.png")
player.orientation = -90

@player.register
def act(self):
    self.move_in_direction(self.world.get_mouse_position())

world.run()