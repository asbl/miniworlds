from miniworldmaker import *

board = Board(300, 200)

rect = Rectangle((280,120), 20, 80)
ball = Circle((20,50),20)
velocity = 1
@rect.register
def act(self):
    rect.x -= 1
    if rect.x == 0:
        rect.x = 280

@ball.register
def act(self):
    global velocity
    self.y += velocity
    if board.frame % 10 == 0:
        velocity += 1
    token = self.detect_token()
    if token == rect:
       self.board.stop()

@ball.register
def on_key_down(self, key):
    global velocity
    velocity = -2
board.run()