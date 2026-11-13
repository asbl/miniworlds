# Audit der Änderungen seit v4.4.0.8

Geprüfter Bereich: d3b8ce6..1a0b850, insbesondere Kamera-Culling,
Zeichenreihenfolge, Cache-Invalidierung, Frame-Batching und Hex-Weltaufbau.

## Befund (behoben)

Der statische Tile-Layer verschob background.image erneut um die
Kameraposition. Die Hintergrund-Transformationen liefern jedoch bereits ein
kameragroßes Bild in lokalen Koordinaten. Beim Scrollen entstanden dadurch
leere Flächen und ein gegenüber den Actors versetztes Hex-Raster.

Der Layer übernimmt den Hintergrund jetzt bei (0, 0). Die Umrechnung der
Actor-Rechtecke bleibt erhalten. Das gilt auch bei einer View größer als die
Welt: Der Hintergrund füllt die View; Actors behalten ihren Weltbezug.

Ein neuer Pixelvergleich prüft den vollständigen Hex-Hintergrund bei drei
Kamerapositionen. Mit dem vorherigen Code schlagen beide gescrollten Fälle
fehl; mit dem Fix bestehen sie. Der bestehende Randfalltest und die
Brute-Force-Referenz wurden auf kameralokale Hintergründe korrigiert.
Die Screenshot-Referenzen des Hex-Scrolltests wurden visuell geprüft und
für die korrigierte Rasterposition erneuert.

## Validierung

- Vollständige Docker-Suite: zunächst 1243 bestanden, eine erwartete
  Abweichung im Hex-Scroll-Screenshot durch das korrigierte Raster.
- Pyodide/Chromium: 23 bestanden, 0 fehlgeschlagen.
- Abschließender vollständiger Docker-Lauf: 1244 bestanden,
  79 Subtests bestanden; keine Fehler.
- Dokumentations-/Übersetzungscheck: bestanden.

Der Dokumentationscheck fand außerdem fünf fehlende deutsche Übersetzungen
der neuen Positionsbereich-Abfrage. Diese wurden ergänzt und die betroffenen
Kataloge aktualisiert. Keine weiteren konkreten Befunde aus dem Diff-Review.
