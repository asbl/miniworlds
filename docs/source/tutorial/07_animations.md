# Kostüme und Animationen

Jeder Actor verfügt über ein oder mehrere Kostüme. 
Diese Kostüme bestehen aus mehreren Bildern, die für Animationen verwendet werden können.

:::{note}
Wenn du in der *API* nach den Attributen und Methoden der Klasse `Costume` suchst, 
findest du sie unter der Klasse `Appearance`. `Appearance` ist die Oberklasse von 
`Costume` und `Background`, da sich Hintergründe und Kostüme in vielen Eigenschaften ähneln.
:::

## Ein Kostüm hinzufügen

Mit der folgenden Funktion kannst du ein neues Kostüm zu einem Actor hinzufügen:

```python
self.add_costume("images/image.jpg")
```

Falls noch kein Kostüm vorhanden ist, wird dieses automatisch das erste Kostüm des Actors.

---

## Weitere Bilder zu einem Kostüm hinzufügen

Um ein Kostüm zu erweitern, kannst du mit der Methode `add_image` zusätzliche Bilder hinzufügen:

```python
self.costume.add_image("images/image_2.jpg")
```

Alternativ kannst du auch eine Liste von Bildern gleichzeitig hinzufügen:

```python
self.costume.add_images(["images/image_1.jpg", "images/image_2.jpg"])
```

---

## Animationen

2D-Animationen funktionieren ähnlich wie ein Daumenkino: 

Indem die Bilder eines Actors schnell hintereinander gewechselt werden, entsteht der Eindruck einer Bewegung.

![Kostüme für den Actor](../_images/costumes.png)

Um eine Animation zu erstellen, musst du zunächst mehrere Bilder zu einem Kostüm hinzufügen (siehe oben).

Dann kannst du die animation mit dem Befehl `costume.animate()` starten. Mit dem Parameter `loop` 
kannst du festlegen, ob die Animation
wiederholt werden soll:

``` python
my_actor.costume.animate()
robo.costume.animate(loop = True) # Endlossanimation
```

### Beispiel:

```python
import miniworlds 

world = miniworlds.World(80, 80)

robot = miniworlds.Actor()
robot.size = (80, 80)
robot.add_costume("images/drive1.png")
robot.costume.add_image("images/drive2.png")
robot.costume.animate()  # Animation aktivieren
robot.costume.loop = True         # Endlos-Schleife der Animation
world.run()
```

 <video controls loop width=300px>
  <source src="../_static/animation1.webm" type="video/webm">
  Your browser does not support the video tag.
</video> 

---

## Zwischen Kostümen wechseln

Um zwischen verschiedenen Kostümen zu wechseln, kannst du die Methode `switch_costume` verwenden:

```python
self.switch_costume()
```

Diese Methode wechselt zum nächsten Kostüm in der Liste. 
Du kannst optional auch eine Zahl als Parameter angeben, um direkt zu einem bestimmten Kostüm zu springen:

```python
self.switch_costume(1)  # Wechselt zum ersten Kostüm
```