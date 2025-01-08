from miniworlds import *

world = world(400,400)
world.add_background("images/grass.jpg")
player = Actor()
player.add_costume("images/player.png")
player.orientation = -90
player.position = (200, 200)

@player.register
def act(self):
    self.direction = self.world.frame
    self.move()
    

world.run()