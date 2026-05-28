"""Solution for loops."""

from miniworlds_robot.tasks import task


world, robot = task("loop_square")

for _ in range(4):
    robot.step()
    robot.step()
    robot.turn_right()

world.run()

