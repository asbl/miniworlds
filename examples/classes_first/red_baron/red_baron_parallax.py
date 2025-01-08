from miniworlds import World, Actor, timer, Text
from random import randint, choice

# based on https://github.com/kantel/pygamezero/tree/master/tappyplane


class RedBaronWorld(World):
    def on_setup(self):
        self.size = (800, 480)
        bottom_ground = self.height - 35
        nr_enemies = 10

        # Add backgrounds
        back0 = Actor(origin="topleft")
        back0.add_costume("background")
        back0.size = self.width, self.height
        back1 = Actor((self.width, 0), origin="topleft")
        back1.size = self.width, self.height
        back1.add_costume("background")
        self.backs = [back0, back1]

        ground0 = Actor((0, bottom_ground), origin="topleft")
        ground0.add_costume("groundgrass")
        ground0.width = self.width
        ground0.costume.is_scaled = True
        ground1 = Actor((self.width, bottom_ground), origin="topleft")
        ground1.add_costume("groundgrass")
        ground1.width = self.width
        ground1.costume.is_scaled = True
        self.grounds = [ground0, ground1]
        self.ground_level = self.height - 85
        self.plane = Plane((100, self.height / 2))

        enemies = []
        for _ in range(nr_enemies):
            enemy = Enemy()
            enemy.reset()
            enemies.append(enemy)

    def act(self):
        for back in self.backs:
            back.x -= 1
            if back.x <= -self.width:
                back.x = self.width
        for ground in self.grounds:
            ground.x -= 2
            if ground.x <= -self.width:
                ground.x = self.width
                
    def on_key_down_space(self):
        if not self.is_running:
            self.reset()
            self.run()


class Plane(Actor):
    def on_setup(self):
        self.add_costume("planered1")
        self.gravity = 0.1
        self.velocity_y = 0
        self.fire = False

    def act(self):
        self.velocity_y += self.gravity
        self.velocity_y *= 0.9  # friction
        self.y += self.velocity_y
        if self.y >= self.world.ground_level:
            self.y = self.world.ground_level
            self.velocity_y = 0
        if self.y <= 20:
            self.y = 20
            self.velocity_y = 0

    def on_key_down_w(self):
        self.velocity_y -= 5

    def on_key_down_d(self):
        if not self.fire:
            self.fire = True
            bullet = Bullet()

            @timer(frames=30)
            def downtime():
                self.fire = False

    def on_detecting_enemy(self, other):
        text = Text((self.world.width / 2, self.world.height / 2), "GAME OVER")
        text.color = (0, 0, 0)
        self.world.stop()


class Bullet(Actor):
    def on_setup(self):
        self.add_costume("laserred")
        self.x = self.world.plane.x
        self.y = self.world.plane.y
        self.speed = 25
        self.fire = False

    def act(self):
        self.x += self.speed

    def on_detecting_enemy(self, enemy):
        enemy.reset()

    def on_not_detecting_world(self):
        self.remove()


class Enemy(Actor):

    enemy_ships = ["shipbeige", "shipblue", "shipgreen", "shippink", "shipyellow"]

    def on_setup(self):
        self.add_costume(choice(self.enemy_ships))
        self.speed = -1.5

    def reset(self):
        self.x = randint(self.world.width + 50, self.world.width + 500)
        self.y = randint(25, self.world.ground_level)

    def act(self):
        self.x += self.speed
        if self.x <= -self.world.width:
            self.reset()


level1 = RedBaronWorld()
level1.run()
