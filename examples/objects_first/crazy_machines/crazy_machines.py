import miniworlds
import miniworlds_physics
import random

world = miniworlds_physics.PhysicsWorld(400, 400)
toolbar = world.add_right(miniworlds.Toolbar(), size=200)
lines_counter = toolbar.add_widget(miniworlds.CounterLabel("Lines"))

obj = "line"
state = None
line_dummy = None
max_length = 100

start = miniworlds.Circle((50, 50))
start.physics.simulation = None

end = miniworlds.Circle((250, 300))
end.physics.simulation = None


@end.register
def on_detecting_actor(self, other):
    print("sensing token")
    if other == start:
        world.is_running = False


@world.register
def on_key_down_space(self):
    actor = miniworlds.Circle(start.center)

    @actor.register
    def act(self):
        if self.y > 400:
            self.world.stop()
            miniworlds.Text((100, 100), "You loose!")

    @actor.register
    def on_detecting(self, other):
        if other == end:
            self.world.stop()
            miniworlds.Text((100, 100), "You won!")


@world.register
def on_mouse_left(self, mouse_pos):
    global state
    global obj
    if obj == "line" and not state:
        state = mouse_pos
    elif state and self.distance_to(state, mouse_pos) < 100 and lines_counter.get_value() < 3:
        # Add the Line
        line = miniworlds.Line(state, mouse_pos)
        state = None
        lines_counter.add(1)


@world.register
def on_mouse_motion(self, mouse_pos):
    global line_dummy
    if line_dummy:
        line_dummy.remove()
    if state and self.distance_to(state, mouse_pos) < 100 and lines_counter.get_value() < 3:
        line_dummy = miniworlds.Line(state, mouse_pos)
        line_dummy.border_color = (100, 100, 100, 100)


world.run()
