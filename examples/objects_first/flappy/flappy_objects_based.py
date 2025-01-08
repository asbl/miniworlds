import random
from miniworlds import Actor, Number, Text
from miniworlds_physics import PhysicsWorld

world = PhysicsWorld(800, 600)
world.game_over = False
world.add_background("images/background.png")
pipes = []

pipes.append(Actor(position=(300, world.height - 280)))
pipes.append(Actor(position=(500, 0)))
pipes.append(Actor(position=(700, world.height - 280)))
pipes.append(Actor(position=(900, 0)))

for pipe in pipes:
    pipe.direction = 0
    pipe.add_costume("images/pipe1.png")
    pipe.size = (50, 280)
    pipe.passed = False
    pipe.physics.simulation = "manual"
    pipe.physics.velocity_x = -150
    pipe.origin = "topleft"


    @pipe.register
    def act(self):
        if self.position[0] < 75 and self.passed is False:
            self.passed = True
            score.inc()


    @pipe.register
    def on_detecting_left_border(self):
        position = (self.x + random.randint(750, 800), self.y)
        self.move_to(position)
        self.passed = False

pipes[1].costume.orientation = -180
pipes[3].costume.orientation = -180



score = Number()
score.position = (30, 30)
score.size = (40, 40)
score.physics.simulation = "static"
world.stop()

bird = Actor()
bird.position = (75, 200)
bird.add_costume("images/fly.png")
bird.size = (60, 60)
bird.physics.simulation = "simulated"
bird.is_flipped = True
bird.physics.size = (0.8, 0.8)
bird.is_rotatable = False


@bird.register
def on_detecting_borders(self, borders):
    if "bottom" in borders or "top" in borders:
        end = Text()
        end.set_text("Game over!")
        end.position = (400, 200)
        world.game_over = True
        world.stop()


@bird.register
def on_detecting_actor(self, other):
    if other in pipes:
        end = Text((200, 200), "Game over!")
        end.set_text("Game over!")
        world.game_over = True
        world.stop()


@bird.register
def on_key_down_space(self):
    self.physics.velocity_y = - 200
    if world.is_running is False and not world.game_over:
        world.start()


@bird.register
def act(self):
    pass


world.run()