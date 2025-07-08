# Tutorial: Red Baron

In this chapter, we’ll build a side-scrolling shooter step by step.

<video controls loop width=100%>
  <source src="../_static/red_baron.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

The techniques of creating parallax backgrounds, handling speed and movement, and generating enemies are common in games. After this tutorial, you’ll be able to apply them in your own projects.

* **Based on**: `https://github.com/kantel/pygamezero/tree/master/tappyplane`
* **License**: Attribution-NonCommercial-ShareAlike 4.0 International
* **Prerequisite**: Basic knowledge of classes

---

## Step 1: Set Up the Framework

You need a world where actors can be placed. The final line must be `world.run()`:

```python
from miniworlds import World, Actor, timer, Text
world = World(800, 480)

// your code here

world.run()
```

---

## Prepare the Folder

Place your images for background, player, and enemies in the `images` folder:

```
my_code
|
|--images
|----planered1.png
|----background.png
|----groundgrass.png
|----shipbeige.png
|----shipblue.png
|----shipgreen.png
|----shippink.png
|----shipyellow.png
```

(You can find the images here: [miniworlds-cookbook - red baron](https://codeberg.org/a_siebel/miniworlds_cookbook/src/branch/main/classes_first/red_baron))

---

## Create Backgrounds

Create two backgrounds side by side to simulate infinite scrolling:

```python
back0 = Actor()
back0.add_costume("background")
back0.size = world.width, world.height
back1 = Actor(world.width, 0)
back1.size = world.width, world.height
back1.add_costume("background")
backs = [back0, back1]
```

To animate them:

```python
@world.register
def act(self):
    for back in backs:
        back.x -= 1
        if back.x <= -world.width:
            back.x = world.width
    for ground in grounds:
        ground.x -= 2
        if ground.x <= -world.width:
            ground.x = world.width
```

---

## Step 2: Create the Plane Class

### Define the Plane Class

```python
class Plane(Actor):
    def on_setup(self):
        self.add_costume("planered1")
```

### Create an Instance

At the end of your code:

```python
plane = Plane(100, world.height / 2)
```

### Add Physics

Extend `on_setup()`:

```python
    def on_setup(self):
        self.add_costume("planered1")
        self.gravity = 0.1
        self.velocity_y = 0
```

### Simulate Physics

```python
    def act(self):
        self.velocity_y += self.gravity
        self.velocity_y *= 0.9  # friction
        self.y += self.velocity_y
```

### Add Upward Force on Key Press

```python
    def on_key_down_w(self):
        self.velocity_y -= 5
```

---

## Step 3: Add Enemies

Import:

```python
from random import randint, choice
```

### Create Enemy Class

```python
class Enemy(Actor):
    def on_setup(self):
        self.add_costume(choice(enemyships))

    def reset(self):
        self.x = randint(world.width + 50, world.width + 500)
        self.y = randint(25, world.height - 85)
```

### Add Enemies

```python
enemies = []
for _ in range(10):
    enemy = Enemy()
    enemy.reset()
    enemies.append(enemy)
```

### Move Enemies

Extend `on_setup()`:

```python
def on_setup(self):
    self.add_costume(choice(enemyships))
    self.speed = -1.5
```

Then:

```python
def act(self):
    self.x += self.speed
    if self.x <= -self.width:
        self.reset()
```

---

## Step 4: Add Shooting

Create the Bullet class:

```python
class Bullet(Actor):
    def on_setup(self):
        self.add_costume("laserred")
        self.x = plane.x
        self.y = plane.y
        self.speed = 25
        self.fire = False
    
    def act(self):
        self.x += self.speed

    def on_detecting_enemy(self, enemy):
        enemy.reset()
        
    def on_detecting_not_on_world(self):
        self.remove()
```

---

## Full Example Code

...