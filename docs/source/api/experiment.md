# Experimentieren aus einer IDE

`World.pause()`, `World.invoke(callback, *args, **kwargs)`, `World.refresh()`
und `World.resume()` bilden die öffentliche Schnittstelle für interaktive
Objektaufrufe. `world.is_paused` zeigt den Experimentierzustand an.
Das bisherige `stop()` behält seine Semantik; `start()` beendet auch eine
Experimentierpause.

```python
from miniworlds import World, Actor, ExperimentSession

world = World(400, 300)
figur = Actor((50, 50))
world.pause()
world.refresh()
world.invoke(figur.move, 10)
# Rückgabewerte kommen direkt zurück, Fehler werden weitergereicht.
world.resume()
```

Pause hält auch Frame 0 an. Automatische Aktionen, Kollisionen, Animationen,
Timer und Spielereignisse werden nicht ausgeführt. Betriebssystemereignisse
wie Fenster schließen bleiben in der laufenden App aktiv. Ereignisse für
pausierte Welten werden verworfen, nicht für später gesammelt. Andere Welten
laufen weiter; für eine komplett pausierte Anwendung alle Welten pausieren.

`refresh()` zeichnet den aktuellen Zustand, ohne einen Simulationsschritt
auszuführen. `invoke()` pausiert vor dem Aufruf und bleibt auch nach Fehlern
pausiert. Änderungen vor einem Fehler bleiben erhalten und werden dargestellt.
Die Schnittstelle unterstützt synchrone Aufrufe; Coroutinen werden abgewiesen.

## Objektbank und Programmversion

```python
session = ExperimentSession(world, source_version="hash-des-geladenen-projekts")
handle = session.register(figur)
session.invoke(handle, "move", 10)

# Bei Änderungen im Editor, ohne Schülercode erneut auszuführen:
session.mark_source_changed("hash-des-geänderten-projekts")
status = session.describe(handle)
assert status["is_stale"]
# UI: „Code geändert – Laufzeit verwendet noch den vorherigen Stand“
```

Die geladene Version bleibt während der Sitzung unverändert. Der Host muss
Revisionen für alle relevanten Projektdateien bestimmen und Änderungen melden.
Alte Objekte bleiben mit ihrem bisherigen Code aufrufbar. Wird der Editorstand
wiederhergestellt, verschwindet die Abweichung.

Bei Backend-Ende `session.close()` aufrufen und die Objektbank im Frontend
leeren. Erst nach erfolgreichem Laden des neuen Programms eine neue Sitzung
mit neuer Quellversion anlegen. Jede Sitzung hat eine eigene Generation;
Handles aus einer anderen oder geschlossenen Sitzung sind ungültig. Ein neues
`ExperimentSession`-Objekt allein lädt keinen Programmcode neu.

## Einbindung in Thonny

Diese Schnittstelle gehört in den Ausführungsprozess. Die Oberfläche importiert
miniworlds nicht. IDE-Kommandos müssen auf dem Thread ausgeführt werden, auf dem
die Welt erzeugt wurde und die SDL-Hauptschleife läuft. `invoke()` prüft diesen
Thread. Auch `pause`, `resume` und `refresh` dort ausführen.

Der Desktop-Aufruf `world.run()` betreibt weiterhin seine eigene Hauptschleife.
Der Thonny-Adapter unter `libraries/thonny-miniworlds` installiert intern einen
Host, der Kommandos zwischen Frames verarbeitet. Ein expliziter Experimentierstart
über das Objektlabor aktiviert ihn; Schülercode benötigt keine zusätzlichen
Aufrufe oder Importe. Normales F5 führt das Programm wie bisher aus.

Die Oberfläche und der Ausführungsprozess tauschen Aufträge über einen lokalen,
mit einem zufälligen Token geschützten Kanal aus. Empfang und Ausführung sind
getrennt: Nur die Hauptschleife führt Objektoperationen aus. Jede Antwort enthält
Sitzungsgeneration und Auftragskennung. Stop/Restart beendet die Sitzung;
Editoränderungen markieren den Laufzeitstand als veraltet. Lange Schüleraufrufe
blockieren weiterhin den Ausführungsthread und lassen sich mit Thonnys
Stop/Restart abbrechen.
