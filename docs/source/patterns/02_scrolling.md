# Scrolling

Often, you want the screen to “scroll.”

The simplest way to achieve this is by “moving” the background.

For it to work smoothly, the background must be created as an `Actor`, and you’ll need **two backgrounds**.

Both backgrounds move from right to left (or top to bottom, left to right, etc.—depending on your game). As soon as one background leaves the screen, it is repositioned on the right.

This creates the illusion of an “endless” landscape.

In code, this can be implemented like this:

* Create the background twice using the same background image and place them side by side.
* It’s helpful to store both backgrounds in a list so you can move them together.

```python
back0 = Actor()
back0.add_costume(BACKGROUND)
back0.size = WIDTH, HEIGHT
back1 = Actor(WIDTH, 0)
back1.size = WIDTH, HEIGHT
back1.add_costume(BACKGROUND)
backs = [back0, back1]
```

In the `world.act` method (which is called every frame), you can scroll the screen:

```python
@world.register
def act(self):
    for back in backs:
        back.x -= 1
        if back.x <= -WIDTH:
            back.x = WIDTH
```

Full example:

```python
from miniworlds import *

WIDTH, HEIGHT = 800, 400
world = World(WIDTH, HEIGHT)
left, bottom = WIDTH/2, HEIGHT/2

BACKGROUND = "desertback"

back0 = Actor()
back0.add_costume(BACKGROUND)
back0.size = WIDTH, HEIGHT
back1 = Actor(WIDTH, 0)
back1.size = WIDTH, HEIGHT
back1.add_costume(BACKGROUND)
backs = [back0, back1]

walker = Actor((100, HEIGHT - 100))
walker.size = 100, 60
walker.add_costumes(["walk1", "walk2"])
walker.speed = 1
walker.count = 0

@world.register
def act(self):
    for back in backs:
        back.x -= 1
        if back.x <= -WIDTH:
            back.x = WIDTH
    walker.count += walker.speed
    if walker.count > 11:
        costume = walker.next_costume()
        walker.count = 0

@world.register
def on_key_down(self, keys):
    if "q" in keys:
        world.quit

world.run()
```

Note: The idea comes from the blog [schockwellenreiter](http://blog.schockwellenreiter.de/2022/05/2022051502.html), where Jörg Kantereit originally implemented this snippet using Pygame Zero.
