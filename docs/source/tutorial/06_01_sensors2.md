
# Weitere Sensoren

## Überprüfung der Spielfeldgrenzen

Du kannst auch Sensoren verwenden, um zu überprüfen, ob sich ein Akteur an den Rändern oder außerhalb des Spielfelds befindet:

### Ist die Figur nicht mehr auf dem Spielfeld?###

Diese Funktion überprüft, ob eine Figur noch in der aktuellen Welt ist.

```python
@player3.register
def on_not_detecting_world(self):
    print("Warning: I'm not on the world!!!")
```

### Beispiel: Ein Fisch, der an den Spielfeldrändern zurückschwimmt

Das folgende Programm simuliert einen Fisch, der an den Spielfeldrändern automatisch umkehrt:

```python
from miniworlds import TiledWorld, Actor 

world = TiledWorld()
world.columns = 4
world.rows = 1
world.add_background("images/water.png")

fish = Actor((0,0))
fish.add_costume("images/fish.png")
fish.costume.orientation = -90
fish.direction = "right"

@fish.register
def act(self):
    self.move()

@fish.register
def on_not_detecting_world(self):
    self.move_back()
    self.flip_x()  # Der Fisch dreht um, wenn er den Spielfeldrand erreicht

world.run()
```

### Ausgabe

<video controls loop width=300px>
  <source src="../_static/flipthefish.webm" type="video/webm">
  Dein Browser unterstützt das Video-Tag nicht.
</video>

### Erklärung

  * Die Methode `on_not_detecting_world` wird nur aufgerufen, wenn erkannt wird, dass sich der Fisch nicht mehr in 
  der Welt befindet. er wird mit move_back wieder zurückbewegt und anschließend gedreht.


## Überprüfung auf Spielfeldgrenzen

Man kann auch überprüfen, ob die Grenzen des Spielfeldes erreicht oder berührt werden:

#### Ist die Figur an den Grenzen des Spielfelds?**

```python
@player4.register
def on_detecting_borders(self, borders):
    print("Borders are here!", str(borders))
```

Erklärung:
* Wenn sich eine Figur an den Rändern des Spielfelds befindet (z.B. an der Position `(0,0)`), wird ausgegeben: 
 `Borders are here! ['right', 'top']`.
