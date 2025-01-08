from miniworldmaker import *

board = Board()
player = Circle((200,200), 20)

flee = Circle((100,100),20)
flee.color = (0,255,0)
chaser = Circle((300,300),20)
chaser.color = (255,0,0)
chaser_speed = 1.1
flee_speed = 1.1

@player.register
def act(self):
    player.position = board.get_mouse_position()

@chaser.register
def act(self):
    v1 = Vector.from_tokens(player, chaser)
    v2 = - v1.normalize().multiply(chaser_speed)
    chaser.move_vector(v2)

@flee.register
def act(self):
    v1 = Vector.from_tokens(player, flee)
    if  v1.length() < 100:
        v1 = Vector.from_tokens(player, flee)
        v2 = v1.normalize().multiply(flee_speed)
        flee.move_vector(v2)
        
board.run()