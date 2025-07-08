# Drag and Drop

To move an actor, you need to register the events `on_mouse_left` and `on_mouse_left_released`.
You also need a variable (e.g., `dragged`) to store the state of whether an object is currently being dragged.

* When the mouse is clicked, the `dragged` variable is set to `True`.
* When the mouse is released, the actor is only moved if `dragged` is `True`. Then `dragged` is reset to `False`.

## Examples:

Move circles:

```python
import miniworlds

world = miniworlds.World(200, 200)
circle = miniworlds.Circle((30, 30), 60)
circle.direction = 90
circle.dragged = False

@circle.register
def on_mouse_left(self, mouse_pos):
    if self.detect_point(mouse_pos):
        self.dragged = True

@circle.register
def on_mouse_left_released(self, mouse_pos):
    if self.dragged:
        self.dragged = False
        self.center = mouse_pos

world.run()
```

Drag and drop on a TiledWorld:

```python
import miniworlds 
world = miniworlds.TiledWorld()
t1 = miniworlds.Actor((0, 0))
t2 = miniworlds.Actor((3, 4))
t2.dragged = False

@t2.register
def on_mouse_left(self, mouse_pos):
    if self.detecting_point(mouse_pos):
        self.dragged = True
        print("start drag")

@t2.register
def on_mouse_left_released(self, mouse_pos):
    tile = mouse_pos
    if self.dragged:
        self.position = tile
    self.dragged = False

world.run()
```
