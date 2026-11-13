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
