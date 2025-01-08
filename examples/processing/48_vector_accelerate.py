from miniworldmaker import *
board = Board()

mover = Circle()
mover.velocity = Vector(0, 0)
mover.topspeed = 10


@board.register
def act(self):
    mouse_vec = Vector(board.get_mouse_x(), board.get_mouse_y())
    location = Vector.from_token_position(mover)
    acceleration = mouse_vec - location
    acceleration.normalize().multiply(2)
    mover.velocity.add(acceleration)
    mover.velocity.limit(mover.topspeed)
    mover.move_vector(mover.velocity)
        
board.run()
