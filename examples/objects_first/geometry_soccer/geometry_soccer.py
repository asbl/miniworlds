from miniworldmaker import *
board = PhysicsBoard(400,400)
board.gravity = (0, 0)
p1 = Token(100,100)
p1.physics.simulation = "manual"
p1.size = (40, 40)
p1.physics.density = 50

@p1.register
def on_key_pressed_space(self):
    print("space")
    
@p1.register
def on_key_pressed_w(self):
    self.move(2)
@p1.register
def on_key_pressed_a(self):
    self.turn_left(1)
@p1.register
def on_key_pressed_d(self):
    self.turn_right(1)
        
p2 = Circle(300,100)
p2.physics.density = 1
p2.elasticy = 20
board.run()