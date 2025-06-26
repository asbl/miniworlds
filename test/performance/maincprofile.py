import cProfile
import pstats
import datetime
import os
from miniworlds import World, Actor

world = World(300, 600)
world.add_background("images/clouds.png")
world.background.is_scaled = False

def get_unique_filename(ext="txt"):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    base_dir = os.getcwd()
    counter = 1
    while True:
        filename = f"{date_str}_{counter}.{ext}"
        full_path = os.path.join(base_dir, filename)
        if not os.path.exists(full_path):
            return full_path
        counter += 1

@world.register
def on_setup(self):
    for y in (400, 440, 480):
        for i in range(300):
            actor = Actor((10 + i, y))
            actor.add_costume("ship.png")
            actor.speed = 1
    self.moved = False
    print("enable cprofile")
    world.profiler = cProfile.Profile()
    world.profiler.enable()

@world.register
def act(self):
    if self.frame < 100:
        for actor in self.actors:
            actor.move(actor.speed)
    if self.frame == 100:

        world.profiler.disable()

        filename = get_unique_filename()
        print(f"Profiling-Datei wird geschrieben: {filename}")

        with open(filename, "w") as f:
            stats = pstats.Stats(world.profiler, stream=f)
            stats.sort_stats('time')
            stats.print_stats()

        print(f"Profiling-Daten erfolgreich gespeichert in: {filename}")

        self.moved = True
        world.stop()
        world.quit()


world.run()
