from miniworlds import World, Actor

world = World(500,500)
world.add_background("images/sky.jpg")
player = Actor((90, 400))
player.add_costume("images/ship.png")

@player.register
def act(self):
    player.y = player.y - 1

world.run()