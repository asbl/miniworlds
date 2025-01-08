import miniworlds
import miniworlds_physics
from objects import (
    Base,
    Marble,
    CloudFactory,
    LineFactory,
    PinJointFactory,
    RectObjectFactory,
    Wheel,
)


class LevelBase(miniworlds_physics.PhysicsWorld):
    def __init__(self, level_manager):
        super().__init__()
        self.level_manager = level_manager
        self.selected_object = None
        self.objects = []
        self.rows = 400
        self.columns = 400
        self.start_marker = None
        self.timer = None
        self.end_marker = None
        self.status = "waiting"  # "waiting", "started", "won", "lost"

    def on_setup(self):
        print("setup level")
        self.window.reset()
        self.status = "waiting"  # "waiting", "started", "won", "lost"
        self.timer = miniworlds.Number((10, 10))
        self.timer.physics.simulation = None
        self.timer.set_value(10)
        toolbar = miniworlds.Toolbar()
        self.toolbar = self.add_right(toolbar, size=200)
        self.start_marker = miniworlds.Circle((-100, -100))
        self.start_marker.color = (100, 200, 200)
        self.start_marker.physics.simulation = None
        self.end_marker = miniworlds.Circle((-100, -100))
        self.end_marker.color = (0, 200, 0)
        self.end_marker.physics.simulation = None
        self.number = ((0, 10), 100)

        @self.end_marker.register
        def on_detecting_actor(self, other):
            if isinstance(other, Marble):
                self.world.win()

    def on_key_down_space(self):
        if self.is_running and self.status == "waiting":
            self.status = "started"
            actor = Marble(self.start_marker.center)

            @actor.register
            def act(self):
                if self.y > 400:
                    self.world.loose()

        elif self.status == "won":
            self.level_manager.next_level()
        elif self.status == "lost":
            self.level_manager.same_level()

    def on_mouse_left(self, mouse_pos):
        if self.selected_object:
            self.selected_object.on_click(mouse_pos)

    def on_mouse_motion(self, mouse_pos):
        if self.selected_object:
            self.selected_object.on_motion(mouse_pos)

    def act(self):
        """If status is started, countdown timer to zero.
        If counter value is zero, the level is lost.
        """
        if self.status == "started" and self.frame % 60 == 0:
            self.timer.sub(1)
            if self.timer.get_value() == 0:
                self.loose()

    def win(self):
        self.stop()
        t = miniworlds.Text((100, 100), "You won!")
        t.physics.simulation = None
        self.status = "won"

    def loose(self):
        self.stop()
        t = miniworlds.Text((100, 100), "You lost!")
        t.physics.simulation = None
        self.status = "lost"

    def select_object(self, selected):
        self.selected_object = selected
        for obj in self.objects:
            obj.selector_label.background_color = (150, 150, 150)
        selected.selector_label.background_color = (255, 0, 0)
        self.selected_object.saved_mouse_pos = None


class Level1(LevelBase):
    def on_setup(self):
        print("setup Level")
        super().on_setup()
        line_factory = LineFactory(self, 100)
        line_factory.add_to_level(3)
        self.selected_object = line_factory
        self.start_marker.center = (100, 100)
        self.end_marker.center = (200, 200)
        print("setup world")


class Level2(LevelBase):
    def on_setup(self):
        print("setup Level 2")
        super().on_setup()
        line_factory = LineFactory(self, 100)
        line_factory.add_to_level(3)
        miniworlds.Line((50, 150), (300, 175))
        self.selected_object = line_factory
        self.start_marker.center = (100, 100)
        self.end_marker.center = (200, 200)
        print("setup world", self.backgrounds)


class Level3(LevelBase):
    def on_setup(self):
        print("setup Level 3")
        super().on_setup()
        rect_factory = RectObjectFactory(self, 100)
        rect_factory.add_to_level(3)
        miniworlds.Line((50, 150), (300, 175))
        miniworlds.Line((50, 210), (380, 210))
        self.selected_object = rect_factory
        self.start_marker.center = (100, 100)
        self.end_marker.center = (200, 200)
        print("setup world", self.backgrounds)


class Level4(LevelBase):
    def on_setup(self):
        print("setup Level 3")
        super().on_setup()
        c = miniworlds.Circle((20, 50), 10)
        p = miniworlds.Point((100, 100))
        p.physics.simulation = None
        miniworlds.Line((50, 210), (380, 210))
        c.physics.join(p)
        self.connect(c, p)
        self.selected_object = None
        self.start_marker.center = (100, 100)
        self.end_marker.center = (200, 200)
        print("setup world", self.backgrounds)


class Level5(LevelBase):
    def on_setup(self):
        print("setup Level 3")
        super().on_setup()
        c = miniworlds.Circle((300, 100), 10)
        pin_joint_factory = PinJointFactory(self, 100, c)
        c.physics.simulation = None
        pin_joint_factory.add_to_level(1)
        miniworlds.Line((50, 120), (190, 150))
        miniworlds.Line((150, 190), (400, 190))
        self.selected_object = pin_joint_factory
        self.start_marker.center = (100, 100)
        self.end_marker.center = (200, 180)
        print("setup world", self.backgrounds)


class Level6(LevelBase):
    def on_setup(self):
        print("setup Level 3")
        super().on_setup()
        cloud_factory = CloudFactory(self, 100)
        cloud_factory.add_to_level(1)
        self.selected_object = cloud_factory
        self.start_marker.center = (100, 100)
        miniworlds.Line((50, 90), (150, 150))
        self.end_marker.center = (350, 280)
        print("setup world", self.backgrounds)


class Level7(LevelBase):
    def on_setup(self):
        print("setup Level 3")
        super().on_setup()
        line_obj = LineFactory(self, 100)
        line_obj.add_to_level(1)
        self.selected_object = line_obj
        self.start_marker.center = (50, 50)
        miniworlds.Line((30, 85), (120, 120))
        self.end_marker.center = (350, 350)
        print("setup world", self.backgrounds)
        p = miniworlds.Point((120, 120))
        p.physics.simulation = None
        line = miniworlds.Line((120, 120), (160, 120))
        c = Marble((130, 100))
        c.physics.density = 0.5
        r = miniworlds.Rectangle((280, 100), 10, 10)
        r.physics.density = 0.1
        miniworlds.Line((180, 360), (370, 360))


class Level8(LevelBase):
    def on_setup(self):
        print("setup Level 3")
        super().on_setup()
        line_factory = LineFactory(self, 40)
        line_factory.add_to_level(3)
        self.selected_object = line_factory
        self.start_marker.center = (200, 200)
        miniworlds.Line((180, 180), (180, 300))
        miniworlds.Line((300, 260), (400, 260))
        self.end_marker.center = (350, 250)
        c = Marble((300, 250))


class LevelFelix1(LevelBase):
    def on_setup(self):
        super().on_setup()
        self.start_marker.center = (290, 150)
        miniworlds.Line((280, 160), (10, 50))
        miniworlds.Line((280, 160), (380, 160))
        self.end_marker.center = (20, 0)
        c = miniworlds.Circle((290, 50), 10)
        c.physics.simulation = None
        pinjoin_obj = PinJointFactory(self, 100, c)
        pinjoin_obj.add_to_level(1)


class LevelBruno1(LevelBase):
    def on_setup(self):
        super().on_setup()
        self.start_marker.center = (50, 50)
        # Obstacles
        Base((40, 60), (100, 100))
        Base((100, 100), (140, 100))
        Base((160, 120), (190, 145))
        Base((200, 200), (240, 155))
        Base((160, 240), (200, 240))
        Base((160, 365), (320, 350))
        r = miniworlds.Rectangle((120, 80), 20, 20, origin="topleft")
        r.physics.density = 0.9
        r.physics.elasticity = 0.1
        c = miniworlds.Circle((120, 5))
        c.physics.simulation = None
        # Objects
        pin_joint_factory = PinJointFactory(self, 75, c)
        pin_joint_factory.add_to_level(1)
        rect_factory = RectObjectFactory(self, 50)
        rect_factory.add_to_level(2)
        w = Wheel((240, 280), 70, 3)
        self.end_marker.center = (200, 350)

class LevelEnd(LevelBase):
    def on_setup(self):
        super().on_setup()
        self.win()
