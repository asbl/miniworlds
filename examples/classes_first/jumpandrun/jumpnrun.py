import miniworlds
import miniworlds_physics
import math



class Level1(miniworlds_physics.PhysicsWorld):
    def on_setup(self):
        self.size = (400,400)
        self.camera.world_size = (1200, 400)
        self.debug = False

class Player(miniworlds.Actor):
    def on_setup(self):
        self.direction = "right"
        self.size = (80, 80)
        self.orientation = -90
        self.physics.size = (0.8, 0.8)
        self.physics.density = 1
        self.physics.max_velocity_x = 200  # don't run faster than this
        self.physics.friction = 0.7
        self.moment = math.inf  # do not rotate
        self.sensor = miniworlds.Sensor(self, positioning = "absolute", direction=180, distance = 40)
        self.sensor.size = (40, 20)
        self.sensor.visible = True
        self.standing_costume = self.add_costume("images/alien_stand.png")
        self.walking_costume = self.add_costume(
            ["images/alien_walk1.png", "images/alien_walk2.png"]
        )
        self.jumping_costume = self.add_costume("images/alien_jump.png")
        self.old_velocity_x = 0
        self.was_standing = False
        self.was_jumping = False
        self.was_walking = False
        

    def on_key_pressed_d(self):
        self.physics.force_in_direction(90, 1000)

    def on_key_pressed_a(self):
        self.physics.force_in_direction(-90, 1000)

    
    def on_key_down_w(self):
        if self.sensor.detect():
            self.physics.force_in_direction(0, 15000)
    
    def act(self):
        self.world.camera.from_actor(self)
        changed_state = False
        # select costume
        if self.started_standing():
            self.start_standing()
            changed_state = True
        elif self.started_walking():
            self.start_walking()
            changed_state = True
        elif self.started_jumping():
            self.start_jumping()
            changed_state = True
        if changed_state or not self.is_standing():
            if self.physics.velocity_x < 1:
                self.is_flipped = True
            else:
                self.is_flipped = False
        # safe current state for next act
        self.old_velocity_x = self.physics.velocity_x
        self.was_jumping = self.is_jumping()
        self.was_standing = self.is_standing()
        self.was_walking = self.is_walking()
        
    def is_standing(self):
        return abs(self.physics.velocity_x) < 5 and self.sensor.detect()

    def is_walking(self):
        return abs(self.physics.velocity_x) > 5 and self.sensor.detect()

    def is_jumping(self):
        return not self.sensor.detect()

    def started_jumping(self):
        return (not self.was_jumping) and self.is_jumping()

    def started_standing(self):
        return (not self.was_standing) and self.is_standing()

    def started_walking(self):
        return (not self.was_walking) and self.is_walking()

    def has_changed_direction(self):
        if self.old_velocity_x >= -5 and self.physics.velocity_x < 0:
            return True
        elif self.old_velocity_x <= 5 and self.physics.velocity_x > 0:
            return True
        else:
            return False

    def start_standing(self):
        self.switch_costume(self.standing_costume)
        self.costume.is_rotatable = False

    def start_walking(self):
        self.switch_costume(self.walking_costume)
        self.costume.is_rotatable = False
        self.costume.animate(loop=True)

    def start_jumping(self):
        self.switch_costume(self.jumping_costume)
        self.costume.is_rotatable = False
       
level = Level1() 

c = miniworlds.Rectangle((0, 300), 400, 4)
c.physics.simulation = "manual"
c2 = miniworlds.Rectangle((400, 360), 400, 4)
c2.direction = 10
c2.physics.simulation = "manual"
c2.friction = 1

c3 = miniworlds.Rectangle((400, 220), 80, 4)
c3.direction = 10
c3.physics.simulation = "manual"

p = Player((20, 20))
level.run()
