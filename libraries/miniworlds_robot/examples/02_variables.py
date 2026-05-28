"""Variables: use names for values that control the route."""

from miniworlds_robot.tasks import task


world, robot = task("variables_path", robot="blue")

steps_to_wall = 0
turns_for_about_face = 0

for _ in range(steps_to_wall):
    robot.step()

for _ in range(turns_for_about_face):
    robot.turn_left()

# TODO: Complete the program.

world.run()

