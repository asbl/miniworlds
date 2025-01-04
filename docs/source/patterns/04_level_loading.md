# Level Loading

Ein typischer Anwendungsfall: Du möchtest ein neues Level starten, wenn die Bildschirmfigur den Rand erreicht oder durch eine Tür geht, usw.

Dies geht folgendermaßen:

* Speichere dein Level in einer Datenbank, einer Textdatei oder einer einfachen Liste.
* Du brauchst eine **Funktion**, die dein Level lädt, sobald etwas passiert (du erreichst den Rand, berührst ein Actor, ...)

## Speichern deines Levels als Liste

Du kannst dein Level in einer mehrdimensionalen Liste speichern. In einem ganz einfachen Fall könnte dies z.B. so aussehen:

``` python
r00 = [    "  d",
           "  w",
           "www"]
```

Du brauchst dann eine Übersetzung in Actors, `w` steht hier für eine `Wall`, `d` für eine `Door`.

Die Räume kannst du dann in einer Liste oder als Dictionary speichern, z.B. so als Liste:

``` python
rooms = [r00, r01]
```

...oder so als Dictionary:

``` python
rooms = {0: r00, 1: r01}
```

### Anlegen von Klassen für die einzelnen Objekte

Damit ein Objekt einer *bestimmten Art* erzeugt werden kann, ist es sinnvoll, eine Klasse für dieses Objekt zu speichern.

Dies könnte z.B. so aussehen:

``` python
class Wall(Actor):
    def on_setup(self):
        self.add_costume("wall")
``` 

Die Klasse `Wall` definiert Objekte, sich wie Actors verhalten, aber von dem Standard-Actor insofern unterscheidet, dass diese immer als Kostüm ein Bild mit einer Wand besitzen.

## Übersetzen der Liste

Die Liste kannst du nun in Actors übersetzen:

``` python
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

Zunächst werden in der ersten For-Schleife alle Actors bis auf das Player-Objekt gelöscht

In der zweiten Schleife wird nun über die Listen iteriert. Dabei wird jedesmal, wenn ein entsprechender Actor in der String-Liste gefunden wird, ein entsprechendes Actor angelegt.

## Wechseln des Raums

Mit der Vorarbeit ist es einfach den Raum zu wechseln: Du musst einfach nur die Methode setup_room an geeigneter Stelle aufrufen um den Raum zu wechseln, z.B. so:

``` python
    def on_key_down(self, keys):
        global r01
        if "SPACE" in keys:
            if self.detect_actor(Wall):
                setup_room(rooms[1]) 
```

So könnte das ganze Programm aussehen:

``` python
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

Sobald ein Spieler auf der Tür steht und die Leertaste drückt, wird der Raum gewechselt.

![Room switching](../_images/room_switching.png)