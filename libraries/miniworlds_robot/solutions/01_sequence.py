"""Solution for sequence."""

from miniworlds_robot.tasks import task


world, robot = task("sequence_path")

robot.step()
robot.step()
robot.turn_right()
robot.step()
robot.turn_left()
robot.step()

world.run()

