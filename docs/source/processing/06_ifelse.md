# Verzweigungen

Verzweigungen brauchst du immer dann, wenn du Bedingungen überprüfen willst und davon der Programmfluss abhängen soll.

### Erstes Beispiel

Willst du z.B. in deinem Spiel überpfüen, ob ein bestimmter Punktestand erreicht wurde, so geht dies mit einer Anweisung

``` python
if points > 100:
    print("You have won!")
```

### Allgemeine Syntax

Allgemein ist dies die Syntax für Verzweigungen:

``` python
if <Bedingung>:
    <Code Block>
```
### Boolsche Ausdrücke

Eine Bedingung ist ein Ausdruck, der den Wert `True` oder `False` besitzen 
kann - Man nennt solche Ausdrücke *boolsche Ausdrücke*.

Die einfachsten boolschen Ausdrücke sind `True` und `False`. Weitere Ausdrücke erhälst du i.d.R. mit **Vergleichen**, z.B.:

``` python
10 < 100 # True
110 < 100 # False
x < 10 # True, if x < 10
"a" == "b" # False
3 == 4 # False
"ab" == "ab" # True
```

Die Ausdrücke können beliebig kompliziert sein und Variablen enthalten.

```{warning}
Achtung: Bei Vergleichen verwendet man immer ein doppeltes Gleichheitszeichen anstelle eines einfachen Gleichheitszeichen
```

### Vergleiche

Folgende Vergleiche kannst du verwenden:

* `<`: Kleiner als
* `<=` : Kleiner als oder gleich 
* `==`: Gleich
* `>=`: Größer als oder gleich
* `>` Größer als

### Code Blöcke

Willst du mehrere Anweisungen abhängig von der Bedingung durchführen, so geht dies mit Hilfe von Code-Blöcken. Code-Blöcke sind stets gleichweit eingerückt und alle Anweisungen die entsprechend eingerückt sind, werden 

Beispiel:

``` python
if points > 100:
    print("You have won!")
    print("Congratulations")
print("The game is over")
```

Unabhängig von der Punktzahl wird die letzte Code-Zeile auf jeden Fall ausgeführt. Die beiden eingerückten Zeilen werden allerdings nur ausgeführt, wenn der Punktestand größer als 100 ist.

## Elif und Else

Mit elif und else kannst du Alternativen einbauen. Dies geht z.B. so:

``` python
if points > 100:
    print("You have won!")
    print("Congratulations")
elif points > 50:
    print("you lost by a narrow margin")
else: 
    print("you have clearly lost)
```

Die allgemeine Syntax ist:

``` python
if <Bedingung>:
    <Code Block>
elif <Bedingung>:
    <Code Block>
else <Bedingung>:
    <Code Block>
```

Sowohl elif als auch else können dabei weggelassen werden. Es sind auch mehrere elif-Blöcke möglich.

## Ausführliches Beispiel

Ein Rechteck soll sich von rechts nach links bewegen. Wenn es die linke Seite erreicht, soll es wieder ganz rechts auftauchen.

Die erste Variante sieht so aus:

``` python
from miniworlds import *

world = World(300, 200)

rect = Rectangle((280,120), 20, 80)

@rect.register
def act(self):
    rect.x -= 1


world.run()
```

Es fehlt noch der entscheidende Teil.

Diesen kann man so formulieren:

`Falls die x-Koordinate den Wert 0 erreicht, setze das Rechteck wieder nach rechts`

Dies kann man direkt in Python übersetzen:

``` python
from miniworlds import *

world = World(300, 200)

rect = Rectangle((280,120), 20, 80)

@rect.register
def act(self):
    rect.x -= 1
    if rect.x == 0:
        rect.x = 280

world.run()
```

## Ein weiteres Beispiel - Ein simples Flappy-Bird

Wir wollen eine Art (einfaches) Flappy-Bird programmieren.

Unser Hauptcharakter soll ein Ball sein, der bei Tastendruck sich nach oben bewegt.
Dies können wir wie folgt realisieren:

``` python
from miniworlds import *

world = World(300, 200)

rect = Rectangle((280,120), 20, 80)
ball = Circle((20,50),20)
velocity = 1
@rect.register
def act(self):
    rect.x -= 1
    if rect.x == 0:
        rect.x = 280

@ball.register
def act(self):
    global velocity
    self.y += velocity
    if world.frame % 10 == 0:
        velocity += 1
    
world.run()
```

Der Ball fällt und fällt immer schneller.

In der Zeile:

``` python
    if world.frame % 10 == 0:
        velocity += 1
```

wird die Geschwindigkeit erhöht, mit der der Ball fällt. 
Im ersten Schritt soll sich der Ball nach oben bewegen können, wenn eine Taste gedrückt wird.

``` python
from miniworlds import *

world = World(300, 200)

rect = Rectangle((280,120), 20, 80)
ball = Circle((20,50),20)
velocity = 1
@rect.register
def act(self):
    rect.x -= 1
    if rect.x == 0:
        rect.x = 280

@ball.register
def act(self):
    global velocity
    self.y += velocity
    if world.frame % 10 == 0:
        velocity += 1

@ball.register
def on_key_down(self, key):
    global velocity
    velocity = -2
world.run()
```

### Kolissionen

Nun wollen wir nicht nur einfach Positionen vergleichen, sondern auch die Lage von Objekten zueinander.

Dafür können wir verschiedene `sensor`-Methoden verwenden.

Dies geht z.B. so:

``` python
from miniworlds import *

world = World(300, 200)

rect = Rectangle((280,120), 20, 80)
ball = Circle((20,50),20)
velocity = 1
@rect.register
def act(self):
    rect.x -= 1
    if rect.x == 0:
        rect.x = 280

@ball.register
def act(self):
    global velocity
    self.y += velocity
    if world.frame % 10 == 0:
        velocity += 1
    actor = self.detect_actor()
    if actor == rect:
       self.world.stop()

@ball.register
def on_key_down(self, key):
    global velocity
    velocity = -2
world.run()
```

Die Logik befindet sich in folgenden Zeilen:

``` python
    actor = self.detect_actor()
    if actor == rect:
       self.world.stop()
```

Die erste Zeile überprüft mit einem Sensor, welches Actor an der eigenen Position gefunden wurde (und gibt das erste gefundene Actor zurück).
Anschließend wird das so gefundene Actor mit dem Rechteck verglichen. Wenn dies die gleichen Objekte sind, dann wird das Spiel abgebrochen.

So sieht das Flappy-Bird-Spiel nun aus:

 <video controls loop width=300px>
  <source src="../_static/flappy.webm" type="video/webm">
  Your browser does not support the video tag.
</video> 