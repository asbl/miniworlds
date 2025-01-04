# Bewegungen

### Grundlagen

Bevor wir tiefer in die Bewegungsfunktionen eintauchen, hier eine kurze Wiederholung der wichtigsten Konzepte:

- Mit **`self.direction`**, **`self.x`**, **`self.y`** und **`self.position`** kannst du die Position und Ausrichtung 
  eines Akteurs direkt steuern.

Darüber hinaus gibt es spezielle Methoden, mit denen du einen Akteur geradeaus oder in bestimmte Richtungen bewegen kannst.

## Die `move()`-Funktion

Die Methode **`move()`** bewegt deinen Akteur in die Richtung, in die er gerade schaut (basierend auf der aktuellen **`direction`**). Wenn du die **`direction`** vorher änderst, passt sich die Bewegung automatisch an die neue Ausrichtung an.

```python
@player.register
def act(self):
    self.direction = "right"  # Alternativ kann auch ein Winkel, z.B. 90, verwendet werden
    self.move()
```

## `turn_left()` und `turn_right()`

Mit **`turn_left()`** und **`turn_right()`** kannst du den Akteur um eine bestimmte Gradzahl nach links oder rechts drehen.

- **`player.turn_left(degrees)`**: Dreht den Akteur um **degrees** Grad nach links.
- **`player.turn_right(degrees)`**: Dreht den Akteur um **degrees** Grad nach rechts.

### Beispiel:

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
  Dein Browser unterstützt das Video-Tag nicht.
</video>

## `move_in_direction()`

Alternativ zur Standardbewegung kannst du den Akteur mit **`move_in_direction()`** in eine beliebige Richtung bewegen, indem du einen Winkel angibst.

### Beispiel: Bewegung schräg nach oben

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
  Dein Browser unterstützt das Video-Tag nicht.
</video>

### Beispiel: Bewegung in Richtung des Mauszeigers

Das folgende Beispiel zeigt, wie der Akteur mithilfe von **`move_in_direction()`** der Position des Mauszeigers folgt:

```python
import miniworlds 

world = miniworlds.World(400, 400)
world.add_background("images/grass.jpg")
player = miniworlds.Actor()
player.add_costume("images/player.png")
player.orientation = -90

@player.register
def act(self):
    self.move_in_direction(self.world.get_mouse_position())

world.run()
```

<video controls loop width=100%>
  <source src="../_static/followmouse.webm" type="video/webm">
  Dein Browser unterstützt das Video-Tag nicht.
</video>