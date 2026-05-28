"""Solution for functions."""

from miniworlds_robot.tasks import task


def turn_around(robot):
    robot.turn_left()
    robot.turn_left()


def walk_two_steps(robot):
    robot.step()
    robot.step()


world, robot = task("function_path")

walk_two_steps(robot)
turn_around(robot)
walk_two_steps(robot)

world.run()

