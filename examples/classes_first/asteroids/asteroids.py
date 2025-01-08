import random

import miniworlds


class MyWorld(miniworlds.World):

    def on_setup(self):
        asteroids = list()
        for i in range(5):
            asteroid = Asteroid(
                position=(
                    random.randint(30, self.width - 30),
                    random.randint(0 + 30, self.height - 30),
                )
            )
            asteroids.append(asteroid)
        Player(position=(40, 40))
        self.add_background("images/galaxy.jpg")


class Player(miniworlds.Actor):

    def __init__(self, position):
        super().__init__(position)
        self.add_costume("images/ship.png")
        self.size = (30, 30)
        self.costume.orientation = -90

    def on_key_pressed_w(self):
        self.turn_left(10)

    def on_key_pressed_s(self):
        self.turn_right(10)

    def on_key_down_space(self):
        self.shoot()

    def act(self):
        self.move()
        borders = self.detect_borders()

    def on_detecting_asteroid(self, asteroid):
        print("asteroid!!!", asteroid)
        explosion = Explosion(position=(self.position[0] + 40, self.position[1] + 40))
        explosion.costume.is_animated = True
        self.world.play_sound("sounds/explosion.wav")
        self.remove()

    def on_detecting_borders(self, borders):
        self.bounce_from_border(borders)

    def shoot(self):
        laser = Laser.from_center(self.center)
        laser.direction = self.direction


class Laser(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/laser.png")
        self.size = (30, 30)
        self.costume.is_upscaled = True
        self.costume.orientation = 180
        self.speed = 15
        self.world.play_sound("sounds/laser.wav")

    def act(self):
        self.move()

    def on_detecting_asteroid(self, other):
        other.remove()
        explosion = Explosion(position=(other.position[0] + 40, other.position[1] + 40))
        explosion.costume.is_animated = True
        explosion.costume.text_position = (100, 100)
        explosion.costume.text = "100"
        self.world.play_sound("sounds/explosion.wav")
        self.remove()


class Asteroid(miniworlds.Actor):
    def __init__(self, position):
        super().__init__(position)
        self.add_costume("images/asteroid.png")
        self.size = (30, 30)
        self.direction = random.randint(0, 360)

    def act(self):
        borders = self.detect_borders()
        if borders:
            self.bounce_from_border(borders)
        self.move()


class Explosion(miniworlds.Actor):

    def on_setup(self):
        self.size = (128, 128)
        self.add_costume()
        self.costume.add_images(
            [
                "images/explosion00.png",
                "images/explosion01.png",
                "images/explosion02.png",
                "images/explosion03.png",
                "images/explosion04.png",
                "images/explosion05.png",
                "images/explosion06.png",
                "images/explosion07.png",
                "images/explosion08.png",
            ]
        )
        self.costume.animation_speed = 10
        self.costume.is_animated = True
        miniworlds.ActionTimer(24, self.remove, None)


random.seed()
my_world = MyWorld(400, 300)
my_world.run()
