4.4.0.19
  * Fehler behoben (Browser/Pyodide): Programme mit `world.run(fullscreen=True)` blieben im Editor bzw. in der WebAssembly-Umsetzung hängen. SDL gibt im Pyodide-Worker bei `set_mode(..., pygame.SCALED)` nicht zurück. Browser-Programme verwenden jetzt die normale, weltgroße Canvas-Fläche; `fullscreen`, `fit_desktop` und `replit` bleiben dort ohne Wirkung, Vollbild bietet weiterhin die einbettende Seite an.
4.4.0.18
  * Performance für Pyodide und dichte Szenen: adaptives Neuzeichnen anhand sichtbarer Änderungen, wiederverwendete Fonts, bedarfsgesteuerte Audio-Initialisierung und bereinigte Transformations-Caches. Gemeinsame Skalierungs- und Rotationsergebnisse lassen sich mit begrenztem Speicherbudget optional wiederverwenden.
  * Neue optionale Funktionen für Survivors-artige Spiele: räumliche Rechteck-, Radius- und Nächster-Nachbar-Abfragen, Kollisionsgruppen, kameraunabhängige Kollisionen, getrennte Denk-/Bewegungs-/Animationsintervalle und `move_towards_fast()` ohne Richtungsänderung.
  * Neuer `ActorPool` für Pixelwelten: Actors behalten beim Wiederverwenden ihre Manager und Kostüme. Inaktive Actors verlassen Simulation, Zeichnung und räumliche Indizes; gebundene Timer werden bei Pool-Freigabe oder fehlgeschlagenem Reset entfernt.
  * Framebudget korrigiert: Ereignisverarbeitung, Aktualisierung aller Welten und vollständiges Zeichnen werden vor der gemeinsamen Wartephase berücksichtigt. Das bisherige framebasierte Bewegungs-, Timer-, Pause- und Einzelschrittverhalten bleibt erhalten.
  * Projektvalidator untersucht verschachtelte Dateien und Assets, überspringt Entwicklungsumgebungen und meldet Threads, blockierende Warteaufrufe und Endlosschleifen für den Webexport. Hinweise zu requests und SQLite präzisiert.
  * Regressionstests für Pool-Lebenszyklen, eigene Zeichengruppen, Kollisionsfilter, Rendering und Frame-Pacing sowie zusätzliche Pyodide-Performance-Grenzen ergänzt. Dokumentation und deutsche API-Übersetzungen erweitert; Thonny-Integrationstests liefern bei einem CI-Timeout Backend-Thread-Stacks.
4.4.0.17
  * Fehler behoben (`tools.api_index`): Reine Engine-Technik (`position_manager`, `costume_manager`, `sensor_manager`, `get_costume_class`, `get_world_connector`, `get_events`, `registered_events`, `dirty`, `rect`) taucht nicht mehr in Referenz und Autovervollständigung der Editoren auf. Die Namen bleiben in `hidden`, werden also weiter nicht als Tippfehler gemeldet.
4.4.0.16
  * Fehler behoben (`tools.api_index`): Alle Einträge zeigten als Hilfetext den Docstring von `str`; jetzt steht dort die erste Zeile der eigenen Dokumentation. Mitglieder aus internen Basisklassen (`register`, `remove`, `World.width`/`height` …) fehlten; sie werden jetzt bei der nächsten öffentlichen Klasse geführt. Je Klasse gibt es zusätzlich eine Liste `hidden` mit bekannten, aber nie vorgeschlagenen Namen.
  * Fehler behoben (`tools.code_hints`): Spalten sind jetzt UTF-16-Einheiten statt UTF-8-Bytes, sodass Umlaute oder Emojis vor einem Tippfehler die Markierung nicht mehr verschieben. Keine Hinweise mehr für Hooks, die nur Unterklassen definieren (Template-Methode), und für `@world.register`-Handler mit eigenem `self` innerhalb einer Methode.
4.4.0.15
  * Neues Modul `miniworlds.tools.code_hints`: `check(files)` findet typische Anfängerfehler aus dem Quelltext, ohne etwas auszuführen: nirgends definierte Namen (mit Vorschlag), `self.mov(2)` statt `self.move(2)`, vergessenes `self` vor einer Methode oder in `def act():`, ein Programm ohne `welt.run()`. Die Prüfung ist vorsichtig und schweigt bei Basisklassen, die sie nicht sehen kann, und bei Erweiterungspaketen (`miniworlds_*`).
  * Neues Modul `miniworlds.tools.api_index`: `build_index()` listet je öffentlicher Actor-/World-Klasse ihre Basisklasse sowie Methoden (mit Signatur) und Eigenschaften mit der ersten Docstring-Zeile, als Grundlage für Autovervollständigung.
  * `ScenarioHost`: neues Kommando `constructor` (Parameter von `__init__` nach der Position); `place` nimmt Konstruktorwerte entgegen (`place(Klasse, x, y, ["8", "'blau'"])`). `Scenario.place(cls, x, y, *args, **kwargs)` ruft `cls((x, y), *args, **kwargs)` auf.
4.4.0.14
  * Neues Modul `miniworlds.tools.class_model`: `analyze(files)` liefert aus Python-Quelltexten ein statisches Klassenmodell (Klassen mit Datei und Zeilen, Attribute, Methoden, Vererbung auch über Dateien hinweg bis zu den öffentlichen miniworlds-Klassen, Art Actor/World). Es wird nur mit `ast` gelesen, nichts wird ausgeführt; Dateien mit Syntaxfehlern werden gemeldet und übersprungen. Grundlage für ein UML-Klassendiagramm in Greenfoot-artigen IDEs.
  * `ScenarioHost`-Status liefert zusätzlich `by_class` (Anzahl Actors je Klassenname) für Live-Zähler.
  * Nachgetragen aus 4.4.0.13: `world.step(n)` führt eine pausierte Welt um genau n Frames weiter; `miniworlds.tools.Scenario`/`ScenarioHost` steuern Act/Run/Pause, Tempo, Platzieren, Verschieben, Löschen, Inspizieren und Methodenaufrufe für Greenfoot-artige IDEs; `actor.detect(Klasse)`, `world.contains_position/contains_rect/contains_rect_any`, Richtungsnamen (`"right"`) in `detect_all`/`detect_actor_at`/`detect_actors_at`/`detect_color_at`, `actor.last_position`, `TiledWorld.borders`, `world.has_background` und `world.remove_background()` funktionieren jetzt wie dokumentiert; die Ereignisse heißen `on_mouse_left_up`/`on_mouse_right_up` (die dokumentierten `..._released` gab es nie).
4.4.0.13
  * Neuer Parameter `world.run(video_driver="x11")` erzwingt einen SDL-Videotreiber (z. B. `"x11"` oder `"wayland"`), falls das Fenster unter Linux schwarz bleibt. Das entspricht dem Start mit `SDL_VIDEODRIVER=x11`, was weiterhin funktioniert. Ist der Treiber nicht verfügbar, bleibt der bisherige aktiv und es wird ein `RuntimeError` mit Hinweis ausgelöst; im Browser wird der Parameter ignoriert.
  * Fehler behoben: In einer HexWorld blieben Actors unsichtbar, deren Farbe über `actor.add_costume((r, g, b))` gesetzt wurde; sie werden jetzt als Sechseck in dieser Farbe gezeichnet. Actors ohne gesetzte Farbe bleiben wie bisher nur ein Rahmen. Regressionstest ergänzt.
4.4.0.12
  * Neue interne, optionale IDE-Anbindung (`miniworlds.base.runtime_host`): Ein installierter Host wird beim Start der App, in jedem Frame und beim Beenden benachrichtigt. In normalen Programmen ist kein Host installiert, Schülercode braucht keine zusätzlichen Aufrufe oder Importe.
  * Neues Thonny-Plugin `thonny-miniworlds` (unter `libraries/thonny-miniworlds`) mit Lernwerkzeugen, Objektlabor und Live-Ansicht; es nutzt die Experimentier-Schnittstelle aus 4.4.0.11 über einen lokalen, mit zufälligem Token gesicherten Kanal. Normales F5 führt das Programm wie bisher aus. Das Plugin hat ein eigenes CHANGELOG.
  * Dokumentation der Experimentier-Schnittstelle um die Thonny-Einbindung ergänzt; Tests für Plugin, Runtime-Host und Live-Verbindung.
4.4.0.11
  * Neue Experimentier-Schnittstelle für IDEs: `world.pause()`, `world.resume()`, `world.refresh()`, `world.invoke(callback, *args, **kwargs)` und `world.is_paused`. Eine pausierte Welt führt keine automatischen Aktionen, Kollisionen, Animationen, Timer und Spielereignisse aus (auch nicht vor dem ersten Frame); Fenster-Ereignisse bleiben aktiv, andere Welten laufen weiter. `refresh()` zeichnet den aktuellen Zustand ohne Simulationsschritt. `invoke()` ruft synchron auf, gibt den Rückgabewert zurück, bleibt auch nach Fehlern pausiert und stellt Änderungen vor einem Fehler dar; Coroutinen werden abgewiesen und der Aufruf muss im Thread der Hauptschleife erfolgen. `stop()` behält seine Semantik, `start()` beendet auch eine Experimentierpause.
  * Neue Klasse `ExperimentSession` (`from miniworlds import ExperimentSession`): Objektbank mit sitzungsgebundenen Handles (`register`, `resolve`, `describe`, `invoke`, `close`) und Erkennung veralteten Codes über `mark_source_changed`. Handles aus anderen oder beendeten Sitzungen sind ungültig.
  * Fehler behoben: Pause und Fehlerbehandlung in der Hauptschleife und in der Toolbar-Hauptschleife; Ereignisse für pausierte Welten werden verworfen statt später ausgeliefert.
  * Dokumentation (`api/experiment`, deutsch und englisch) und Tests ergänzt.
4.4.0.10
  * Fehler behoben (HexWorld): Mausereignisse liefern Fensterpixel, die Hex-Abfragen behandelten sie aber als Weltpixel. Bei gescrollter Kamera oder angedockter Welt wurde dadurch eine weit entfernte Kante oder Ecke ausgewählt. `get_tile_from_pixel`, `get_from_pixel`, `get_edge_from_pixel`, `get_corner_from_pixel`, `get_actors_from_pixel` und die Erkennung von Actors auf Ecken und Kanten rechnen Fensterpixel jetzt korrekt in Weltpixel um.
  * Fehler behoben (HexWorld): Klicks auf den Rand des Spielfelds ergaben `None`, obwohl die angeklickte Kante sichtbar war. Rundet ein Klick auf eine Position außerhalb der Welt, wird aus den angrenzenden Randfeldern gewählt, sodass Straßen und Siedlungen am Rand eines Catan-Spielfelds anklickbar bleiben. Abfragen außerhalb der Kamerasicht und außerhalb der Welt liefern weiterhin `None`.
  * Regressionstests für gescrollte Kameras, angedockte Fenster, Randklicks, Actor-Erkennung und die Mausereignis-Pipeline.
4.4.0.9
  * Kamera-Scrolling: Der statische Tile-Layer übernimmt den bereits kameralokalen Hintergrund ohne erneute Verschiebung. Dies verhindert leere Flächen und versetzte Hex-Raster, auch bei einer View größer als die Welt.
  * HexWorld: Sichtkandidaten für Tiles, Ecken und Kanten sowie der Rasteraufbau berücksichtigen die gescrollte Kamera; Weltaufbau und Pixelabfragen sind optimiert.
  * Cache-Invalidierung, Zeichenreihenfolge und gebündelte Hintergrundaktualisierungen für große Szenen verbessert; Regressionstests ergänzt.
4.4.0.8
  * Performance für große Welten (z. B. Survivors-like): Kamera-Sichtabfragen und Sensor-Queries in TiledWorlds laufen über den TiledSpatialIndex statt über alle Actors; der Kamera-View-Cache wird bei Actor-Bewegungen selektiv (O(1)) statt komplett invalidiert; get_global_rect ist in TiledWorlds pro Frame gecached; der statische Tile-Layer wird nur noch für sichtbare Actors neu gebaut; Background-Änderungen re-rendern nur Costumes von Actors in Sicht; Rotationen werden pro Direction gecached; Kollisions-Erkennung wird pro Actor und Frame nur einmal berechnet.
  * Fehler behoben: Statische Actors wurden in TiledWorlds beim Kamera-Scrolling im vorgebackenen Layer um bis zu `topleft_px - topleft_tiles` Pixel versetzt gerendert (Pixel-Rect vs. Tile-Koordinaten gemischt).
  * TiledWorld.detect_actors / world.actors_at nutzen den räumlichen Index statt eines Vollscans.
  * HexWorld: Bewegungsrichtungen werden auf die nächste Hex-Achse gerundet (nearest_axis_degrees), Nachbar-Tiles werden über eine versionsbasierte Cache-Invalidierung verwaltet, Hex-Kamera-Setter für width/height/topleft sind ergänzt; Doku der Hex-Manager-Klassen erweitert.
  * Neuer Benchmark "tiled camera culling" (Survivors-like-Szenario) in der world-Gruppe; Regressionstests für Kamera-Sicht, Cache-Invalidierung, Static-Layer-Positionierung und Kollisions-Caching.
4.4.0.6
  * HexWorld: Farbige Hex-Kostüme haben transparente Ecken statt pinker Rechteckflächen.
  * Neue Methode actor.point_towards(target) dreht die Figur zu einer Position oder einem anderen Actor, ohne sich zu bewegen (Pendant zu move_towards).
  * point_towards, move_towards und move_away lösen Ziel-Actors jetzt konsistent über dieselbe Position auf und akzeptieren Listen im Lernmodus wie set_position; zuvor ergaben point_towards und move_towards bei origin="topleft" unterschiedliche Richtungen und Listen wurden mit einer irreführenden "must be an Actor"-Meldung abgelehnt.
  * Blockierte Ziele in TiledWorld und HexWorld werden in Feldkoordinaten abgefragt und vor der Rechteckprüfung in Pixelkoordinaten umgerechnet.
  * Actor-Positionen auf Ecken und Kanten von HexWorld/TiledWorld (z. B. Siedlungen/Straßen in einem Catan-artigen Spiel) werden nach Kamera-Scrolling korrekt zentriert statt an der Sprite-Ecke ausgerichtet.
  * Kollisionsfilter verwenden die registrierten Figurenklassen der aktuellen Welt, auch nach einem Neustart mit gleichnamigen Klassen; die Namensauflösung ist zusätzlich deterministisch, sodass auch Filterabfragen vor der ersten Instanz einer neu definierten gleichnamigen Klasse die richtige Klasse treffen.
  * detect(actor) schließt die eigene Figur auch im schnellen Kollisionspfad aus, auch wenn eine Distanz als Keyword-Argument übergeben wird.
  * detect(actor, distance) liefert wieder den ersten gefundenen Actor statt einer Liste, wie es die Dokumentation verspricht.
  * Regressionstests für Selbstkollisionen, Hex-Kostüme, Nachbarabfragen und das Gegner-Ausweichmuster aus Project Moose, nativ und unter Pyodide.
3.1.0.2
  * Hotpath optimization: framebasierter Cache für statische Blocking-Rects reduziert Rect-Abfragen je Bewegungs-Tick
  * Robuste Edge-Case-Guards für ungültige Punkte und defekte Actor-Zustände in Sensor/Runtime-Pfaden
  * Cache-Invalidierung über _blocking_registry_version bei is_blocking/static-Änderungen
  * Neue Unit-Tests für Sensor-, Runtime- und Connector-Pfade
2.18.0.4
  * (Re-)added modifiers
2.18.0.3
  * Changed keyup event
2.18.0.2
  * fixed Key-Events
2.18.0.0
  * Removed Physics Engine from miniworlds, due to installing problems on windows clients.
