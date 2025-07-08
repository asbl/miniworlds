# Additional Sensors

## Checking World Boundaries

You can also use sensors to check whether an actor is at the edges or outside the boundaries of the world.

### Is the Actor Outside the World?

This function checks whether an actor is no longer within the current world:

```python
@player3.register
def on_not_detecting_world(self):
    print("Warning: I'm not on the world!!!")
```

### Example: A Fish That Turns Around at the World Borders

The following program simulates a fish that automatically turns around when it reaches the edges of the world:

```python
from miniworlds import TiledWorld, Actor 

world = TiledWorld()
world.columns = 4
world.rows = 1
world.add_background("images/water.png")

fish = Actor((0, 0))
fish.add_costume("images/fish.png")
fish.costume.orientation = -90
fish.direction = "right"

@fish.register
def act(self):
    self.move()

@fish.register
def on_not_detecting_world(self):
    self.move_back()
    self.flip_x()  # The fish turns around when it reaches the edge

world.run()
```

### Output

<video controls loop width=300px>
  <source src="../_static/flipthefish.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

### Explanation

* The method `on_not_detecting_world` is called only when the fish is detected as being outside the world.
* It moves the fish back using `move_back()` and then flips its direction with `flip_x()`.

---

## Detecting World Borders

You can also check whether an actor has **reached or touched** the boundaries of the world:

### Is the Actor Touching the Borders?

```python
@player4.register
def on_detecting_borders(self, borders):
    print("Borders are here!", str(borders))
```

**Explanation:**

* When the actor touches one or more edges of the world (e.g., at position `(0, 0)`), the output might be:
  `Borders are here! ['right', 'top']`.
