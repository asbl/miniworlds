## Concept: Framerate

You can configure how often the `act()` method is called by adjusting the attributes `world.fps` and `world.speed`.

* `world.fps` defines the **frame rate**.
  Like a flipbook where pages are turned at a fixed speed, the frame rate defines **how many times per second the screen is redrawn**.
  The default value is `60`, which means **60 frames per second**.

* `world.frame` stores the **current frame count**.
  It increases continuously from the start of the program.

* `world.speed` defines how often the **game logic** (e.g., `act`) is called per second.
  A value of `3` means the `act()` function is called **every third frame**.

---

### Example

```python
import miniworlds 

world = miniworlds.World()
world.size = (120, 210)

@world.register
def on_setup(self):
    world.fps = 1
    world.speed = 3

@world.register
def act(self):
    print(world.frame)

world.run()
```

---

### Output:

```
3
6
9
12
15
```

Explanation:

* The program runs **1 frame per second**.
* The `act()` method is called **every 3rd frame**, so it is called **every 3 seconds**.
* This results in a slow and steady frame count being printed.
