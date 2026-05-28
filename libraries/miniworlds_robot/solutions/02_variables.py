"""Solution for variables."""

from miniworlds_robot.tasks import task


world, robot = task("variables_path", robot="blue")

steps_to_wall = 4
turns_for_about_face = 2

for _ in range(steps_to_wall):
    robot.step()

for _ in range(turns_for_about_face):
    robot.turn_left()

robot.step()

world.run()

