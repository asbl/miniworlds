from miniworlds import Number, Rectangle, Circle, Line
import miniworlds_physics


class PongWorld(miniworlds_physics.PhysicsWorld):

    def on_setup(self):
        self.debug = False
        self.add_background((100, 0, 0, 255))
        self.damping = 1
        self.gravity = 0, 0
        self.player1 = Paddle((10, 130), width=10, height=80)
        self.player2 = Paddle((740, 280), width=10, height=80)
        self.left = Border((0, 0), (0, 600))
        self.top = Border((0, 0), (800, 0))
        self.right = Border((795, 0), (795, 600))
        self.bottom = Border((0, 595), (800, 595))
        self.points_left = Number((100, 100))
        self.points_left.number = 0
        self.points_left.size = (200, 200)
        self.points_left.physics.simulation = None
        self.points_right = Number((600, 100))
        self.points_right.number = 0
        self.points_right.size = (200, 200)
        self.points_right.physics.simulation = None
        self.ball = Ball((295, 5))

    def on_key_pressed_w(self):
        self.player1.move_in_direction("up")

    def on_key_pressed_s(self):
        self.player1.move_in_direction("down")

    def on_key_pressed_u(self):
        self.player2.move_in_direction("up")

    def on_key_pressed_j(self):
        self.player2.move_in_direction("down")


class Border(Line):

    def on_setup(self):
        self.physics.friction = 0
        self.physics.elasticity = 1
        self.physics.simulation = "manual"

class Paddle(Rectangle):
    def on_setup(self):
        self.size = (10, 80)
        self.costume.is_rotatable = False
        self.physics.simulation = "manual"
        self.physics.friction = 0
        self.physics.elasticity = 1


class Ball(Circle):

    def on_setup(self):
        self.add_costume("images/fly.png")
        self.direction = 30
        self.size = (30, 30)
        self.position = (400, 200)
        self.physics.mass = 1
        self.physics.elasticity = 1
        self.physics.friction = 0

    def on_begin_simulation(self):
        self.impulse(160, 2500)

    def on_touching_line(self, line, collision):
        #print("touching line ", line, collision, self.world.left)
        if line == self.world.left:
            #print("inc points")
            self.world.points_right.inc()
        if line == self.world.right:
            self.world.points_left.inc()


world = PongWorld(800, 600)
world.run()
