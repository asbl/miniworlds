# miniworlds

**miniworlds** ist eine in Python und Pygame geschriebene Spiel-Engine, die für SchülerInnen entwickelt wurde, um 2D-Miniwelten und Spiele zu erstellen.

Die Erstellung der ersten Spiele mit **minigames** ist einfach und macht Spaß.

:::{admonition} miniworlds und miniworldmaker

**miniworlds** ist das Nachfolgeprojekt des **miniworldmakers**. Sehr vieles ist ähnlich, manche Bezeichnungen
und Funktionen unterscheiden sich vom miniworldmaker.
(z.B. aus Tokens wurden Actors, aus Boards wurden Worlds)

:::

## Beispiele

### Zwei Actors, die per Tastatur gesteuert werden

Zwei Actors, die per Tastatur gesteuert werden

```python
from miniworlds import World, Actor

world = World()
world.add_background("images/grass.jpg")
player = Actor((90,90))
player.add_costume("images/player.png")
player.costume.orientation = -90
@player.register
def on_key_down_w(self):
    player.y = player.y - 1

player2 = Actor((180,180))
player2.add_costume("images/player.png")
player2.costume.orientation = -90
@player2.register
def on_key_pressed_s(self):
    player2.y = player2.y - 1

world.run()
```

```{figure} _images/examples_twoactors.png
:scale: 30 %
:alt: Example: Two actors

Example: Two actors
```

### Skeetshooting

Ein zufällig platziertes Ziel kann mit der Maus "abgeschossen" werden.

``` python
from miniworlds import World, Actor, Number
import random

world = World(400, 400)
world.add_background("images/skeetshooting.png")
target = Actor((100, 100))
target.add_costume("images/target-red.png")
target.orientation = -90
target.size = (80,80)

cooldown = 5
hits = Number((20,20), 0)

@target.register
def act(self):
    global cooldown
    if self.world.frame % 50 == 0: # every 50th frame:
        target.position = (random.randint(0, 400), random.randint(0, 400))
    cooldown -= 1

@target.register
def on_clicked_left(self, position):
    global cooldown, hits
    if cooldown < 0:
        hits += 1
        cooldown = 10
        
world.run()

```

```{figure} _images/examples_skeetshooting.png
:scale: 30 %
:alt: Example: Skeetshooting

Example: Skeetshooting
```

### Aircrafts

Klassisches Spiel, bei dem man ein Flugzeug steuert und Gegner abwehrt und ausweicht.

```python
from miniworlds import World, Actor, Circle, Text
import random

world = World(300, 600)
world.add_background("images/clouds")
world.background.is_scaled = False
aircraft = Actor((150, 500))
aircraft.add_costume("images/ship.png")

@aircraft.register
def on_setup(self):
    self.downtime = 0


@aircraft.register
def act(self):
    """Increment the downtime every frame per 1"""
    self.downtime += 1


@aircraft.register
def on_key_pressed(self, keys):
    """Move aircraft left/right with a, d keys.
    """
    if "a" in keys:
        aircraft.x -= 1
    elif "d" in keys:
        aircraft.x += 1


@aircraft.register
def on_key_down(self, keys):
    """Shoot, if downtime > 100
    """
    if " " in keys and self.downtime > 100:
        position = aircraft.center
        position = (aircraft.center[0], aircraft.center[1] - 20)
        bullet = Circle(position)
        self.downtime = 0

        @bullet.register
        def act(self):
            self.y = self.y - 1

        @bullet.register
        def on_detecting_actor(self, other):
            if other in self.world.enemies:
                other.remove()
                self.remove()


@world.register
def on_setup(self):
    self.enemies = []


@world.register
def act(self):
    if self.frame % 120 == 0:
        enemy = Actor((random.randint(30, 270), 50))
        enemy.add_costume("images/enemy.png")
        enemy.orientation = 180
        self.enemies.append(enemy)

        @enemy.register
        def act(self):
            self.y = self.y + 1

        @enemy.register
        def on_detecting_actor(self, other):
            """ If enemy detects the aircraft, the game ends.
            """
            if other == aircraft:
                self.world.stop()
                aircraft.remove()
                t = Text((150, 300), "GAME OVER")
                t.color = (0, 0, 0)
                for enemy in self.world.enemies:
                    enemy.remove()
                self.remove()
                

world.run()
```

```{figure} _images/examples_aircrafts.png
:scale: 40 %
:alt: Example: Skeetshooting

Example: Skeetshooting
```

### RPG with console and sidebar

```python
from miniworlds import TiledWorld, Toolbar, Console, Actor, Button, Label, PagerHorizontal

world = TiledWorld()
world.columns = 8
world.rows = 8
world.tile_size = 24
world.camera.world_size_x = 16
world.camera.world_size_y = 16
world.add_background((255, 255, 255, 255))

toolbar = Toolbar()
@toolbar.register
def on_setup(self):
    self.add_background("images/bg")
    self.background.set_mode(mode="textured", texture_size=(200, 200))

world.toolbar = world.add_right(toolbar, size=180)

console = Console()
world.console = world.add_bottom(console, size=100)
world.console.newline("You enter a new world")

pager = PagerHorizontal(console)
world.add_bottom(pager, size=60)

def create_grass(pos):
    g = Actor(pos)
    g.add_costume("images/grass2.png")
    g.static = True
    g.layer = 0


def create_wall(pos, walls):
    w = Actor(pos)
    w.add_costume("images/wall.png")
    w.static = True
    w.is_blocking = True
    walls.append(w)


@world.register
def on_setup(self):
    for i in range(world.rows):
        for j in range(world.columns):
            create_grass((j, i))
    self.walls = []
    create_wall((0, 4), self.walls)
    create_wall((1, 4), self.walls)
    create_wall((2, 4), self.walls)
    create_wall((3, 4), self.walls)
    create_wall((4, 4), self.walls)
    create_wall((5, 4), self.walls)
    create_wall((6, 4), self.walls)
    create_wall((6, 0), self.walls)
    create_wall((6, 1), self.walls)
    create_wall((6, 3), self.walls)
    

torch = Actor((10, 4))


@torch.register
def on_setup(self):
    torch.layer = 2
    torch.add_costume("images/torch.png")


fireplace = Actor((10, 12))
fireplace.layer = 2


@fireplace.register
def on_setup(self):
    self.costume_not_burned = fireplace.add_costume("images/fireplace_0.png")
    self.burning = False
    self.costume_burned = fireplace.add_costume(
        ["images/fireplace_1.png", "images/fireplace_2.png"]
    )
    fireplace.switch_costume(self.costume_not_burned)


door = Actor((6, 2))

@door.register
def on_setup(self):
    self.add_costume("images/door_closed.png")
    self.closed = True
    self.door_open_costume = door.add_costume("images/door_open.png")
    self.switch_costume(0)
    door.layer = 2


player = Actor((8, 2))


@player.register
def on_setup(self):
    self.add_costume("images/knight")
    self.costume.is_rotatable = False
    self.layer = 3
    self.is_blockable = True


@player.register
def act(self):
    self.world.camera.from_actor(self)



@player.register_message("burn")
def burn_torch(self, sender):
    print("BURN?")
    if not fireplace.burning:
        fireplace.world.play_sound("sounds/fireplace.wav")
        fireplace.switch_costume(fireplace.costume_burned)
        fireplace.costume.is_animated = True


@player.register_message("open_door")
def open(self, sender):
    if door.closed:
        door.switch_costume(door.door_open_costume)
        door.world.play_sound("sounds/olddoor.wav")
        door.closed = False


inventory = []


@player.register
def on_key_down_w(self):
    player.move_up()


@player.register
def on_key_down_s(self):
    player.move_down()


@player.register
def on_key_down_a(self):
    player.move_left()


@player.register
def on_key_down_d(self):
    player.move_right()


@player.register_message("Torch")
def light_fireplace(self, data):
    print("light")
    found_actors = player.detect_all()
    if fireplace in found_actors:
        self.world.console.newline("You light the fireplace.")
        self.send_message("burn")
        self.world.toolbar.remove("Torch")
    else:
        self.world.console.newline("...nothing happens")


@player.register_sensor(door)
def ask_open_door(self, door):
    if door.closed:
        self.undo_move()
        message = "The door is closed - Do you want to open it?"
        reply = self.ask.choices(message, ["Yes", "No"])
        if reply == "Yes":
            self.send_message("open_door")


@player.register_sensor(torch)
def pick_up_torch(self, torch):
    reply = self.ask.choices(
        "You find a torch - Do you want to pick it up?", ["Yes", "No"]
    )
    if reply == "Yes":
        inventory.append("Torch")
        torch.remove()
        l = Label("You pick up the torch")
        line = world.console.add(l)
        
        b = Button("Torch", "images/torch.png")
        world.toolbar.add(b)


world.run()
```

```{figure} _images/examples_rpg.png
:scale: 30 %
:alt: Example: RPG

Example: RPG
```



## Credits


* `Greenfoot <https://www.greenfoot.org/>`_ 
  Miniworlds ist stark von Greenfoot inspiriert.
  
* `Kenney Assets <https://www.kenney.nl/assets>`_ 
  Die meisten Bilder der Beispiele basieren auf Kenney Assets  

Links
=====

* [Github Repository](https://github.com/asbl/miniworlds)
* [Beispiele](https://github.com/asbl/miniworlds_examples) 

```{toctree}
---
caption: Tutorial
maxdepth: 1
hidden: true
---
tutorial/01_installation
tutorial/02_00_world
tutorial/03_00_actors
tutorial/03_01_actors_position
tutorial/04_00_act
tutorial/04_01_events
tutorial/04_02_messages
tutorial/05_movement
tutorial/06_00_sensors
tutorial/06_01_sensors2
tutorial/07_animations
tutorial/09_timers
tutorial/10_status
tutorial/10_01_status2
```

```{toctree}
---
caption: Weitere Tutorials
maxdepth: 1
hidden: true
---
processing/index
```

```{toctree}
---
caption: Konzepte
maxdepth: 1
hidden: true
---
concepts/concept_conditions
concepts/concept_defining_functions
concepts/concept_framerate
concepts/concept_functions
concepts/concept_imports
concepts/concept_loops
concepts/concept_naming
concepts/concept_self
```

```{toctree}
---
caption: Anleitungen
maxdepth: 1
hidden: true
---
patterns/01_drag_and_drop
patterns/02_scrolling
patterns/03_game_over
patterns/04_level_loading
patterns/05_database
patterns/maze_game
patterns/red_baron
patterns/flappy_physics
```

```{toctree}
---
caption: API > Basics
maxdepth: 2
hidden: true
---
api/world
api/background
api/actor
api/costume
api/appearance
```

```{toctree}
---
caption: API > Actor Classes
maxdepth: 2
hidden: true
---
api/actor_number
api/actor_text
api/actor_textbox
api/actor_sensor
api/actor_shapes
api/actor_widgets
```

```{toctree}
---
caption: API > World Classes
maxdepth: 2
hidden: true
---
api/world
api/world_tiled
api/world_physics
api/world_toolbar
api/world_console
```

```{toctree}
---
caption: API > Sound & Music
maxdepth: 2
hidden: true
---
api/music
```


```{toctree}
---
caption: Helpers
maxdepth: 2
hidden: true
---
api/timer
api/positions_vector
```

```{toctree}
---
caption: Impressum
maxdepth: 2
hidden: true
---
impressum
```

Last updated: {{ build_date }}
