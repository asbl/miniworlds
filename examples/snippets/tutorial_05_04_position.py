from miniworlds import World, Actor, Number
import random

world = World(400, 400)
world.add_background("images/skeetshooting.png")
target = Actor((100, 100))
target.add_costume("images/target-red.png")
target.orientation = -90
target.size = (80,80)

cooldown = 5
hits = Number((20,20), 0)

@target.register
def act(self):
    global cooldown
    if self.world.frame % 50 == 0: # every 50th frame:
        target.position = (random.randint(0, 400), random.randint(0, 400))
    cooldown -= 1

@target.register
def on_clicked_left(self, position):
    global cooldown, hits
    if cooldown < 0:
        hits += 1
        cooldown = 10
        
world.run()