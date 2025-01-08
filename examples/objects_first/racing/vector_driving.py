from miniworlds import World, Actor, Vector, Rectangle, Text, Line, timer, CircleSensor

world = World()
obstacles = []

player = Actor((240,350),20, 40)
player.add_costume("car")
player.speed = 1
player.vector = Vector(1,0)
player.layer = 2
player.is_blockable = True

sensor = CircleSensor(player, distance  = 20)
sensor.layer = 3
sensor.visible = True # set to True, to show sensor
sensor.radius = 10
time = 0

tester = None # Test
def create_tile(position, type):
    global obstacles, tester
    tile = Actor(position)
    if type == "topleft":
        tile.add_costume("images/road-topleft.png")
        obstacles.append(Line((position[0]+ 100 ,position[1] +10),    (position[0]  + 40, position[1] + 30),))
        obstacles.append(Line((position[0] + 40, position[1]+30), (position[0]  + 30, position[1] + 40),))
        obstacles.append(Line((position[0] + 30, position[1]+40), (position[0]  + 20, position[1] + 50),))
        obstacles.append(Line((position[0] + 20, position[1]+50), (position[0]  + 10, position[1] + 100),))
        #inner
        obstacles.append(Line((position[0] + 90 ,   position[1]+100),    (position[0]  + 100, position[1] + 90),))
    elif type == "leftright":
        tile.add_costume("images/road-leftright.png")
        l1 = Line((position[0] + 0, position[1]+ 10),(position[0] + 100, position[1] + 10))
        obstacles.append(l1)
        obstacles.append(Line((position[0] + 0, position[1]+ 90),(position[0] + 100, position[1] + 90)))
    elif type == "topright":
        tile.add_costume("images/road-topright.png")
        obstacles.append(Line((position[0],   position[1] +10),    (position[0]  + 60, position[1] + 20),))
        obstacles.append(Line((position[0] + 60, position[1]+20), (position[0]  + 70, position[1] + 30),))
        obstacles.append(Line((position[0] + 70, position[1]+30), (position[0]  + 80, position[1] + 40),))
        obstacles.append(Line((position[0] + 80, position[1]+40), (position[0]  + 90, position[1] + 100),))
        #inner
        obstacles.append(Line((position[0] ,   position[1]+90),    (position[0]  + 10, position[1] + 100),))
    elif type == "topbottom":
        tile.add_costume("images/road-bottomtop.png")
        obstacles.append(Line((position[0] + 90, position[1]),(position[0] + 90,position[1] + 100)))
        obstacles.append(Line((position[0] + 10, position[1]),(position[0] + 10,position[1] + 100)))
    elif type == "bottomright":
        tile.add_costume("images/road-bottomright.png")
        # outer
        obstacles.append(Line((position[0] + 90, position[1]+0),    (position[0]  + 70, position[1] + 60),))
        obstacles.append(Line((position[0] + 70, position[1]+60), (position[0]  + 50, position[1] + 70),))
        obstacles.append(Line((position[0] + 50, position[1]+70), (position[0]  + 30, position[1] + 80),))
        obstacles.append(Line((position[0] + 30, position[1]+80), (position[0]  + 0, position[1] + 90),))
        #inner
        obstacles.append(Line((position[0] ,   position[1]+10),    (position[0]  + 10, position[1] + 0),))
    elif type == "bottomleft":
        tile.add_costume("images/road-bottomleft.png")
        #outer
        obstacles.append(Line((position[0]+10,   position[1]+0),    (position[0]  + 10, position[1] + 10),))
        obstacles.append(Line((position[0] + 10, position[1]+10), (position[0]  + 20, position[1] + 30),))
        obstacles.append(Line((position[0] + 20, position[1]+30), (position[0]  + 30, position[1] + 70),))
        obstacles.append(Line((position[0] + 30, position[1]+70), (position[0]  + 100, position[1] + 90),))
        #inner
        obstacles.append(Line((position[0]+90,   position[1]+0),    (position[0]  + 100, position[1] + 10),))
    tile.origin = "topleft"
    tile.size = (100,100)
    tile.costume.set_mode(mode="scale")
    for obstacle in obstacles:
        obstacle.is_blocking = True

create_tile((0,0), "topleft")
create_tile((100,0), "leftright")
create_tile((200,0), "leftright")
create_tile((300,0), "topright")
create_tile((300,100), "topbottom")
create_tile((300,200), "topbottom")
create_tile((300,300), "bottomright")
create_tile((200,300), "leftright")
create_tile((100,300), "leftright")
create_tile((0,300), "bottomleft")
create_tile((0,200), "topbottom")
create_tile((0,100), "topbottom")
# uncomment the following lines to show borders of track
#for obstacle in obstacles:
#    obstacle.visible = False


goal = Rectangle((160,310),20,80)
goal.origin = "topleft"
goal.color = (0,255,0, 200)
goal.border = 0

checkpoint = Rectangle((160,10),20,80)
checkpoint.origin = "topleft"
checkpoint.color = (0,255,255, 200)
checkpoint.border = 0

state = "start"

@player.register
def act(self):
    global tester
    self.direction = self.vector
    self.move_vector(self.vector)

@player.register
def on_key_pressed_a(self):
    self.vector.rotate(-1)

@player.register
def on_key_pressed_d(self):
    self.vector.rotate(1)

@player.register
def on_key_pressed_w(self):
    if self.vector.length() < 1:
        self.vector.normalize()
    self.vector.multiply(1.01)

@player.register
def on_key_pressed_s(self):
    self.vector.multiply(0.99)
    
@sensor.register
def on_detecting_actor(self, other):
    if other in obstacles:
        player.vector.multiply(0.2)
        self.watch_actor.undo_move()
    global checkpoint

@world.register
def act(self):
    global time
    time = time + 1
        

@player.register_sensor(checkpoint)
def check(self, checkpoint):
    global state, time
    if state == "start":
        state = "checkpoint"
        text = Text((200,200), f"Checkpoint at {round(time / self.world.fps,1)}")
        text.font_size = 12
        @timer(frames = 100)
        def remove():
            text.remove()

@player.register_sensor(goal)
def goal(self, goal):
    global state, time
    if state == "checkpoint":
        state = "start"
        text = Text((200,200), f"Checkpoint at {round(time / self.world.fps,1)}")
        text.font_size = 12
        @timer(frames = 100)
        def remove():
            text.remove()
        time = 0
    
world.run()