"""Loops: repeat a pattern to walk around a square."""

from miniworlds_robot.tasks import task


world, robot = task("loop_square")

for _ in range(4):
    # TODO: Walk one side of the square and turn.
    pass

world.run()

