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