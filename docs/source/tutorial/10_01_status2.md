## Das Programm stoppen

Bei einem Spielende oder einem Levelwechsel gibt es oft bestimmte Aktionen, die durchgeführt werden müssen, 
wie z.B. das Spielfeld zurückzusetzen oder das Spiel zu pausieren. Dafür stehen folgende Befehle zur Verfügung:

- **`world.stop()`**: Stoppt das Spielfeld. Es werden keine weiteren Aktionen ausgeführt und keine Events mehr abgefragt.
- **`world.start()`**: Setzt einen vorherigen `stop`-Befehl zurück und lässt das Spiel weiterlaufen.
- **`world.is_running`**: Mit dieser Variable kannst du überprüfen, ob das Spielfeld gerade aktiv ist.
- **`world.clear()`**: Entfernt alle Figuren vom Spielfeld.
- **`world.reset()`**: Löscht das aktuelle Spielfeld und erstellt ein neues, indem alle Figuren wie in der Methode `world.on_setup()` definiert, neu erzeugt werden.

