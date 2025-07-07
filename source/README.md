miniworlds
---------

miniworlds allows you to create 2D mini worlds and games. 

It is a 2D engine inspired by greenfoot and gamegrid based on pygame.

### Examples

Two actors that can be controlled with the keyworld.

```python
from miniworlds import World, Actor

world = World()
world.add_background("images/grass.jpg")
player = Actor((90,90))
player.add_costume("images/player.png")
player.costume.orientation = -90 
@player.register
def on_key_down_w(self):
    player.y = player.y - 1
   
player2 = Actor((180,180))
player2.add_costume("images/player.png")
player2.costume.orientation = -90 
@player2.register
def on_key_pressed_s(self):
    player2.y = player2.y - 1
    
world.run()
```

[Two Actors](examples_twoactors.png)