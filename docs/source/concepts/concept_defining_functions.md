# Concept: Functions, Parameters, and Return Values

So far, you’ve used methods like `on_setup` or `act`, which belong to a `World` or an `Actor`.
Now you’ll learn how to create your **own functions**. Functions are *subroutines* that allow you to **reuse code** instead of repeating it.

---

## First Example

You want to create four red circles like this:

```python
import miniworlds 

world = miniworlds.World(80, 80)

c1 = Circle((20, 20), 20)
c1.color = (255, 0, 0)
c2 = Circle((60, 20), 20)
c2.color = (255, 0, 0)
c3 = Circle((60, 60), 20)
c3.color = (255, 0, 0)
c4 = Circle((20, 60), 20)
c4.color = (255, 0, 0)

world.run()
```

This works, but if you want to make **all four green**, you’d need to change **four lines**.
Instead, you can use a function:

```python
import miniworlds 

world = World(80, 80)

def create_circle(x, y):
    c = miniworlds.Circle((x, y), 20)
    c.color = (255, 0, 0)

create_circle(20, 20)
create_circle(60, 20)
create_circle(60, 60)
create_circle(20, 60)

world.run()
```

---

## General: Defining Functions

When you want to automate complex tasks—like creating multiple actors—you define a function:

```python
def function_name(parameters):
    code_block
```

Example:

```python
def create_circle(x, y):
    c = Circle((x, y), 20)
    c.color = (255, 0, 0)
```

**Explanation:**

* **Function name**: `create_circle`
* **Parameters**: `x`, `y` → passed in when calling the function
* **Function body**: runs from top to bottom when the function is called

---

## Calling Functions

To use a function, write:

```python
function_name(arguments)
```

For example:

```python
create_actor(4, 2)
```

---

## Drawing Complex Figures

You can use functions to draw complex figures easily:

```python
import miniworlds 

world = miniworlds.World(400, 220)

def create_face(x, y):
    c = miniworlds.Circle((x, y), 40)
    c.color = (255, 255, 0)
    miniworlds.Circle((x + 15, y - 10), 10)
    miniworlds.Circle((x - 15, y - 10), 10)
    a = Arc((x, y + 20), 40, 20, 180, 360)
    a.center = a.position
    a.color = (255, 0, 0)

create_face(60, 60)
create_face(260, 60)
create_face(160, 160)

world.run()
```

---

## Creating Actors Automatically

This example shows how you can place multiple actors efficiently using functions:

```python
import miniworlds 

world = miniworlds.TiledWorld()
world.rows = 8

def create_actor(x, y):
    t = Actor()
    t.position = (x, y)
    t.add_costume("images/player.png")

def create_wall(x, y):
    t = Actor()
    t.position = (x, y)
    t.add_costume("images/wall.png")

create_actor(4, 2)
create_wall(4, 4)
create_wall(5, 4)
create_wall(6, 4)
create_wall(6, 3)
create_wall(6, 2)
create_wall(6, 1)
create_wall(5, 1)
create_wall(4, 1)
create_wall(3, 1)

world.run()
```

---

## Registering Behavior in Functions

This example creates random **raindrops**, where each has behaviors (registered with `@c.register`) defined **within** the function:

```python
import miniworlds 
import random

world = miniworlds.World()
world.add_background((80, 180, 255))

def raindrop(x, y):
    c = miniworlds.Circle((x, y), random.randint(10, 20))
    c.color = (0, 0, random.randint(100, 255), 100)
    c.static = True

    @c.register
    def act(self):
        self.move_down(random.randint(1, 3))

    @c.register
    def on_detecting_not_on_world(self):
        self.remove()

@world.register
def act(self):
    if world.frame % 5 == 0:
        raindrop(random.randint(0, 400), 0)

world.run()
```

---

## Return Values

So far, functions just did something.
With a **return value**, you can get information **back** from a function.

Example:

```python
def is_even(x):
    if x % 2 == 0:
        return True
    else:
        return False

print(is_even(4))  # Output: True
```

Another example: color a circle red if it’s on the **left half** of the screen.

```python
import miniworlds 
import random

world = miniworlds.World(400, 50)

def is_left(obj):
    if obj.x <= 200:
        return True
    else:
        return False

for i in range(20):
    x = random.randint(0, 400)
    y = 25
    c = miniworlds.Circle((x, y), 10)
    if is_left(c):
        c.color = (255, 0, 0)

world.run()
```