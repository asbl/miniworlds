# Drag and Drop

Um ein Actor zu verschieben, müssen die Events `on_mouse_left` sowie `on_mouse_left_released` registriert werden.
Dann benötigt man eine Variable (z.B. `dragged`), in der man den Zustand speichert, d.h. ob ein Objekt gerade verschoben wird. 

 <video controls loop width=100%>
  <source src="../_static/draganddrop.webm" type="video/webm">
  Your browser does not support the video tag.
</video> 

* Wenn die Maus geklicked wird, dann wird der Zustannd der Variable `dragged`auf `True` gesetzt.
* Wenn die Maus losgelassen wird, dann wird das Actor nur dann verschoben, wenn `dragged` auf `True` gesetzt ist. Danach wird `dragged` wieder auf `False` gesetzt.

## Beispiele:

Kreise verschieben:

``` python
import miniworlds

world = miniworlds.World(200, 200)
circle = miniworlds.Circle((30, 30), 60)
circle.direction = 90
circle.dragged = False

@circle.register
def on_mouse_left(self, mouse_pos):
    if self.detect_point(mouse_pos):
        self.dragged = True
        
@circle.register
def on_mouse_left_released(self, mouse_pos):
    if self.dragged:
        self.dragged = False
        self.center = mouse_pos
        
world.run()
```

Drag and Drop auf einem TiledWorld:

``` python
import miniworlds 
world = miniworlds.TiledWorld()
t1 = miniworlds.Actor((0,0))
t2 = miniworlds.Actor((3,4))
t2.dragged = False

@t2.register
def on_mouse_left(self, mouse_pos):
    if self.detecting_point(mouse_pos):
        self.dragged = True
        print("start drag")
        
@t2.register
def on_mouse_left_released(self, mouse_pos):
    tile = mouse_pos
    if self.dragged:
        self.position = tile
    self.dragged = False
        
world.run()
```



