# Movement

### Basics

Before we dive deeper into movement functions, here’s a quick recap of the core concepts:

* You can directly control an actor’s position and orientation using **`self.direction`**, **`self.x`**, **`self.y`**, and **`self.position`**.

In addition, Miniworlds provides special methods that let an actor move straight ahead or in specific directions.

## The `move()` Function

The **`move()`** method moves your actor forward in the direction they are currently facing (based on **`direction`**).
If you change the **`direction`** beforehand, the movement will automatically follow the new orientation.

```python
@player.register
def act(self):
    self.direction = "right"  # You can also use an angle, e.g., 90
    self.move()
```

## `turn_left()` and `turn_right()`

With **`turn_left()`** and **`turn_right()`**, you can rotate the actor by a specified number of degrees to the left or right:

* **`player.turn_left(degrees)`**: Rotates the actor **left** by `degrees`
* **`player.turn_right(degrees)`**: Rotates the actor **right** by `degrees`

### Example:

```python
import miniworlds 

world = miniworlds.World(400, 400)
world.add_background("images/grass.jpg")
player = miniworlds.Actor((100, 100))
player.add_costume("images/player.png")

@player.register
def act(self):
    self.move()

@player.register
def on_key_down_a(self):
    self.turn_left(30)

@player.register
def on_key_down_d(self):
    self.turn_right(30)

world.run()
```

<video controls loop width=100%>
  <source src="../_static/turn.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

## `move_in_direction()`

As an alternative to regular movement, you can use **`move_in_direction()`** to move the actor in any direction by specifying an angle.

### Example: Diagonal movement

```python
import miniworlds 

world = miniworlds.World()
world.add_background("images/grass.jpg")
player = miniworlds.Actor((100, 100))
player.add_costume("images/player.png")

@player.register
def act(self):
    self.move_in_direction(45)

world.run()
```

<video controls loop width=100%>
  <source src="../_static/movedirection.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

### Example: Move toward the mouse pointer

The following example shows how to make the actor follow the mouse pointer using **`move_in_direction()`**:

```python
import miniworlds 

world = miniworlds.World(400, 400)
world.add_background("images/grass.jpg")
player = miniworlds.Actor()
player.add_costume("images/player.png")
player.orientation = -90

@player.register
def act(self):
    self.move_in_direction(self.world.mouse.get_position())

world.run()
```

<video controls loop width=100%>
  <source src="../_static/followmouse.webm" type="video/webm">
  Your browser does not support the video tag.
</video>
