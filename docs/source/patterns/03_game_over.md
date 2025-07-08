# Game Over

Typically, the following happens during a game over event:

1. The game is paused
2. A text appears (optionally with a high score)
3. There is an option to restart the game

First, it makes sense to define a method that creates all actors needed at the start of a game:

```python
def setup():
    player = Circle(40,100)
    @player.register
    def on_key_pressed(self, keys):
        global running
        if running:
            if 's' in keys:
                self.y += 1
            if 'w' in keys:
                self.y -= 1
        else:
            setup()
    @player.register
    def on_detecting_actor(self, other):
        if other in enemies:
            game_over()
```

This method creates a player object and already registers events to that player.
For example, if another actor is detected, the `game_over` method is triggered.

In the `game_over` method, the world is paused:

```python
def game_over():
    global running
    running = False
    Text(100,100, "Game Over")
    world.stop()
```

Globally, we check whether the SPACE key is pressed – if the world is stopped, the `restart` method is triggered:

```python
@world.register
def on_key_down(self, keys):
    global running
    if not running and "SPACE" in keys:
        restart()
```

The `restart` method removes all actors, restarts the world, and calls `setup`:

```python
def restart():
    global running
    enemies = []
    for actor in world.actors:
        actor.remove()
    world.start()
    running = True
    setup()
```

Complete example:

```python
from miniworlds import *
import random

running = True
enemies = []

world = World()

def setup():
    player = Circle(40,100)
    @player.register
    def on_key_pressed(self, keys):
        global running
        if running:
            if 's' in keys:
                self.y += 1
            if 'w' in keys:
                self.y -= 1
        else:
            setup()
    @player.register
    def on_detecting_actor(self, other):
        if other in enemies:
            game_over()

def game_over():
    global running
    running  = False
    Text(100,100, "Game Over")
    world.stop()
    
def restart():
    global running
    enemies = []
    for actor in world.actors:
        actor.remove()
    world.start()
    running = True
    setup()
    
def create_enemy():
    global enemies
    enemy = Circle(400, random.randint(0,400))
    enemies.append(enemy)
    @enemy.register
    def act(self):
        self.x -= 1
        if self.x < 0:
            enemies.remove(self)
            self.remove()
    
@world.register
def act(self):
    if self.frame % 50 == 0:
        create_enemy()

@world.register
def on_key_down(self, keys):
    global running
    if not running and "SPACE" in keys:
        restart()
        
setup()
world.run()
```
