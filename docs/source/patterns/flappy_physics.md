# Tutorial: Flappy Bird

In this chapter, we will create a Flappy Bird game step-by-step using the `miniworlds_physics` engine.

![Flappy Bird Game](../_images/patterns_flappy.png)

---

## Step 1: Importing the Physics Engine

Install the `miniworlds_physics` package just like you installed `miniworlds`. Then, import `PhysicsWorld`:

```python
import random
from miniworlds import Actor, Number, Text
from miniworlds_physics import PhysicsWorld  # Import the physics engine

world = PhysicsWorld(800, 600)
# Your code goes here
world.run()
```

---

## Step 2: Creating the Pipes

### Add Pipes and Store Them in a List

Add several pipes and store them in a list so their properties can be managed easily:

```python
pipes = [
    Actor(position=(300, world.height - 280)),
    Actor(position=(500, 0)),
    Actor(position=(700, world.height - 280)),
    Actor(position=(900, 0))
]
```

### Set Pipe Properties

Use a loop to set properties for all pipes:

```python
for pipe in pipes:
    pipe.direction = 0
    pipe.add_costume("images/pipe1.png")
    pipe.size = (50, 280)
    pipe.passed = False
    pipe.physics.simulation = "manual"
    pipe.physics.velocity_x = -150
    pipe.origin = "topleft"
```

For the 2nd and 4th pipes (which face down), rotate them 180 degrees:

```python
pipes[1].costume.orientation = -180
pipes[3].costume.orientation = -180
```

### Register Pipe Methods

Add two important methods to the pipes:

```python
for pipe in pipes:
    @pipe.register
    def act(self):
        if self.x < 75 and not self.passed:
            self.passed = True

    @pipe.register
    def on_detecting_left_border(self):
        self.move_to((self.x + random.randint(750, 800), self.y))
        self.passed = False
```

---

## Step 3: Creating the Bird

### Set Bird Attributes

The bird is an `Actor` with physics:

```python
bird = Actor()
bird.position = (75, 200)
bird.add_costume("images/fly.png")
bird.size = (60, 60)
bird.physics.simulation = "simulated"
bird.is_flipped = True
bird.physics.size = (0.8, 0.8)
bird.physics.shape_type = "circle"
bird.is_rotatable = False
```

### Register Bird Methods

#### Detect Screen Borders

If the bird hits the top or bottom, end the game:

```python
@bird.register
def on_detecting_borders(self, borders):
    if "bottom" in borders or "top" in borders:
        end = Text("Game over!", position=(400, 200))
        world.game_over = True
        world.stop()
```

#### Detect Collisions with Pipes

If the bird hits a pipe, end the game:

```python
@bird.register
def on_detecting_actor(self, other):
    if other in pipes:
        end = Text("Game over!", position=(200, 200))
        world.game_over = True
        world.stop()
```

#### Detect Key Input

When the space bar is pressed, the bird moves upward:

```python
@bird.register
def on_key_down_space(self):
    self.physics.velocity_y = -200
    if not world.is_running and not world.game_over:
        world.start()
```

---

## Step 4: Adding a Score

The score is shown with a static `Number` object:

```python
score = Number()
score.position = (30, 30)
score.size = (40, 40)
score.physics.simulation = "static"
```

In the pipe’s `act` method, increase the score:

```python
@pipe.register
def act(self):
    if self.x < 75 and not self.passed:
        self.passed = True
        score.inc()
```

---

## Complete Code

```python
import random
from miniworlds import Actor, Number, Text
from miniworlds_physics import PhysicsWorld

world = PhysicsWorld(800, 600)
world.game_over = False
world.add_background("images/background.png")

pipes = [
    Actor(position=(300, world.height - 280)),
    Actor(position=(500, 0)),
    Actor(position=(700, world.height - 280)),
    Actor(position=(900, 0))
]

for pipe in pipes:
    pipe.add_costume("images/pipe1.png")
    pipe.size = (50, 280)
    pipe.passed = False
    pipe.physics.simulation = "manual"
    pipe.physics.velocity_x = -150
    pipe.origin = "topleft"

    @pipe.register
    def act(self):
        if self.x < 75 and not self.passed:
            self.passed = True
            score.inc()

    @pipe.register
    def on_detecting_left_border(self):
        self.move_to((self.x + random.randint(750, 800), self.y))
        self.passed = False

pipes[1].costume.orientation = -180
pipes[3].costume.orientation = -180

score = Number()
score.position = (30, 30)
score.size = (40, 40)
score.physics.simulation = "static"

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
        end = Text("Game over!", position=(400, 200))
        world.game_over = True
        world.stop()

@bird.register
def on_detecting_actor(self, other):
    if other in pipes:
        end = Text("Game over!", position=(200, 200))
        world.game_over = True
        world.stop()

@bird.register
def on_key_down_space(self):
    self.physics.velocity_y = -200
    if not world.is_running and not world.game_over:
        world.start()

world.run()
```
