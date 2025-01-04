# Konzept: Importe

Mit import kannst du Bibliotheken importieren und die dort abgelegten Klassen und Funktionen verwenden. Es gibt unterschiedliche Arten, wie du Bibliotheken importieren kannst:

## Unterschiedliche Arten von Imports

Man kann in Python auf unterschiedliche Arten Bibliotheken importieren. 
Die folgenden 3 Anweisungen sind alle erlaubt:

``` python
import miniworlds
from miniworlds import *
import miniworlds 
```

Mit der hier verwendeten Version `import miniworlds` musst du jedesmal `miniworlds.objekt` schreiben, wenn du ein Objekt aus der miniworlds-Bibliothek importierst. Stattdessen kannst du auch `from miniworlds import *` schreiben - Dann kannst du miniworlds weglassen.

So sähe das erste Programm aus, wenn wir `import miniworlds` geschrieben hätten:

``` {code-block} python
---
lineno-start: 1
---
import miniworlds
world = miniworlds.TiledWorld()
world.add_background("images/soccer_green.jpg")
world.columns = 20
world.rows = 8
world.tile_size = 40

world.run()
```

## Explizite vs. Implizit.

Die Variante jedesmal `miniworlds.objekt` anstatt einfach nur `objekt` zu schreiben
mag zwar zuerst hässlicher erscheinen, weil man mehr Text schreiben muss.

Dies ist trotzdem in Python die bevorzugte Variante, da so erkennbar ist,
welche Objekte aus welcher Bibliothek importiert wurden. 

Es könnte ja z.B. sein, dass du in deinem Programm eine Klasse `TiledWorld` definierst
und damit zweimal der gleiche Name verwendet wird - Für Leser deines Programms wird es
dann schwierig nachzuvollziehen, worauf sich der Name TiledWorld bezieht.

Im Python-Zen gilt das Prinzip **explicit over implicit** - Dies bedeutet, dass oft mehr Code besser
ist, wenn dieser dadurch besser nachvollziehbar wird.

## Aliase

Die dritte Variante ist ein Kompromiss zwischen erster und zweiter Variante.
Wenn die der Name `miniworlds` zu lang ist, dann kannst du einen Alias definieren, z.B. `mwm`

Das Programm würde dann folgendermaßen aussehen:

``` {code-block} python
---
lineno-start: 1
---
import miniworlds 
world = miniworlds.TiledWorld()
world.add_background("images/soccer_green.jpg")
world.columns = 20
world.rows = 8
world.tile_size = 40

world.run()
```

## Hinweise für Lehrer

Es werden in diesen Tutorials beide Varianten verwendet. Als Lehrer sollte man sich aber entscheiden,
welche Variante man für den Einstieg bevorzugt.

Für Anfänger kann es hilfreich sein, auf diese Art von Importen zu verzichten.

