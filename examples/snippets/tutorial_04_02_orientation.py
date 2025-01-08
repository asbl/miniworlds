from miniworlds import *

world = World()
world.add_background("images/grass.jpg")
player = Actor((90,90))
player.add_costume("images/player_orientation_top.png")
player.direction = "right"
player.costume.orientation = -90 

world.run()