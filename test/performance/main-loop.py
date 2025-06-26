from miniworlds import World, Actor
import time
import sys

world = World(300, 600)
world.add_background("images/clouds.png")
world.background.is_scaled = False

@world.register
def on_setup(self):
    for y in (400, 440, 480, 520):
        for i in range(300):
            actor = Actor((10 + i, y))
            actor.add_costume("ship.png")
            actor.speed = 1

    self.moved = False  # Flag, ob Bewegung schon gemessen wurde

@world.register
def act(self):
    start = time.perf_counter()
    for actor in self.actors:
        actor.move(actor.speed)
    elapsed = time.perf_counter() - start

world.run()
