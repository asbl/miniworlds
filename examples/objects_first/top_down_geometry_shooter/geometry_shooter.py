from miniworlds import World, Rectangle, Circle
import random

world = World(400, 400)
world.world_size_x = 5000
world.world_size_y = 5000
cooldown = 0
bullets = []
enemies = []
player = Rectangle((25, 25))
player.finder = True
player.size = (30, 30)
world.camera.from_actor(player)


@player.register
def act(self):
    world.camera.from_actor(player)
    global cooldown
    cooldown -= 1


@player.register
def on_key_pressed_w(self):
    self.move(3)


@player.register
def on_key_pressed_a(self):
    self.turn_left(5)


@player.register
def on_key_pressed_d(self):
    self.turn_right(5)


@player.register
def on_key_pressed_s(self):
    self.move(-1)


@player.register
def on_key_down_space(self):
    print("space")
    global cooldown
    global bullets
    if cooldown <= 0:
        cooldown = 50
        bullet = Circle()
        bullet.color = (0, 255, 0, 100)
        bullet.radius = 10
        bullet.center = player.center
        bullet.direction = player.direction
        bullet.lifetime = 60
        bullet.speed = 5
        bullets.append(bullet)

        @bullet.register
        def act(self):
            self.lifetime -= 1
            self.move(self.speed)
            if self.lifetime < 0:
                bullets.remove(self)
                self.remove()

        @bullet.register
        def on_detecting(self, other):
            if other in enemies:
                self.remove()
                enemies.remove(other)
                kill_enemy(other)

@player.register
def act(self):
    print("in view?", self.world.camera.is_actor_in_view(self), self.position_manager.get_global_rect(), self.world.camera.rect)
    
def create_enemy():
    enemy = Circle((random.randint(400, 5000), random.randint(400, 5000)))
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    size = random.randint(10, 200)
    enemy.radius = random.randint(20,120)
    enemy.static = True
    enemy.chasing = True
    enemy.speed = (1 - (size / 200)) * 3
    enemies.append(enemy)
    enemy.color = (r, g, b)
    @enemy.register
    def act(self):
        pass
        # print("enemy pos", enemy.center, enemy.rect, enemy.size)


def kill_enemy(enemy):
    global enemies
    center = enemy.center
    direction = enemy.direction
    radius = enemy.radius
    if enemy in enemies:
        enemies.remove(enemy)
    enemy.remove()
    if radius > 20:
        create_children(center, direction, radius)


def create_children(center, direction, radius):
    global enemies
    for d in [direction + 90, direction - 90]:
        enemy = Circle()
        enemy.center = center
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        enemy.steps = random.randint(50, 100)
        enemy.direction = d
        enemy.radius = radius / 2
        enemy.chasing = False
        enemies.append(enemy)


@world.register
def act(self):
    global enemies
    if self.frame % 6 == 0:
        for enemy in enemies:
            if not enemy.chasing:
                enemy.move()
                enemy.steps -= 1
                if enemy.steps < 0:
                    enemy.chasing = True
            if enemy.chasing:
                enemy.point_towards_actor(player)
                enemy.move(enemy.speed)


# Enemies
for _ in range(200):
    create_enemy()
world.run()
