from miniworlds import World, Actor, Circle, Text
import random

world = World(300, 600)
world.add_background("images/clouds.png")
world.background.is_scaled = False
aircraft = Actor((150, 500))
aircraft.add_costume("images/ship.png")

@aircraft.register
def on_setup(self):
    """The downtime specifies the number of frames until the next shot can be fired.
    
    If downtime > 100 a shot can be fired (@see on_key down of aircraft)
    """
    self.downtime = 0


@aircraft.register
def act(self):
    """Increment the downtime every frame per 1"""
    self.downtime += 1


@aircraft.register
def on_key_pressed(self, keys):
    """Move aircraft left/right with a, d keys.
    """
    if "a" in keys:
        aircraft.x -= 1
    elif "d" in keys:
        aircraft.x += 1


@aircraft.register
def on_key_down(self, keys):
    """Shoot, if downtime > 100
    """
    if " " in keys and self.downtime > 100:
        position = aircraft.center
        position = (aircraft.center[0], aircraft.center[1] - 20)
        bullet = Circle(position)
        self.downtime = 0

        @bullet.register
        def act(self):
            self.y = self.y - 1

        @bullet.register
        def on_detecting_actor(self, other):
            if other in self.world.enemies:
                other.remove()
                self.remove()


@world.register
def on_setup(self):
    self.enemies = []


@world.register
def act(self):
    if self.frame % 120 == 0:
        enemy = Actor((random.randint(30, 270), 50))
        enemy.add_costume("images/enemy.png")
        enemy.orientation = 180
        self.enemies.append(enemy)

        @enemy.register
        def act(self):
            self.y = self.y + 1

        @enemy.register
        def on_detecting_actor(self, other):
            """ If enemy detects the aircraft, the game ends.
            """
            if other == aircraft:
                self.world.stop()
                aircraft.remove()
                t = Text((150, 300), "GAME OVER")
                t.color = (0, 0, 0)
                for enemy in self.world.enemies:
                    enemy.remove()
                self.remove()
                

world.run()
