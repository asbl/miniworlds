# Timer

Mit **Timern** kannst du Ereignisse **zeitgesteuert** ausführen. 

Das bedeutet, dass eine Aktion nicht sofort, sondern mit einer Verzögerung von Millisekunden oder Sekunden 
gestartet wird. 

Timer sind nützlich, wenn du beispielsweise möchtest, dass eine Aktion erst nach einer bestimmten Zeit stattfindet.

:::{note}
Python bietet in der `time`-Bibliothek die Funktion `time.sleep(...)` an, um Verzögerungen zu erzeugen. 
Diese Methode solltest du jedoch **nicht** verwenden, da sie zu globalen Verzögerungen 
führt und unerwünschte Seiteneffekte verursachen kann.
:::

## Einen Timer starten

Um einen Timer zu starten, kannst du folgendes Beispiel verwenden:

```python
from miniworlds import ActionTimer
[...]
ActionTimer(24, player.move)
```

### Erklärung

1. Nach 24 Frames wird der Timer ausgelöst.
2. Die Methode `player.move` wird dann ausgeführt.

---

## Verschiedene Timer-Typen

Es gibt verschiedene Timer-Typen, die je nach Anwendungsfall genutzt werden können:

### ActionTimer

Der **ActionTimer** führt nach einer vorgegebenen Zeit eine Methode aus und entfernt sich danach automatisch. 
Er eignet sich für Aktionen, die einmalig nach einer Verzögerung ausgeführt werden sollen.

```python
ActionTimer(24, player.move, None)
```

In diesem Beispiel wird die Funktion `move` des Objekts `player` nach 24 Frames einmalig ausgeführt.

### LoopActionTimer

Der **LoopActionTimer** funktioniert ähnlich wie der ActionTimer, 
wiederholt jedoch die Aktion in regelmäßigen Abständen. Dieser Timer ist ideal für wiederkehrende Aktionen.

```python
LoopActionTimer(24, player.move)
```

In diesem Fall wird die Methode `move` des Objekts `player` alle 24 Frames ausgeführt.

Um einen LoopActionTimer zu stoppen, kannst du ihn wie folgt entfernen:

```python
loopactiontimer = LoopActionTimer(24, player.move)
...
loopactiontimer.unregister()  # Entfernt den LoopActionTimer
```

---

## Timer mit Events verknüpfen

Ähnlich wie bei Sensoren kannst du Timer so konfigurieren, dass Methoden auf bestimmte Timer-Ereignisse reagieren. 
Dazu registrierst du Methoden, die bei einem Timer-Ereignis ausgeführt werden sollen.

Ein Beispiel für eine solche Methode sieht wie folgt aus:

```python
@timer(frames=24)
def moving():
    player.move()
```

In diesem Fall wird die Methode `moving` nach 24 Frames aufgerufen und führt die Aktion `player.move()` aus.

Um einen **LoopTimer** zu registrieren, der regelmäßig ausgeführt wird, kannst du folgendes Beispiel verwenden:

```python
@loop(frames=48)
def moving():
    player.turn_left()
    player.move(2)
```

Hier wird die Methode `moving` alle 48 Frames wiederholt ausgeführt und lässt den Actor sich nach links drehen und bewegen.