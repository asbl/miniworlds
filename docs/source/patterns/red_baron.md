# Tutorial: Roter Baron

In diesem Kapitel erstellen wir Schritt für Schritt einen Side-Scrolling-Shooter.

<video controls loop width=100%>
  <source src="../_static/red_baron.mp4" type="video/mp4">
  Dein Browser unterstützt das Video-Tag nicht.
</video>

Die Techniken zur Erstellung von Parallax-Hintergründen, der Verwaltung von Geschwindigkeit und Bewegung sowie das Generieren von Gegnern sind in Spielen weit verbreitet. Nachdem du sie hier gesehen hast, solltest du in der Lage sein, sie in deinen eigenen Projekten zu verwenden.

* **Basierend auf**: `https://github.com/kantel/pygamezero/tree/master/tappyplane`
* **Lizenz**: Attribution-NonCommercial-ShareAlike 4.0 International
* Voraussetzug: Kenntis im Umgang mit Klasse.
* 
## Schritt 1: Grundgerüst erstellen

Erstelle ein Grundgerüst: Du benötigst eine Welt, in der Akteure platziert werden können.

Deine letzte Zeile muss `world.run()` sein.

```python
from miniworlds import World, Actor, timer, Text
world = World(800, 480)

// dein Code hier

world.run()
```

## Ordner vorbereiten

Du musst Bilder für Hintergründe, Spieler und Gegner im Verzeichnis `images` innerhalb deines Code-Verzeichnisses ablegen.

```
my_code
|
|--images
|----planered1.png
|----background.png
|----groundgrass.png
|----shipbeige.png
|----shipblue.png
|----shipgreen.png
|----shippink.png
|----shipyellow.png
```

(Die Bilder findest du in diesem Repository: [miniworlds-cookbook - red baron](https://codeberg.org/a_siebel/miniworlds_cookbook/src/branch/main/classes_first/red_baron))

## Hintergründe erstellen

Mit dem folgenden Code kannst du zwei Hintergründe generieren, die einen **endlos scrollenden** Effekt erzeugen.

Erstelle zwei Hintergründe, die nebeneinander den gesamten Bildschirm füllen:

```python
back0 = Actor()
back0.add_costume("background")
back0.size = world.width, world.height
back1 = Actor(world.width, 0)
back1.size = world.width, world.height
back1.add_costume("background")
backs = [back0, back1]
```

Nun animieren wir die Hintergründe:

* Beide Hintergründe bewegen sich konstant von rechts nach links.
* Wenn ein Hintergrund den linken Bildschirmrand verlässt, wird er nach rechts verschoben.

```python
@world.register
def act(self):
    for back in backs:
        back.x -= 1
        if back.x <= -world.width:
            back.x = world.width
    for ground in grounds:
        ground.x -= 2
        if ground.x <= -world.width:
            ground.x = world.width
```

Dies erzeugt einen **endlos scrollenden** Hintergrund.

## Schritt 2: Flugzeug-Klasse erstellen

### Flugzeug-Klasse erstellen

Erstelle eine `Plane`-Klasse als Vorlage für deinen Spieler:

```python
class Plane(Actor):
    def on_setup(self):
        self.add_costume("planered1")
```

### Instanz der Flugzeug-Klasse erstellen

Erstelle am Ende deines Codes, vor `world.run()`, eine Instanz dieser Klasse:

```python
plane = Plane(100, world.height / 2)
```

### Physik hinzufügen

Nun fügen wir der Flugzeug-Klasse Physik hinzu. Modifiziere die `on_setup()`-Methode der Klasse:

```python
    def on_setup(self):
        self.add_costume("planered1")
        self.gravity = 0.1
        self.velocity_y = 0
```

* `velocity_y` beschreibt die aktuelle Geschwindigkeit des Flugzeugs in y-Richtung.
* `gravity` repräsentiert die Schwerkraft, die die Geschwindigkeit des Flugzeugs beeinflusst.

#### Physik simulieren

Die Physik wird in der `act()`-Methode der Klasse simuliert:

```python
    def act(self):
        self.velocity_y += self.gravity
        self.velocity_y *= 0.9  # Reibung
        self.y += self.velocity_y
```

Dies fügt die Geschwindigkeit zu den y-Koordinaten des Flugzeugs hinzu. Die Schwerkraft verringert die Geschwindigkeit kontinuierlich, während die Reibung die Bewegung glättet.

### Kraft bei Tastendruck hinzufügen

Verwende das `on_key_down`-Event, um eine Aufwärtskraft auf den Actor anzuwenden:

```python
    def on_key_down_w(self):
        self.velocity_y -= 5
```

## Schritt 3: Gegner hinzufügen

Importiere `randint` und `choice`, um zufällig Gegner zu generieren:

```python
from random import randint, choice
```

### Gegner-Klasse erstellen

Füge eine Gegner-Klasse als Vorlage hinzu:

```python
class Enemy(Actor):
    
    def on_setup(self):
        self.add_costume(choice(enemyships))

    def reset(self):
        self.x = randint(world.width + 50, world.width + 500)
        self.y = randint(25, world.height - 85)
```

Die Methode `reset()` setzt die Position des Gegners zufällig innerhalb eines bestimmten Bereichs.

### Gegner zur Welt hinzufügen

Erstelle mehrere Instanzen der Gegner-Klasse mit einer Schleife und füge sie der Welt hinzu:

```python
enemies = []
for _ in range(10):
    enemy = Enemy()
    enemy.reset()
    enemies.append(enemy)
```

### Gegner bewegen

Modifiziere die `on_setup()`-Methode der Gegner-Klasse:

```python
def on_setup(self):
    self.add_costume(choice(enemyships))
    self.speed = -1.5
```

Die `speed`-Eigenschaft gibt an, wie viele Schritte sich der Gegner in jeder Frame in x-Richtung bewegt.

Füge eine `act()`-Methode hinzu, um die Bewegung zu simulieren:

```python
def act(self):
    self.x += self.speed
    if self.x <= -self.width:
        self.reset()
```

## Schritt 4: Schießen hinzufügen

Erstelle eine `Bullet`-Klasse, um die Schussfunktion hinzuzufügen:

```python
class Bullet(Actor):
    def on_setup(self):
        self.add_costume("laserred")
        self.x = plane.x
        self.y = plane.y
        self.speed = 25
        self.fire = False
    
    def act(self):
        self.x += self.speed

    def on_detecting_enemy(self, enemy):
        enemy.reset()
        
    def on_detecting_not_on_world(self):
        self.remove()
```

Mit den Methoden `on_detecting_enemy` und `on_detecting_not_on_world` können Kugeln Gegner erkennen und bei Verlassen der Welt entfernt werden.

## Komplettcode:

```python
from miniworlds import World, Actor, timer, Text
from random import randint, choice

# based on https://github.com/kantel/pygamezero/tree/master/tappyplane


class RedBaronWorld(World):
    def on_setup(self):
        self.size = (800, 480)
        bottom_ground = self.height - 35
        nr_enemies = 10

        # Add backgrounds
        back0 = Actor(origin="topleft")
        back0.add_costume("background")
        back0.size = self.width, self.height
        back1 = Actor((self.width, 0), origin="topleft")
        back1.size = self.width, self.height
        back1.add_costume("background")
        self.backs = [back0, back1]

        ground0 = Actor((0, bottom_ground), origin="topleft")
        ground0.add_costume("groundgrass")
        ground0.width = self.width
        ground0.costume.is_scaled = True
        ground1 = Actor((self.width, bottom_ground), origin="topleft")
        ground1.add_costume("groundgrass")
        ground1.width = self.width
        ground1.costume.is_scaled = True
        self.grounds = [ground0, ground1]
        self.ground_level = self.height - 85
        self.plane = Plane((100, self.height / 2))

        enemies = []
        for _ in range(nr_enemies):
            enemy = Enemy()
            enemy.reset()
            enemies.append(enemy)

    def act(self):
        for back in self.backs:
            back.x -= 1
            if back.x <= -self.width:
                back.x = self.width
        for ground in self.grounds:
            ground.x -= 2
            if ground.x <= -self.width:
                ground.x = self.width
                
    def on_key_down_space(self):
        if not self.is_running:
            self.reset()
            self.run()


class Plane(Actor):
    def on_setup(self):
        self.add_costume("planered1")
        self.gravity = 0.1
        self.velocity_y = 0
        self.fire = False

    def act(self):
        self.velocity_y += self.gravity
        self.velocity_y *= 0.9  # friction
        self.y += self.velocity_y
        if self.y >= self.world.ground_level:
            self.y = self.world.ground_level
            self.velocity_y = 0
        if self.y <= 20:
            self.y = 20
            self.velocity_y = 0

    def on_key_down_w(self):
        self.velocity_y -= 5

    def on_key_down_d(self):
        if not self.fire:
            self.fire = True
            bullet = Bullet()

            @timer(frames=30)
            def downtime():
                self.fire = False

    def on_detecting_enemy(self, other):
        text = Text((self.world.width / 2, self.world.height / 2), "GAME OVER")
        text.color = (0, 0, 0)
        self.world.stop()


class Bullet(Actor):
    def on_setup(self):
        self.add_costume("laserred")
        self.x = self.world.plane.x
        self.y = self.world.plane.y
        self.speed = 25
        self.fire = False

    def act(self):
        self.x += self.speed

    def on_detecting_enemy(self, enemy):
        enemy.reset()

    def on_not_detecting_world(self):
        self.remove()


class Enemy(Actor):

    enemy_ships = ["shipbeige", "shipblue", "shipgreen", "shippink", "shipyellow"]

    def on_setup(self):
        self.add_costume(choice(self.enemy_ships))
        self.speed = -1.5

    def reset(self):
        self.x = randint(self.world.width + 50, self.world.width + 500)
        self.y = randint(25, self.world.ground_level)

    def act(self):
        self.x += self.speed
        if self.x <= -self.world.width:
            self.reset()


level1 = RedBaronWorld()
level1.run()
```