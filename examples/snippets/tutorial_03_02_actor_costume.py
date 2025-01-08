from miniworlds import World, Actor

world = World(600, 300)
world.add_background("images/grass.png")
a1 = Actor((0, 0))
a1.add_costume("images/player.png")
a2 = Actor((100, 200))
a2.add_costume("images/knight.png")
world.run()