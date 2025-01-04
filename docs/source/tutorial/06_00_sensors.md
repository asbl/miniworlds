# Sensoren

Actors verfügen über **Sensoren**, mit denen sie ihre Umwelt abtasten 
können und z.B andere Actors an ihrer Position aufspüren können.

Es gibt zwei Möglichkeiten, Sensoren zu verwenden:

1. Du kannst Objekte "aktiv" aufspüren.
2. Du kannst Events registrieren, die durch Sensoren getriggert werden.

## Objekte aufspüren

Du kannst Objekte aufspüren, indem du die Sensoren eines Akteurs direkt nutzt. Hier ein Beispiel, wie das funktioniert:

```python
import miniworlds 

world = miniworlds.World(200, 100)

r = miniworlds.Rectangle((10,10), 50, 100)
c = miniworlds.Circle((200,50), 20)

@c.register
def act(self):
    self.move_left()

@r.register
def act(self):
    actor = self.detect()  # Sensor erkennt Objekte an der aktuellen Position
    if actor:
        self.color = (255, 0, 0)  # Ändert die Farbe, wenn ein Objekt erkannt wird

world.run()
```

### Ausgabe


<video controls loop width=300px>
  <source src="../_static/sensor.webm" type="video/webm">
  Dein Browser unterstützt das Video-Tag nicht.
</video>


### Erklärung

  * In der `act()`-Methode des Rechtecks wird der Sensor **`self.detect()`** verwendet, 
  um zu prüfen, ob sich an der aktuellen Position ein anderer Akteur befindet. Wenn das Rechteck ein Objekt erkennt, ändert es seine Farbe.
 Die Variable actor enthält den gefundenen Actor. Wenn kein Akteur gefunden wird, gibt die Methode `None` zurück.
  * Die Anweisung `if actor` ist eine Abkürzung für `if actor != None`. Man kann so überprüfen,
  ob eine Variable einen Wert enthält.



## Ereignisse registrieren

Im obigen Beispiel wurde **aktiv** nach Akteuren gesucht. 
Alternativ kannst du ein Ereignis registrieren, das automatisch aufgerufen wird, wenn der Sensor etwas entdeckt:

```python
from miniworlds import World, Rectangle, Circle

world = World(200, 100)

r = Rectangle((10,10), 50, 100)
c = Circle((200,50), 20)

@c.register
def act(self):
    self.move_left()

@r.register
def on_detecting(self, other):
    self.color = (255, 0, 0)  # Ändert die Farbe, wenn ein Objekt erkannt wird

world.run()
```

### Erklärung:

- Die registrierte Methode **`on_detecting(self, other)`** wird aufgerufen, sobald der Akteur ein anderes Objekt an seiner Position entdeckt.
- Der Parameter **`other`** repräsentiert das gefundene Objekt, sodass du herausfinden kannst, welcher Akteur entdeckt wurde.

## Unterschiedliche Objekte erkennen

Mit Sensoren und **if-else-Verzweigungen** kannst du bestimmen, welches spezifische Objekt gefunden wurde:

```python
import miniworlds 

world = miniworlds.World(200, 100)

r = miniworlds.Rectangle((10,10), 50, 100)

c1 = miniworlds.Circle((200,50), 20)
c2 = miniworlds.Circle((120,50), 20)

@c1.register
def act(self):
    self.move_left()

@c2.register
def act(self):
    self.move_left()

@r.register
def on_detecting(self, other):
    if other == c1:
        self.color = (255, 0, 0)  # Rotes Rechteck bei Erkennung von c1
    elif other == c2:
        self.color = (0, 255, 0)  # Grünes Rechteck bei Erkennung von c2

world.run()
```
### Ausgabe


<video controls loop width=300px>
  <source src="../_static/sensor2.webm" type="video/webm">
  Dein Browser unterstützt das Video-Tag nicht.
</video>


### Erklärung

In der Methode **`on_detecting`** wird überprüft, ob das erkannte Objekt **`c1`** oder **`c2`** ist, und die Farbe des Rechtecks wird entsprechend angepasst.

```{note}
**Hinweis: Globale Variablen**: Normalerweise sind Variablen nur innerhalb einer Methode bekannt. Der Zugriff auf globale Variablen, wie in diesem Beispiel, ist zwar einfach, kann jedoch unerwünschte Seiteneffekte verursachen. Im Tutorial *classes_first* lernst du, wie du solche Zugriffe vermeiden kannst.
```

## Beispiel: Kollision mit Wänden verhindern

Mit Sensoren kannst du auch verhindern, dass sich Objekte durch Wände bewegen. Hier ein Beispiel:

```python
import miniworlds 

world = miniworlds.TiledWorld()
world.columns = 8
world.rows = 2
world.speed = 30

player = miniworlds.Actor()
player.add_costume("images/player_1.png")

wall = miniworlds.Actor((4,0))
wall.add_costume("images/wall.png")

@player.register
def act(self):
    if player.position != (0,4):
        player.direction = "right"
        player.move()

@player.register
def on_detecting(self, other):
    if other == wall:
        self.move_back()  # Der Akteur bewegt sich zurück, wenn er eine Wand erkennt

world.run()
```

<video controls loop width=300px>
  <source src="../_static/wall.webm" type="video/webm">
  Dein Browser unterstützt das Video-Tag nicht.
</video>

## FAQ

**Meine Kollisionen werden nicht erkannt, was kann ich tun?**

Teste zuerst, ob die Methode überhaupt aufgerufen wird. Füge dazu eine `print`-Anweisung ein:

```python
@player.register
def on_detecting(self, actor):
    print(actor)
```

Falls die `print`-Anweisung nicht aufgerufen wird, funktioniert der Sensor nicht.
