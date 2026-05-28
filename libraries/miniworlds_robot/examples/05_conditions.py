"""Conditions: collect leaves only when the robot is on one."""

from miniworlds_robot.tasks import task


def collect_leaf_if_present(robot):
    # TODO: Use if robot.on_leaf().
    pass


world, robot = task("leaf_line")

for _ in range(6):
    collect_leaf_if_present(robot)
    robot.step()
collect_leaf_if_present(robot)

world.run()

