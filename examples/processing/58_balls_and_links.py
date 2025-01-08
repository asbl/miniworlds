from random import uniform
from miniworldmaker import *

class Ball(Circle):
    
    def on_setup(self):
        self.max_w = self.board.width
        self.max_h = self.board.height
        self.position = uniform(5, self.max_w-5), uniform(5, self.max_h -5)
        self.speed = Vector(uniform(-2, 2), uniform(-2,2));

    def act(self):
        self.position = self.position + self.speed
        if self.x < 5 or self.x > self.max_w - 5:
            self.speed.x = - self.speed.x
        if self.y < 5 or self.y > self.max_h - 5:
            self.speed.y = - self.speed.y

class Connector(Line):
    
    def __init__(self, b1, b2):
        super().__init__((0,0),(1,1))
        self.b1 = b1
        self.b2 = b2
    
    def act(self):
        self.start_position = self.b1.center
        self.end_position = self.b2.center
        
board = Board(100, 100)
balls = []
for i in range(5):
    balls.append(Ball())

c = Connector(balls[0], balls[1])
board.run()