# Positionierung und Ausrichtung von Actors

In diesem Abschnitt lernst du, wie du Actors im Koordinatensystem positionieren und ausrichten kannst.

### Grundlagen

Zunächst eine kurze Wiederholung der wesentlichen Konzepte:

* Du kannst einen Actor an einer beliebigen Position erstellen:
  ```python
  actor = Actor((50, 120))  # erstellt einen Actor an der Position (50, 120)
  ```
* Das Koordinatensystem hat seinen Ursprung oben links:
  ```{figure} ../_images/tutorial_addactor_coord.png
  :scale: 30 %
  :alt: Das Koordinatensystem
  ```
* Die Position eines Actors bezieht sich immer auf dessen **Mittelpunkt** (auch Ursprung genannt).

---

## Position eines Actors nachträglich ändern

Du kannst die Position eines Actors auch nach dessen Erstellung anpassen, indem du die Attribute `x`, `y` oder `position?  änderst:

```python
my_actor.x = 120  # setzt die x-Koordinate auf 120
my_actor.y = 90   # setzt die y-Koordinate auf 90
my_actor.position = (120, 90) # setzt die Position auf x=120, y=90
```

---

## Ausrichtung des Actors ändern

Die Ausrichtung eines Actors lässt sich über das Attribut `direction` festlegen. D
ies ermöglicht es, den Actor in eine bestimmte Richtung zu drehen:


In der folgenden Darstellung siehst du, wie der Wert für `Direction` zu interpretieren ist.

```{figure} ../_images/movement.jpg
  :scale: 30 %
  :alt: Ausrichtung des Actors

  In der Darstellung siehst du die Bedeutung von `Direction`:
  * 0 up
  * 90 right | -90 left
  * 180 oder - 180 down
```

---

## Ursprung des Actors ändern

Du kannst den Ursprung (den Punkt, auf den sich die Position des Actors bezieht) ändern. Dies wird durch das Attribut `origin` festgelegt:

```python
a1 = Actor((0, 20))
a1.origin = "topleft"  # setzt den Ursprung auf die linke obere Ecke
```

```{figure} ../_images/pixel_coordinates.png
  :scale: 30 %
  :alt: Ausrichtung des Actors
  
  (0|20) bezeichnet jetzt die obere linke Koordinate des Actors.
```

---

Du kannst auch spezifisch das Zentrum oder die linke obere Ecke des Actors festlegen:

```python
a1 = miniworlds.Actor((0, 20))
a1.topleft = (20, 30)  # setzt die linke obere Ecke des Actors auf (20, 30)
a1.center = (20, 30)  # setzt das Zentrum des Actors auf (20, 30)
```

