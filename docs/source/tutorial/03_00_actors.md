# Actors

## Actors: Grundbausteine deiner Welt

Ein Actor ist alles, was sich in deiner Welt bewegen oder verändert werden kann. 
Es könnte ein Charakter sein, den der Spieler steuert, oder ein Objekt wie eine Wand oder ein Hindernis. 
In Miniworlds ist jeder Actor ein eigenständiges Objekt, das auf der Welt angezeigt wird und mit anderen Objekten 
interagieren kann.

## Einen Actor erstellen

angen wir damit an, einen Actor in deiner Welt zu platzieren. 
Zuerst erstellen wir eine einfache Welt mit einem Hintergrund und platzieren einen Actor.

Dies geht so:

```python
import miniworlds

# Erstelle eine Welt mit den Maßen 600x300 Pixel
world = miniworlds.World(600, 300)

# Füge einen Hintergrund hinzu (zum Beispiel ein Grasbild)
world.add_background("images/grass.png")

# Erstelle einen Actor
actor = miniworlds.Actor((100, 40))     # Actor an der Position (0, 0)

# Starte die Welt, damit sie angezeigt wird
world.run()
```

```{figure} ../_images/tutorial_addactor.png
  :scale: 50 %
  :alt: Ausgabe
  
  Ausgabe
```

### Erklärung:

* Wir erstellen einen Actor an der Position x=100, y = 40.
  Er wird als Lila-Rechteck angezeigt, da er noch über kein Kostüm verfügt.
* Beachte, dass der *Ursprung* des Koordinatensystems *oben links* liegt.
  ```{figure} ../_images/tutorial_addactor_coord.png
  :scale: 30 %
  :alt: Das Koordinatensystem
  
  Beispiel: Das Koordinatensystem
  ```
* Die Position (100, 20) bezieht sich auf den **Mittelpunkt** des Actors.

## Kostüme

Jeder Actor in Miniworlds kann ein Kostüm tragen, das sein äußeres Erscheinungsbild bestimmt. 

Ein Kostüm ist einfach ein Bild, das du deinem Actor zuweist, um ihm eine visuelle Identität zu geben.

### Schritt 1: Bilder vorbereiten

Bevor du einem Actor ein Kostüm hinzufügen kannst, musst du die entsprechenden Bilder in den images-Ordner 
deines Projekts kopieren. Ein typischer Projektaufbau könnte so aussehen:

```
project
│   my_world.py # file with your python code
└───images
│   │   grass.png
│   │   knight.png
│   │   player.png
```

### Schritt 2: Kostüm hinzufügen

Sobald du deine Bilder vorbereitet hast, kannst du mit der Methode `add_costume()` deinem Actor ein Bild als Kostüm zuweisen.



```python
from miniworlds import World, Actor
# Erstelle eine Welt mit den Maßen 600x300
world = World(600, 300)

# Füge einen Hintergrund hinzu
world.add_background("images/grass.png")

# Erstelle den ersten Actor an der Position (100, 20) und füge ein Kostüm hinzu
actor2 = Actor((100, 20))
actor2.add_costume("images/knight.png")  # "knight.png" als Kostüm

# Starte die Welt, damit die Actors sichtbar sind
world.run()
```

#### Ausgabe:

```{figure} ../_images/tutorial_firstcostume.png
  :scale: 50 %
  :alt: Ausgabe
  
  Ausgabe
```

#### Erklärung
Nach dem Ausführen siehst du einen Actor mit dem Kostüm `knight.png`.


## Bonus: Experimentiere mit eigenen Kostümen!

Jetzt, da du weißt, wie du Kostüme zuweist, kannst du kreativ werden:

* Erstelle eigene Bilder und speichere sie im images-Ordner.
* Ändere die Position und das Aussehen deiner Actors.

Versuche beispielsweise, einen Actor an einer neuen Position zu erstellen und ihm ein anderes Bild zuzuweisen:

```python
# Füge einen dritten Actor hinzu und gib ihm ein eigenes Kostüm
actor3 = Actor((200, 150))
actor3.add_costume("images/cow.png")  # Kostüm: "cow.png"

# Starte die Welt erneut
world.run()
``` 

## Zusammenfassung:

* Actors erhalten ein Kostüm durch die Methode add_costume().
* Die Bilder müssen im richtigen Ordner gespeichert sein, damit sie gefunden werden.
* Du kannst beliebig viele Actors mit unterschiedlichen Kostümen in der Welt platzieren und gestalten.


:::{admonition} FAQ

## FAQ: Häufige Probleme und Lösungen

### Mein Actor ist falsch ausgerichtet, was kann ich tun?

Wenn dein Actor in die falsche Richtung zeigt, gibt es zwei einfache Lösungen:

#### Problembeschreibung

#### Problem
```python
from miniworlds import World, Actor

world = World()
world.add_background("images/grass.jpg")
player = Actor((90,90))
player.add_costume("images/player_orientation_top.png")
player.direction = "right"

world.run()
```

```{figure} ../_images/tutorial_wrong_orientation1.png
  :scale: 50 %
  :alt: Ausrichtung des Actors
  
  Die Ausrichtung des Bildes ist nach oben gerichtet. 
  Miniworlds erwartet aber Bilder, die nach rechts ausgerichtet sind.
```

```{figure} ../_images/tutorial_wrong_orientation2.png
  :scale: 50 %
  :alt: Ausrichtung des Actors
  
  Daher schaut der Actor im Beispiel in die falsche Richtung
```

#### Lösung

1. **Bild drehen**: Du kannst das Bild in einem Bildbearbeitungsprogramm drehen, 
  sodass es in die gewünschte Richtung zeigt (normalerweise nach oben).

2. **Orientierung im Code anpassen**: Alternativ kannst du die Ausrichtung des Kostüms direkt 
  in Miniworlds ändern. Verwende dazu das Attribut `orientation`, um das Kostüm zu drehen:

   ```python
   my_actor.costume.orientation = 90  # Dreht das Kostüm um 90 Grad
   ```
   
Du kannst auch andere Werte wie -90 oder 180 verwenden, um die Ausrichtung anzupassen, je nachdem
wie dein Ursprungsbild ausgerichtet ist.

Das Beispiel oben könnte man wie folgt korrigieren:

```python
from miniworlds import World, Actor

world = World()
world.add_background("images/grass.jpg")
player = Actor((90,90))
player.add_costume("images/player_orientation_top.png")
player.direction = "right"
player.costume.orientation = -90 

world.run()
```

Erklärung:

* Das Bild ist von der erwarteten Position um -90° nach links gedreht. 
  Mit dieser Zusatzinformation wird das Bild nun korrekt ausgerichtet.

### Wie verhindere ich, dass sich das Kostüm mit dem Actor dreht?

Wie verhindere ich, dass sich das Kostüm mit dem Actor dreht?

Falls du möchtest, dass sich das Kostüm nicht dreht, selbst wenn sich der Actor bewegt oder rotiert, kannst du die Rotation des Kostüms deaktivieren. Setze dazu das Attribut is_rotatable auf False:

```python
my_actor.costume.is_rotatable = False  # Kostüm bleibt fest ausgerichtet
```

:::