# Sensors

Actors have **sensors** that allow them to scan their environment — for example, to detect other actors at their position.

There are two ways to use sensors:

1. You can **actively** detect other objects.
2. You can **register events** that are triggered by sensor detection.

## Actively Detecting Objects

You can actively detect objects by using an actor’s sensors directly.
Here’s an example of how it works:

```python
import miniworlds 

world = miniworlds.World(200, 100)

r = miniworlds.Rectangle((10, 10), 50, 100)
c = miniworlds.Circle((200, 50), 20)

@c.register
def act(self):
    self.move_left()

@r.register
def act(self):
    actor = self.detect()  # Sensor detects objects at current position
    if actor:
        self.color = (255, 0, 0)  # Change color if an object is detected

world.run()
```

### Output

<video controls loop width=300px>
  <source src="../_static/sensor.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

### Explanation

* In the rectangle’s `act()` method, the sensor **`self.detect()`** checks if there’s another actor at the same position.
* If another actor is detected, the rectangle changes color.
* The variable `actor` contains the detected object, or `None` if nothing is found.
* The line `if actor` is shorthand for `if actor != None`.

---

## Registering Detection Events

In the example above, actors **actively** checked for collisions.
Alternatively, you can register a method that is automatically triggered when a sensor detects something:

```python
from miniworlds import World, Rectangle, Circle

world = World(200, 100)

r = Rectangle((10, 10), 50, 100)
c = Circle((200, 50), 20)

@c.register
def act(self):
    self.move_left()

@r.register
def on_detecting(self, other):
    self.color = (255, 0, 0)  # Change color when another object is detected

world.run()
```

### Explanation:

* The method **`on_detecting(self, other)`** is called automatically when an object is detected.
* The `other` parameter refers to the detected object, allowing you to identify what was found.

---

## Detecting Specific Objects

Using sensors along with **if-else statements**, you can distinguish which object was detected:

```python
import miniworlds 

world = miniworlds.World(200, 100)

r = miniworlds.Rectangle((10, 10), 50, 100)

c1 = miniworlds.Circle((200, 50), 20)
c2 = miniworlds.Circle((120, 50), 20)

@c1.register
def act(self):
    self.move_left()

@c2.register
def act(self):
    self.move_left()

@r.register
def on_detecting(self, other):
    if other == c1:
        self.color = (255, 0, 0)  # Turn red when detecting c1
    elif other == c2:
        self.color = (0, 255, 0)  # Turn green when detecting c2

world.run()
```

### Output

<video controls loop width=300px>
  <source src="../_static/sensor2.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

### Explanation

In the **`on_detecting`** method, the actor checks whether it has detected **`c1`** or **`c2`** and changes color accordingly.

```{note}
**Note: Global Variables** — Normally, variables are only accessible within a method.  
Accessing global variables (as in this example) is simple but can cause unwanted side effects.  
You’ll learn how to avoid this in the *classes_first* tutorial.
```

---

## Example: Prevent Actors from Passing Through Walls

Sensors can also be used to prevent actors from walking through walls.
Here’s an example:

```python
import miniworlds 

world = miniworlds.TiledWorld()
world.columns = 8
world.rows = 2
world.speed = 30

player = miniworlds.Actor()
player.add_costume("images/player_1.png")

wall = miniworlds.Actor((4, 0))
wall.add_costume("images/wall.png")

@player.register
def act(self):
    if player.position != (0, 4):
        player.direction = "right"
        player.move()

@player.register
def on_detecting(self, other):
    if other == wall:
        self.move_back()  # Move back when wall is detected

world.run()
```

<video controls loop width=300px>
  <source src="../_static/wall.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

---

## FAQ

**My collision detection doesn’t work — what can I do?**

First, test whether your method is even being called. Add a `print` statement like this:

```python
@player.register
def on_detecting(self, actor):
    print(actor)
```

If nothing prints, the sensor is not working as expected.
