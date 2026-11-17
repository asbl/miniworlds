# Tutorial: Place Enemies on a Canvas

In the [maze game](maze_game.md) the level is a **tilemap**: a 2D list in which
every cell holds a number, and every number stands for an actor class.
That works well for a `TiledWorld`, where everything sits on a fixed grid.

Many games have no grid. Enemies stand wherever the level designer wants
them. In this tutorial you use a normal `World` as a free **canvas**,
place different enemy types on it with the mouse, and store the result in a
**data structure**. From that data you can rebuild the level at any time.

The idea is the same as in the maze game:

| Maze game (`TiledWorld`) | This tutorial (`World`) |
|--------------------------|--------------------------|
| 2D list of numbers       | list of dictionaries     |
| `tiles = [None, Wall, Player]` | `ENEMY_TYPES = {"zombie": Zombie, ...}` |
| position = `(column, row)` | position = `(x, y)` in pixels |

The tutorial needs no image files. Enemies are drawn as colored squares.
Later you can replace them with `add_costume("...")`.

---

## Step 1: A canvas and different enemy types

A `World(width, height)` is a free canvas measured in pixels. Create one
subclass of `Actor` for each **type** of enemy:

```python
import miniworlds

world = miniworlds.World(400, 300)
world.add_background((30, 30, 40))


class Zombie(miniworlds.Actor):
    def on_setup(self):
        self.size = (30, 30)
        self.fill_color = (0, 160, 0)


class Bat(miniworlds.Actor):
    def on_setup(self):
        self.size = (24, 24)
        self.fill_color = (150, 0, 200)


class Ghost(miniworlds.Actor):
    def on_setup(self):
        self.size = (34, 34)
        self.fill_color = (220, 220, 220)


Zombie((80, 80))
Bat((200, 150))
Ghost((320, 220))

world.run()
```

`Zombie((80, 80))` creates an enemy at pixel position `x=80`, `y=80`.
Every enemy type has its own look, but all share the same base class.

---

## Step 2: Store the enemies in a data structure

If you create enemies directly in the code, you cannot save them or change
them later. Better: **first** describe the level as data, **then** create the
actors from that data.

An enemy is described by its type and its position. A dictionary is a good
fit for this, and a list holds all enemies of the level:

```python
enemy_data = [
    {"type": "zombie", "x": 80, "y": 80},
    {"type": "bat", "x": 200, "y": 150},
    {"type": "ghost", "x": 320, "y": 220},
]
```

Just like `tiles` in the maze game, a second structure translates the text
in `"type"` into a class:

```python
ENEMY_TYPES = {
    "zombie": Zombie,
    "bat": Bat,
    "ghost": Ghost,
}
```

Now one function builds the whole level from the data:

```python
def build_enemies(data):
    for actor in list(world.actors):
        actor.remove()
    for entry in data:
        enemy_class = ENEMY_TYPES[entry["type"]]
        enemy_class((entry["x"], entry["y"]))


build_enemies(enemy_data)
```

First all existing actors are removed, so you can call the function again
at any time, for example to load a different level.

```{note}
`list(world.actors)` creates a copy of the list. Without the copy you would
change the list while looping over it.
```

---

## Step 3: Place enemies with the mouse

Now the level is created interactively. The player (here: the level
designer) selects an enemy type with the keys `1`, `2` and `3` and
places it with a left click. Each click does two things:

1. It adds a new entry to `enemy_data`.
2. It creates the matching actor.

```python
selected = "zombie"


@world.register
def on_key_down(self, keys):
    global selected
    if "1" in keys:
        selected = "zombie"
    if "2" in keys:
        selected = "bat"
    if "3" in keys:
        selected = "ghost"


@world.register
def on_mouse_left_down(self, mouse_pos):
    enemy_data.append({"type": selected, "x": mouse_pos[0], "y": mouse_pos[1]})
    ENEMY_TYPES[selected](mouse_pos)
```

```{important}
Use `on_mouse_left_down` here and not `on_mouse_left`. `on_mouse_left` is
called again and again **as long as** the button is held, so one click would
create several enemies. `on_mouse_left_down` fires exactly once per click.
```

---

## Step 4: Remove enemies

A right click removes the enemy closest to the mouse. Remove the entry from
the **data** and rebuild the level, so data and actors always match:

```python
@world.register
def on_mouse_right_down(self, mouse_pos):
    for entry in reversed(enemy_data):
        close_x = abs(entry["x"] - mouse_pos[0]) < 20
        close_y = abs(entry["y"] - mouse_pos[1]) < 20
        if close_x and close_y:
            enemy_data.remove(entry)
            break
    build_enemies(enemy_data)
```

`reversed(...)` checks the enemy placed last first. That is the one drawn
on top.

The important design rule: **the data is the truth.** The actors are only a
view of it. Whenever something changes, change the data first.

---

## Step 5: Save and load

Because the level is a list of dictionaries made of text and numbers, you can
store it directly as a JSON file with the standard module `json`:

```python
import json


def save_level(filename):
    with open(filename, "w") as file:
        json.dump(enemy_data, file)


def load_level(filename):
    global enemy_data
    with open(filename) as file:
        enemy_data = json.load(file)
    build_enemies(enemy_data)
```

Call them from the key handler, for example with `s` for save and `l` for
load:

```python
@world.register
def on_key_down(self, keys):
    global selected
    if "1" in keys:
        selected = "zombie"
    if "2" in keys:
        selected = "bat"
    if "3" in keys:
        selected = "ghost"
    if "s" in keys:
        save_level("enemies.json")
    if "l" in keys:
        load_level("enemies.json")
```

The file contains your level as readable text:

```json
[{"type": "zombie", "x": 80, "y": 80}, {"type": "bat", "x": 200, "y": 150}]
```

You can keep several levels in a dictionary, like the rooms in
[Level Loading](04_level_loading.md):

```python
levels = {
    1: [{"type": "zombie", "x": 80, "y": 80}],
    2: [{"type": "bat", "x": 200, "y": 150}, {"type": "ghost", "x": 300, "y": 90}],
}

build_enemies(levels[2])
```

---

## Step 6: Give each enemy type its own behavior

Because every type is its own class, each one can behave differently. Add an
`act` method. It is called once per frame:

```python
class Zombie(miniworlds.Actor):
    def on_setup(self):
        self.size = (30, 30)
        self.fill_color = (0, 160, 0)
        self.speed = 1

    def act(self):
        self.x += self.speed
        if self.x < 0 or self.x > self.world.width:
            self.speed = -self.speed


class Bat(miniworlds.Actor):
    def on_setup(self):
        self.size = (24, 24)
        self.fill_color = (150, 0, 200)
        self.speed = 2

    def act(self):
        self.y += self.speed
        if self.y < 0 or self.y > self.world.height:
            self.speed = -self.speed
```

Zombies patrol horizontally, bats fly up and down, ghosts stay in place.
Because `build_enemies` only needs the type and the position, the data
structure does not change when you add behavior.

---

## Complete example

```python
import json
import miniworlds

world = miniworlds.World(400, 300)
world.add_background((30, 30, 40))


class Zombie(miniworlds.Actor):
    def on_setup(self):
        self.size = (30, 30)
        self.fill_color = (0, 160, 0)
        self.speed = 1

    def act(self):
        self.x += self.speed
        if self.x < 0 or self.x > self.world.width:
            self.speed = -self.speed


class Bat(miniworlds.Actor):
    def on_setup(self):
        self.size = (24, 24)
        self.fill_color = (150, 0, 200)
        self.speed = 2

    def act(self):
        self.y += self.speed
        if self.y < 0 or self.y > self.world.height:
            self.speed = -self.speed


class Ghost(miniworlds.Actor):
    def on_setup(self):
        self.size = (34, 34)
        self.fill_color = (220, 220, 220)


ENEMY_TYPES = {"zombie": Zombie, "bat": Bat, "ghost": Ghost}
selected = "zombie"
enemy_data = []


def build_enemies(data):
    for actor in list(world.actors):
        actor.remove()
    for entry in data:
        enemy_class = ENEMY_TYPES[entry["type"]]
        enemy_class((entry["x"], entry["y"]))


def save_level(filename):
    with open(filename, "w") as file:
        json.dump(enemy_data, file)


def load_level(filename):
    global enemy_data
    with open(filename) as file:
        enemy_data = json.load(file)
    build_enemies(enemy_data)


@world.register
def on_key_down(self, keys):
    global selected
    if "1" in keys:
        selected = "zombie"
    if "2" in keys:
        selected = "bat"
    if "3" in keys:
        selected = "ghost"
    if "s" in keys:
        save_level("enemies.json")
    if "l" in keys:
        load_level("enemies.json")


@world.register
def on_mouse_left_down(self, mouse_pos):
    enemy_data.append({"type": selected, "x": mouse_pos[0], "y": mouse_pos[1]})
    ENEMY_TYPES[selected](mouse_pos)


@world.register
def on_mouse_right_down(self, mouse_pos):
    for entry in reversed(enemy_data):
        close_x = abs(entry["x"] - mouse_pos[0]) < 20
        close_y = abs(entry["y"] - mouse_pos[1]) < 20
        if close_x and close_y:
            enemy_data.remove(entry)
            break
    build_enemies(enemy_data)


world.run()
```

| Input | Action |
|-------|--------|
| `1`, `2`, `3` | select zombie, bat or ghost |
| left click | place the selected enemy |
| right click | remove the enemy under the mouse |
| `s` / `l` | save / load `enemies.json` |

---

## Summary

* A normal `World` is a free canvas, positions are pixels.
* A **list of dictionaries** describes the level. A **dictionary of classes**
  translates type names into actors, like `tiles` in the maze game.
* One function `build_enemies(data)` creates all actors from the data.
* Change the data first, then rebuild. Then saving, loading and switching
  levels come almost for free.
* Use `on_mouse_left_down` for single clicks.

Ideas to continue: add a fourth enemy type, store extra properties such as
`"speed"` or `"health"` in each dictionary, or add a player and a
"play" mode that starts the enemies moving only after you press a key.
