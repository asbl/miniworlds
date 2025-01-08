import miniworlds


class SelectorLabel(miniworlds.CounterLabel):
    def __init__(self, name):
        super().__init__(name)
        self.object = None
        self.color = (100,100,100)
        self.text.color = (180, 180, 180)

    def on_clicked_left(self, mouse_pos):
        for actor in self.world.actors:
            if isinstance(actor, SelectorLabel):
                actor.color = (100,100, 100)
                actor.text.color = (255, 255, 255)
        self.object.world.select_object(self.object)
        self.color = (0,100,200)
        self.text.color = (255, 255, 255)

class ObjectFactory:
    def __init__(self, world, name):
        self.saved_mouse_pos = None
        """ObjectFactory.saved_mouse_pos saved coordinates"""
        self.name = name
        self.selector_label = SelectorLabel(name)
        self.selector_label.set(1)
        self.max_objects = 1
        self.world = world
        self.dummy = None
        self.needs_two_clicks = True

    def on_click(self, mouse_pos):
        if (
            self.needs_two_clicks
            and not self.saved_mouse_pos
            and self.world.camera.is_in_screen(mouse_pos)
        ):
            # Save mouse pos
            self.saved_mouse_pos = mouse_pos
        elif (
            self.needs_two_clicks
            and self.valid_placement(mouse_pos)
            and self.world.camera.is_in_screen(mouse_pos)
        ):
            # Create object with two clicks
            self.create_object(self.saved_mouse_pos, mouse_pos)
            self.selector_label.sub(1)
        elif (
            not self.needs_two_clicks
            and self.valid_placement(mouse_pos)
            and self.world.camera.is_in_screen(mouse_pos)
        ):
            # Create object with one click
            self.saved_mouse_pos = mouse_pos
            self.create_object(self.saved_mouse_pos, mouse_pos)
            self.selector_label.sub(1)
        else:
            pass

    def create_dummy(self, saved_mouse_pos, mouse_pos):
        obj = self.create_actor(saved_mouse_pos, mouse_pos)
        obj.border_color = (200, 200, 200, 150)
        obj.color = (200, 200, 200, 150)
        obj.physics.simulation = None
        return obj

    def create_object(self, saved_mouse_pos, mouse_pos):
        if self.dummy:
            self.dummy.remove()
        actor = self.create_actor(saved_mouse_pos, mouse_pos)
        self.saved_mouse_pos = None
        return actor

    def valid_placement(self):
        pass

    def add_to_level(self, max_objects):
        self.selector_label.world = self.world.toolbar
        self.world.objects.append(self)
        self.max_objects = max_objects
        self.selector_label.set(self.max_objects)
        self.selector_label.object = self

    def on_motion(self, mouse_pos):
        if self.dummy:
            self.dummy.remove()
        if self.needs_two_clicks and self.saved_mouse_pos and self.valid_placement(mouse_pos):
            self.dummy = self.create_dummy(self.saved_mouse_pos, mouse_pos)
        elif not self.needs_two_clicks and self.valid_placement(mouse_pos):
            self.dummy = self.create_dummy(self.saved_mouse_pos, mouse_pos)


class LineFactory(ObjectFactory):

    def __init__(self, world, max_length):
        super().__init__(world, "Line")
        self.max_length = max_length

    def valid_placement(self, mouse_pos):
        return (
            self.saved_mouse_pos
            and self.world.distance_to(mouse_pos, self.saved_mouse_pos) < self.max_length
            and self.selector_label.get_value() >= 0
        )

    def create_actor(self, saved_mouse_pos, mouse_pos):
        return miniworlds.Line(self.saved_mouse_pos, mouse_pos)


class RectObjectFactory(ObjectFactory):

    def __init__(self, world, max_length):
        super().__init__(world, "Rectangle")
        self.max_length = max_length

    def create_actor(self, saved_mouse_pos, mouse_pos):
        return miniworlds.Rectangle(
            self.saved_mouse_pos, mouse_pos[0] - self.saved_mouse_pos[0], mouse_pos[1] - self.saved_mouse_pos[1], origin = "topleft"
        )

    def valid_placement(self, mouse_pos):
        return (
            self.saved_mouse_pos
            and self.world.distance_to(self.saved_mouse_pos, mouse_pos) < self.max_length
            and self.selector_label.get_value() > 0
            and mouse_pos[0] - self.saved_mouse_pos[0] > 0
            and mouse_pos[1] - self.saved_mouse_pos[1] > 0
        )


class PinJointFactory(ObjectFactory):

    def __init__(self, world, max_length, anchor):
        super().__init__(world, "Linked circle")
        self.max_length = max_length
        self.anchor = anchor
        self.needs_two_clicks = False

    def create_actor(self, saved_mouse_pos, mouse_pos):
        c = miniworlds.Circle(mouse_pos, 10)
        return c

    def create_object(self, saved_mouse_pos, mouse_pos):
        c = super().create_object(saved_mouse_pos, mouse_pos)
        c.physics.join(self.anchor)
        self.world.connect(c, self.anchor)

    def valid_placement(self, mouse_pos):
        return (
            self.world.distance_to(mouse_pos, self.anchor.position)
            and self.world.distance_to(mouse_pos, self.anchor.position) < 100
            and self.selector_label.get_value() > 0
        )


class Cloud(miniworlds.Actor):
    def __init__(self, position):
        super().__init__(position)

    def on_setup(self):
        self.size = 40
        self.physics.simulation = "manual"
        self.add_costume("images/cloud.png")
        self.costume.is_scaled = True
        self.center = self.position

    def on_touching_actor(self, other, info):
        other.impulse(0, 1500)


class CloudFactory(ObjectFactory):

    def __init__(self, world, max_length):
        super().__init__(world, "Cloud")
        self.max_length = max_length
        self.needs_two_clicks = False

    def create_actor(self, saved_mouse_pos, mouse_pos):
        t = Cloud(mouse_pos)
        return t

    def create_object(self, saved_mouse_pos, mouse_pos):
        return super().create_object(saved_mouse_pos, mouse_pos)

    def valid_placement(self, mouse_pos):
        return self.selector_label.get_value() > 0


class Trap(miniworlds.Actor):

    def __init__(self, position, trap):
        super().__init__(position)
        self.trap = trap
        self.size = 10
        self.color = (0, 0, 0)

    def on_setup(self):
        self.physics.simulation = None

    def on_detecting_actor(self, other):
        self.remove()
        self.trap.remove()


class Wheel:
    def __init__(self, position, size, count):
        for i in range(count):
            line = miniworlds.Line(
                (position[0], position[1] + size / 2),
                (position[0], position[1] - size / 2),
            )
            line.direction = 0 + ((180 / count) * i)
            line.border_color = (255, 255, 360 / count)

            @line.register
            def act(self):
                self.direction += 1


class Marble(miniworlds.Circle):
    def on_setup(self):
        self.color = (80, 160, 180)
        self.physics.elasticity = 0.2


class Base(miniworlds.Line):
    def on_setup(self):
        self.thickness = 1
