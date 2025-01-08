from miniworlds import Actor, World

world = World()
world.add_background("images/grass.jpg")
player = Actor((100,100))
player.add_costume("images/player.png")
player.orientation = -90 # correct image orientation
@player.register
def act(self):
    self.move_in_direction(45)

world.run()