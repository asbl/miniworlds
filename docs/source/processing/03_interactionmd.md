# Interaktion 


## on_setup und act


Bisher hast du Befehle einfach untereinander geschrieben und die Befehle wurden dann von oben nach unten abgearbeitet.

Wenn du ein interaktives Programm schreiben willst, dann musst du dies etwas durchbrechen.

Dazu kannst du Methoden **registrieren**, die zu bestimmten Zeiten aufgerufen werden oder auf bestimmte Ereignisse reagieren.

Wir fangen mit zwei einfachen Methoden an, `on_setup` und `act`

  * `on_setup` wird einmal aufgerufen, wenn das `World` erstellt wurde.

  * `act` wird immer und immer wieder aufgerufen, einmal pro Zeiteinheit.

Das folgende Programm:

``` python
from miniworlds import *

world = World()
world.size = (120,210)

@world.register
def on_setup(self):
    print("setup")
  
@world.register
def act(self):
    print("act")
```

liefert z.B. folgende Ausgabe

```
setup
act
act
act
```    

## Code-Blöcke
Die Zeile ``def on_setup(self):`` endet mit einem Doppelpunkt. Darunter siehst du einen Codeblock:

Die Inhalte der Funktion sind alle *eingerückt*, alles was gleich weit eingerückt ist, gehört zu einem Block.

``` python
from miniworlds import *

world = World()
world.size = (120,210)

@world.register
def on_setup(self):
    print("Dies ")
    print("ist ")
    print("Teil ")
    print("eines Codeblocks ")
print("Dies aber nicht")
```

Beim Aufruf von ``on_setup`` werden die vier Zeilen darunter aufgerufen, nicht aber die 5. Zeile.

.. note::
  In der Regel verwendet man in Python *4 Leerzeichen*, wenn man einen Codeblock einrückt.
  Es ist zwar kein Fehler, wenn du nur 3,2,1 oder 5 Leerzeichen oder ein Tab verwendest, solange du immer gleich 
  weit einrückst - Dies wird von erfahrenen Programmierern aber als schlecher Stil empfunden.

## Frame Rate - Wie oft wird act() aufgerufen


Man kann einstellen, wie oft ``act()`` aufgerufen wird, indem man die Attribute ``world.fps`` und ``world.speed`` konfiguriert.

* ``world.fps`` definiert die ``frame rate``. Analog zu einem Daumenkino, bei dem du mit festgelegter Geschwindigkeit die Seiten umblätterst, 
  definiert die Framerate wie oft pro Sekunde das Bild neu gezeichnet wird.
  ``world.fps`` hat den Standardwert 60, d.h. es werden 60 Bilder pro Sekunde angezeigt.

* Im Attribut ``world.frame`` wird der aktuelle frame gespeichert. Die Frames seit Programmstart werden hochgezählt.
  
* ``world.speed`` definiert wie oft die Programmlogik (z.B. act) pro Sekunde aufgerufen wird. 
  Ein Wert von 60 bedeutet, dass die act()-Methode jeden 60. Frame aufgerufen wird.

``` python
  from miniworlds import *

  world = World()
  world.size = (120,210)

  @world.register
  def on_setup(self):
      world.fps = 1
      world.speed = 3
      
  @world.register
  def act(self):
      print(world.frame)

  world.run()
```

Das Programm oben hat die Ausgabe:

```
  3
  6
  9
  12
  15
```


Es wird sehr langsam hochgezählt, weil genau ein Frame pro Sekunde abgespielt wird und jeden 3. Frame
(also alle 3 Sekunden) die Funktion ``act()`` aufgerufen wird.


````{warning}

  Achtung: Es kann zu unvorhergesehenen Nebenwirkungen führen, wenn man Code falsch einrückt, betrachte z.B. folgendes Programm:

``` python
from miniworlds import *

world = World()
world.size = (120,210)

@world.register
def on_setup(self):
    print(1)

print(2)

@world.register
def act(self):
    print(3)
print(4)

world.run()  
```

Das Programm hat die Ausgabe:

```
1
2
4
1
3
3
```

````

Dies liegt daran, dass zuerst ``on_setup()`` ausgeführt wird, nachdem in Zeile 3 das World erstellt wurde.
Anschließend werden die beiden nicht eingerückten Befehle ausgeführt und sobald ``run()`` gestartet wird, wird die Funktion
``act()`` aufgerufen. Achte darauf, dass deine Anweisungen sich innerhalb der Code-Blöcke von act und on_setup befinden.

## Maus-Interaktionen 


Interaktionen finden im miniworlds über **Events** statt. Events können durch unterschiedlichste Systemereignisse aufgerufen werden,
z.B. wenn der Benutzer eine Eingabe mit der Tastatur oder mit der Maus getätigt hat.

Zunächst schauen wir uns Mausinteraktionen an:

Mit der Methode ``get_mouse_position`` kannst du die Mausposition abfragen:

 ``` python
from miniworlds import *

world = World()

@world.register
def on_setup(self):
    world.size = (200,200)

@world.register
def act(self):
    Ellipse(world.get_mouse_position(), 10, 10) 

world.run()
```

Der Kreis folgt nun deiner Mausposition:

<img src="../_images/processing/mouse1.png" alt="Get the mouse position" width="260px">

Wenn du Linien zeichnen möchtest, benötigst du die aktuelle und die letzte Mausposition. Dies geht z.B. wie folgt:

``` python
from miniworlds import *

world = World()

@world.register
def on_setup(self):
    world.size = (200,200)

@world.register
def act(self):
    Line(world.get_prev_mouse_position(), world.get_mouse_position()) 

world.run()
```

<img src="../_images/processing/lines1.png" alt="Get the mouse position" width="260px">

## Listener-Methoden


Schön wäre es, wenn wir noch auf spezifische Events reagieren können, z.B. auf Tastendrücke oder Mausklicks. 
Dafür können wir bestimmte Listener-Methoden registrieren, z.B. ``on_mouse_pressed``

``` python
from miniworlds import *

world = World()

@world.register
def on_setup(self):
    world.size = (200,200)

@world.register
def act(self):
    Ellipse(world.get_mouse_position(), 10, 10) 

@world.register
def on_mouse_left(self, position):
    world.fill_color = (255, 0, 0)
  
@world.register
def on_mouse_right(self, position):
    world.fill_color = (255, 255, 255)
  
world.run()
```

<img src="../_images/processing/mouse2.png" alt="Get the mouse position, color changing" width="260px">

## Tastaturabgaben abfragen

Du kannst auch Angaben von der Tastatur abfragen:

``` python
from miniworlds import *

world = World()

@world.register
def on_setup(self):
    world.size = (200,200)

@world.register
def on_key_down_a(self):
    a = Ellipse.from_center((100, 100), 100, 100) 
    a.fill_color = (255, 0, 0)

@world.register
def on_key_down_b(self):
    a = Ellipse.from_center((100, 100), 100, 100) 
    a.fill_color = (0, 255, 0)

    
world.run()
```

Dieses Programm reagiert auf die Tasten a und b, beim Drücken der Taste <kbd>a</kbd> wird eine rote Ellipse gezeichnet, beim Drücken der Taste <kbd>b</kbd> eine grüne Ellipse.

### Arbeiten mit dem Zufall

Python stellt mit der random Bibliothek einige Möglichkeiten zur Verfügung, wie man interessante graphische Effekte erzeugen kann:

So wird z.B. ein Kreis in einer zufälligen Farbe erstellt:

``` python
from miniworlds import *
import random
world = World()

@world.register
def on_setup(self):
    world.size = (200,200)

@world.register
def on_key_down_a(self):
    a = Ellipse.from_center((100, 100), 100, 100) 
    a.fill_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    
world.run()
```

Ausgabe:

<img src="../_images/processing/changing_colors.gif" alt="changing colors" width="260px"/>

