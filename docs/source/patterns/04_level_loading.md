# Level Loading

A common use case: You want to load a new level when a character reaches the edge of the screen or enters a door, etc.

You can do this as follows:

* Store your level in a database, a text file, or a simple list.
* You need a **function** that loads the level when something happens (you reach the edge, touch an actor, ...)

## Storing your level as a list

You can store your level in a two-dimensional list. A very simple case might look like this:

```python
r00 = [    "  d",
           "  w",
           "www"]
```

You then need a translation to actors — `w` stands for `Wall`, `d` for `Door`.

You can store your rooms in a list or a dictionary, for example:

```python
rooms = [r00, r01]
```

...or like this:

```python
rooms = {0: r00, 1: r01}
```

### Creating classes for individual objects

To create objects of a specific kind, it's useful to define a class:

```python
class Wall(Actor):
    def on_setup(self):
        self.add_costume("wall")
```

## Translating the list

You can now translate the list into actors:

```python
def setup_room(room):
    for actor in world.actors:
        if actor != player:
            actor.remove()
    for i, row in enumerate(room):
        for j, column in enumerate(row):
            x = j
            y = i
            if room[i][j] == "w":
                t = Wall(x, y)
            if room[i][j] == "d":
                d = Door(x, y) 
```

## Switching rooms

With the groundwork done, switching rooms is easy — just call `setup_room` at the right moment:

```python
def on_key_down(self, keys):
    global r01
    if "SPACE" in keys:
        if self.detect_actor(Wall):
            setup_room(rooms[1]) 
```

Complete example:

```python
from miniworlds import *

world = TiledWorld()
world.columns = 3
world.rows = 3

r00 = [    "  d",
           "  w",
           "www"]

r01 =     ["w  ",
           "w  ",
           "w  ",
           ]

rooms = {0: r00, 1: r01}

class Player(Actor):
    
    def on_setup(self):
        self.add_costume("knight")
        self.costume.is_rotatable = False
        self.layer = 1
        
    def on_key_down_w(self):
        self.move_up()

    def on_key_down_s(self):
        self.move_down()

    def on_key_down_a(self):
        self.move_left()
    
    def on_key_down_d(self):
        self.move_right()
        
    def on_detecting_not_on_world(self):
        self.move_back()

    def on_detecting_wall(self, other):
        self.move_back()
        
    def on_key_down(self, keys):
        global r01
        if "SPACE" in keys:
            if self.detect_actor(Wall):
                setup_room(rooms[1])

class Wall(Actor):
    def on_setup(self):
        self.add_costume("wall")

class Door(Actor):
    def on_setup(self):
        self.add_costume("door_closed")


@world.register
def on_setup(self):
    setup_room(r00)
    
def setup_room(room):
    for actor in world.actors:
        if actor != player:
            actor.remove()
    for i, row in enumerate(room):
        for j, column in enumerate(row):
            x = j
            y = i
            if room[i][j] == "w":
                t = Wall(x, y)
            if room[i][j] == "d":
                d = Door(x, y)                
                
player = Player(0, 0)
world.run()
```

When the player is on the door and presses the spacebar, the room changes.
