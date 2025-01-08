from miniworldmaker import *

board = Board()

player = Rectangle((200,350),20, 40)
player.acceleration = 0
player.velocity = 1
player.limit = 5
player.vector = Vector(1,0)
obstacles = []
obstacles.append(Rectangle.from_center((200,200),200,200))
obstacles.append(Rectangle((180,300),20,100))
goal = Rectangle((160,300),20,100)
goal.color = (0,255,0)

@player.register
def act(self):
    self.direction = self.vector
    self.vector.limit(5)
    self.move_vector(self.vector)

@player.register
def on_key_pressed_a(self):
    self.vector.rotate(-5)

@player.register
def on_key_pressed_d(self):
    self.vector.rotate(5)

@player.register
def on_key_pressed_w(self):
    self.speed += 0.01
    self.vector.multiply(self.speed)

@player.register
def on_key_pressed_s(self):
    self.speed -= 0.01
    self.vector.multiply(self.speed)
    
@player.register
def on_detecting_token(self, other):
    if other in obstacles:
        Text((50,50), "Kaboom!")
        self.board.stop()
    if other == goal:
        Text((50,50), f"Success! Time: {self.board.frame}")
        self.board.stop()
        
@player.register
def on_not_detecting_board(self):
    Text((50,50), "Kaboom!")
    self.board.stop()
    
board.run()