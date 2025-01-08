import random
from miniworlds import Actor, Number
from miniworlds_physics import PhysicsWorld

class MyWorld(PhysicsWorld):

    def on_setup(self):
        self.add_background("images/background.png")
        Bird((75, 200))
        self.pipe1 = Pipe()
        self.pipe1.position = (260, self.height - 280)
        self.pipe1.topleft = (260, self.height - 280)
        print("Pipe was created")
        self.pipe2 = Pipe(position=(520, 0))
        self.pipe2.top()
        self.pipe3 = Pipe(position=(780, self.height - 280))
        self.pipe4 = Pipe(position=(760, -100))
        self.pipe4.top()
        self.score = Number(position=(10, 10))
        self.score.size = (40, 40)
        self.score.physics.simulation = None
        self.stop()


class Pipe(Actor):

    def on_setup(self):
        self.add_costume("images/pipe1.png")
        self.costume.is_rotatable = False
        self.size = (80, 300)
        self.passed = False
        self.set_simulation("manual")
        self.set_velocity_x(-150)
        self.origin = "topleft"

    def top(self):
        self.costume.orientation = -180

    def act(self):
        if self.position[0] < 75 and self.passed is False:
            self.passed = True
            self.world.score.inc()

    def on_detecting_left_border(self):
        print("left border")
        self.move_to((random.randint(750, 800), self.y))
        self.set_velocity_x(-150)
        self.passed = False



class Bird(Actor):

    def on_setup(self):
        self.add_costume("images/fly.png")
        self.size = (60, 60)
        self.costume.orientation = 180
        self.flip_x()
        self.physics.size = (0.8, 0.8)
        self.physics.shape_type = "circle"

    def on_detecting_borders(self, borders):
        if "bottom" in borders or "left" in borders:
            self.world.is_running = False
            self.world.reset()

    def on_touching_pipe(self, other, info):
        print("Ouff!")

    def on_key_down_space(self):
        self.set_velocity_y(-300)
        if self.world.is_running is False:
            self.world.is_running = True


world = MyWorld(800, 600)
world.run()

