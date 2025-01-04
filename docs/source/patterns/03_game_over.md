# Game Over

Typischerweise passiert bei einem Game-Over-Event folgendes:

1. Das Spiel wird angehalten
2. Ein Text erscheint (ggf. mit einer High-Score)
3. Es gibt eine Möglichkeit das Spiel neu zu starten.

Zunächst macht es dazu Sinn eine Methode zu erstellen, die alle Actors erstellt, die beim Start eines Spiels erstellt werden sollen:

``` python
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
    def on_detect_actor(self, other):
        if other in enemies:
            game_over()
```

In dieser Methode wird z.B. ein Spieler-Objekt erstellt und auch bereits Events an dieses Spieler-Objekt registriert.
Wenn z.B. ein anderes Actor aufgespürt wird, dann wird die `game_over`-Methode getriggert.

In der `game_over`-Methode wird das World angehalten:

``` python
def game_over():
    global running
    running  = False
    Text(100,100, "Game Over")
    world.stop()
```

Global wird überprüft, ob die SPACE-Taste gedrückt wird - Wenn das World angehalten wird, wird die `restart`-Methode getriggert:

``` python
@world.register
def on_key_down(self, keys):
    global running
    if not running and "SPACE" in keys:
        restart()
```

Die restart-Methode löscht alle Actors, startet das World erneut und ruft `setup` auf

``` python
def restart():
    global running
    enemies = []
    for actor in world.actors:
        actor.remove()
    world.start()
    running = True
    setup()
```

Insgesamt sieht dies dann so aus:


``` python
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
    def on_detect_actor(self, other):
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
