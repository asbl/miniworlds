"""Sequence: add commands in the right order."""

from miniworlds_robot.tasks import task


world, robot = task("sequence_path")

robot.step()
# TODO: Bring the robot to the target tile.

world.run()

