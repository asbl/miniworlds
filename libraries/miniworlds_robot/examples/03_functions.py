"""Functions: give repeated command groups a name."""

from miniworlds_robot.tasks import task


def turn_around(robot):
    # TODO: Turn around.
    pass


def walk_two_steps(robot):
    # TODO: Walk two steps.
    pass


world, robot = task("function_path")

walk_two_steps(robot)
turn_around(robot)
walk_two_steps(robot)

world.run()

