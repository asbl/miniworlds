from miniworldmaker import *
import random

board = Board(400, 200)
points = Number((0,0), 0)

red_circles = []
green_circles = []

@board.register
def act(self):
    if self.frame % 100 == 0:
        c = Circle((400, random.randint(0,200), 40))
        c.color = (255, 0, 0)
        red_circles.append(c)
    elif self.frame % 50 == 0:
        c = Circle((400, random.randint(0,200), 40))
        c.color = (0, 255, 0)
        green_circles.append(c)
    for circle in red_circles:
        circle.move_left()
    for circle in green_circles:
        circle.move_left()

@board.register
def on_mouse_left(self, mouse_position):
    tokens = self.get_tokens_at_position(mouse_position)
    for token in tokens:
        if token in red_circles:
            token.remove()
            points.set_number(points.get_number() - 1)
        elif token in green_circles:
            token.remove()
            points.set_number(points.get_number() + 1)
            
board.run()