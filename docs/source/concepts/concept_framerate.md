## Konzept: Framerate


Man kann einstellen, wie oft `act()` aufgerufen wird, indem man die Attribute `world.fps` und `world.speed` konfiguriert.

* `world.fps` definiert die `frame rate`. Analog zu einem Daumenkino, bei dem du mit festgelegter Geschwindigkeit die Seiten umblätterst, 
  definiert die Framerate wie oft pro Sekunde das Bild neu gezeichnet wird.
  `world.fps` hat den Standardwert 60, d.h. es werden 60 Bilder pro Sekunde angezeigt.
  
* Im Attribut `world.frame` wird der aktuelle frame gespeichert. Die Frames seit Programmstart werden hochgezählt.
  
* `world.speed` definiert wie oft die Programmlogik (z.B. act) pro Sekunde aufgerufen wird. 
  Ein Wert von 60 bedeutet, dass die act()-Methode jeden 60. Frame aufgerufen wird.


``` python
  import miniworlds 

  world = miniworlds.World()
  world.size = (120,210)

  @world.register
  def on_setup(self):
      world.fps = 1
      world.speed = 3
      
  @world.register
  def act(self):
      print(world.frame)

  world.run()
```

Das Programm oben hat die Ausgabe:

```
  3
  6
  9
  12
  15
```

Es wird sehr langsam hochgezählt, weil genau ein Frame pro Sekunde abgespielt wird und jeden 3. Frame
(also alle 3 Sekunden) die Funktion `act()` aufgerufen wird.