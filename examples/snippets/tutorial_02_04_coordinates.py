from miniworlds import World, Actor

world = World()
world.add_background("images/grass.png")
player = Actor()
player.add_costume("images/player.png")
player.position = (100,200)
world.run()
