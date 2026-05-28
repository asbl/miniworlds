"""Solution for conditions."""

from miniworlds_robot.tasks import task


def collect_leaf_if_present(robot):
    if robot.on_leaf():
        robot.remove_leaf()


world, robot = task("leaf_line")

for _ in range(6):
    collect_leaf_if_present(robot)
    robot.step()
collect_leaf_if_present(robot)

world.run()

