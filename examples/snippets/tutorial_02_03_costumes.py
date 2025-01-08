from miniworlds import World, Actor

world = World()
world.add_background("images/grass.jpg")

a1 = Actor((20,20))
a1.add_costume("images/cow.png")
a2 = Actor((60,20))
a2.add_costume("images/chicken.png")
a3 = Actor((100,20))
a3.add_costume("images/dog.png")
a4 = Actor((140,20))
a4.add_costume("images/goat.png")

world.run()