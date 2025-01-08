from miniworlds import *

world = World()
world.add_background("images/grass.jpg")
player = Actor((90,90))
player.add_costume("images/player.png")
player.costume.orientation = -90 
@player.register
def on_key_down_w(self):
    player.y = player.y - 1

world.run()