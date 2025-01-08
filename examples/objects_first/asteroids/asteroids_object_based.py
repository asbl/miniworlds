import random
from miniworlds import Actor, World, ActionTimer

world = World(400, 300)
world.add_background("images/galaxy.jpg")
asteroids = []
for i in range(10):
    asteroid = Actor(
        # The `position` attribute in the code snippet you provided is setting the initial position of
        # the asteroids within the game world.
        position=(
            random.randint(30, world.width - 30),
            random.randint(30, world.height - 30),
        )
    )
    asteroid.add_costume("images/asteroid.png")
    asteroid.size = (30, 30)
    asteroid.direction = random.randint(0, 360)

    @asteroid.register
    def act(self):
        borders = self.detect_borders()
        if borders:
            self.bounce_from_border(borders)
        self.move()

    asteroids.append(asteroid)

player = Actor(position=(40, 40))
player.add_costume("images/ship.png")
player.size = (30, 30)
player.costume.orientation = -90


@player.register
def on_key_pressed_a(self):
    self.turn_left(10)


@player.register
def on_key_pressed_d(self):
    self.turn_right(10)

@player.register
def on_key_pressed_w(self):
    self.move(1)

@player.register
def on_key_pressed_s(self):
    self.move_back(1)
    
@player.register
def on_key_down_space(self):
    laser = Actor()
    laser.direction = self.direction
    laser.add_costume("images/laser.png")
    laser.size = (30, 30)
    laser.center = self.center
    laser.costume.is_upscaled = True
    laser.costume.orientation = 180
    laser.speed = 15
    laser.world.play_sound("sounds/laser.wav")

    @laser.register
    def act(self):
        self.move()

    @laser.register
    def on_detecting(self, other):
        if other in asteroids:
            other.remove()
            explosion = Actor((self.position[0] + 40, self.position[1] + 40))
            explosion.size = (128, 128)
            explosion.add_costume()
            explosion.costume.add_images(
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
            explosion.costume.animation_speed = 10
            explosion.costume.is_animated = True
            world.play_sound("sounds/explosion.wav")
            ActionTimer(24, explosion.remove)
            self.remove()


@player.register
def on_detecting_actor(self, token):
    if token in asteroids:
        explosion = Actor((self.position[0] + 40, self.position[1] + 40))
        explosion.size = (128, 128)
        explosion.add_costume()
        explosion.costume.add_images(
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
        explosion.costume.animation_speed = 10
        explosion.costume.is_animated = True
        ActionTimer(24, explosion.remove)
        world.play_sound("sounds/explosion.wav")
        self.remove()


@player.register
def on_detecting_borders(self, borders):
    self.bounce_from_border(borders)


random.seed()
world.run()
