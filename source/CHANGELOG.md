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
