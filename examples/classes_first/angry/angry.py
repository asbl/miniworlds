import miniworlds
import miniworlds_physics

class MyWorld(miniworlds_physics.PhysicsWorld):
    birds = 0

    def on_setup(self):
        self.add_background("images/backgroundColorGrass.png")
        self.arrow = Arrow(position=(160, 250))
        self.plattform = Plattform(position=(600, 260), origin ="topleft")
        # row 1
        Box(position=(610, 220), origin ="topleft")
        Box(position=(655, 220), origin ="topleft")
        Box(position=(700, 220), origin ="topleft")
        Box(position=(745, 220), origin ="topleft")
        Box(position=(790, 220), origin ="topleft")
        # row 2
        Box(position=(630, 170), origin ="topleft")
        Box(position=(675, 170), origin ="topleft")
        Box(position=(720, 170), origin ="topleft")
        Box(position=(765, 170), origin ="topleft")
        # row 3
        Box(position=(640, 130), origin ="topleft")
        Box(position=(685, 130), origin ="topleft")
        Box(position=(730, 130), origin ="topleft")
        # row 4
        Box(position=(700, 90), origin ="topleft")
        self.counter = miniworlds.Number((20, 20))
        self.counter.size = (100, 100)
        self.counter.physics.simulation = None
        self.shots = miniworlds.Number((120, 260))
        self.shots.costume.font_size = 60
        self.shots.size = (200, 100)
        self.shots.physics.simulation = None
        self.is_running = True

    def act(self):
       # if self.shoots.get_number() >= 10 and self.is_running:
       #     self.is_running = False
       pass


class Arrow(miniworlds.Actor):

    def on_setup(self):
        self.size = (30, 30)
        self.add_costume("images/tank_arrowFull.png")
        self.orientation = -90
        self.direction = 90
        self.costume.is_scaled = True
        self.speed = 0
        self.shoot = 0
        self.physics.simulation = "manual"


    def on_key_pressed(self, keys):
        if "w" in keys:
            self.turn_left(2)
        elif "s" in keys:
            self.turn_right(2)

    def on_key_down(self, keys):
        if self.world.is_running:
            if "space" in keys:
                self.speed += 1
                self.shoot = 1
                if self.shoot == 1:
                    self.shoot = -1
                    bird = Bird(position=self.position)
                    self.speed = 0
        else:
            if "space" in keys:
                self.world.reset()


class Plattform(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/stone.png")
        self.size = (256, 64)
        self.costume.is_textured = True
        self.direction = 0
        self.physics.simulation = "manual"
        self.physics.friction = 2
        self.static = True

class Box(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/box_blue.png")
        self.size = (40, 40)
        self.costume.orientation = 90
        self.physics.friction = 0.1
        self.physics.mass = 1
        # self.physics.size = (0.95, 0.95)
        
    def on_not_detecting_world(self):
        self.world.counter.inc()
        self.remove()


class Bird(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/fly.png")
        self.physics.mass = 5
        self.physics.friction = 1
        self.physics.elasticity = 0
        self.physics.shape_type = "circle"
        self.orientation = 180
        self.flip_x()
        self.size = (40, 40)
        self.static = True

        
    def on_begin_simulation(self):
        direction = self.world.arrow.direction
        power = 10000
        self.impulse(direction, power)
        self.world.shots.inc()

    def act(self):
        if "bottom" in self.detect_borders() or "right" in self.detect_borders():
            self.remove()

def main():
    world = MyWorld(1024, 700)
    world.run()

if __name__ == '__main__':
    main()