# Events

## Mach dein Spiel interaktiv

In diesem Abschnitt erfährst du, wie du deinem Spiel Interaktivität verleihst, indem du auf Tastatur-Eingaben, Mausaktionen oder Kollisionen reagierst.

## Was sind Events?

**Events** (Ereignisse) sind der Schlüssel zu interaktiven Spielen. Sie ermöglichen es, auf Benutzeraktionen zu reagieren, wie Tastendrücke oder Mausbewegungen, und verändern dynamisch das Verhalten deiner Akteure.

- **`on_setup()`**: Wird am Anfang aufgerufen, um deine Welt zu initialisieren und vorzubereiten.
- **`act()`**: Diese Methode wird in jedem Frame aufgerufen und aktualisiert die Welt sowie die Akteure.
- Es gibt spezielle Event-Methoden wie **`on_key_pressed`**, **`on_mouse_left`** oder **`on_clicked_left`**, um auf verschiedene Benutzeraktionen zu reagieren.

## Events registrieren

Damit ein Akteur oder die Welt auf ein Event reagieren kann, musst du die entsprechende Methode registrieren. Die Registrierung funktioniert ähnlich wie bei der `act()`-Methode.

### Beispiel: Einfache Tasteneingabe

```python
@player.register  # Registriert die Methode als Event
def on_key_down_w(self):
    self.y -= 1  # Bewegt den Spieler nach oben
```

#### Erklärung:

Diese Methode wird ausgeführt, sobald die Taste <kbd>w</kbd> gedrückt wird. Der Akteur `player` bewegt sich dabei um einen Schritt nach oben.

## Beispiel: Steuerung mit mehreren Tasten

Im nächsten Beispiel wird ein Akteur über die Tasten <kbd>W</kbd>, <kbd>A</kbd>, <kbd>S</kbd> und <kbd>D</kbd> gesteuert.

```python
import miniworlds

world = miniworlds.TiledWorld()
world.columns = 20
world.rows = 8
world.tile_size = 42
world.add_background("images/soccer_green.jpg")

player = miniworlds.Actor()
player.add_costume("images/player_1.png")

@player.register
def on_key_down_w(self):
    self.y = self.y - 1  # Bewegt den Akteur nach oben

@player.register
def on_key_down_a(self):
    self.x = self.x - 1 # Bewegt den Actor nach links

@player.register
def on_key_down_d(self):
   self.x = self.x + 1  # Bewegt den Actor nach rechts

@player.register
def on_key_down_s(self):
    self.y = self.y + 1  # Bewegt den Actor nach unten

world.run()
```

#### Erklärung:

In diesem Beispiel wird der Akteur wie folgt gesteuert:

- <kbd>W</kbd>: Bewegt den Akteur nach oben.
- <kbd>A</kbd>: Bewegt den Akteur nach links.
- <kbd>D</kbd>: Bewegt den Akteur nach rechts.
- <kbd>S</kbd>: Bewegt den Akteur nach unten.

### Unterschied: `on_key_down` vs. `on_key_pressed`

Es gibt zwei Arten von Tastatur-Events, um auf Tasteninteraktionen zu reagieren:

- **`on_key_down(self, key)`**: Wird genau einmal aufgerufen, wenn eine Taste gedrückt wird.
- **`on_key_pressed(self, key)`**: Wird fortlaufend aufgerufen, solange die Taste gedrückt gehalten wird.

### Beispiel: Unterschiedliche Tastatur-Events

```python
import miniworlds 

world = miniworlds.World()
world.add_background("images/grass.jpg")

player = miniworlds.Actor((90, 90))
player.add_costume("images/player.png")
player.costume.orientation = -90 

@player.register
def on_key_down_w(self):
    self.y -= 1  # Bewegt den ersten Spieler nach oben

player2 = miniworlds.Actor((180, 180))
player2.add_costume("images/player.png")
player2.costume.orientation = -90 

@player2.register
def on_key_pressed_s(self):
    self.y -= 1  # Bewegt den zweiten Spieler nach unten, solange die Taste gedrückt ist
    
world.run()
```

```{note}
Du kannst entweder konkrete Tasten wie `on_key_down_b(self)` abfragen oder allgemeine Tastatur-Ereignisse mit `on_key_down(self, key)` verarbeiten, um alle Tastatureingaben zu erkennen.
```
