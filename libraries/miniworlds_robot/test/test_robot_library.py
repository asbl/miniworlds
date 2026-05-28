import pytest

from miniworlds import Actor
from miniworlds_robot import Leaf, Loader, ObjectConfig, RobotConfig, WorldConfig, load_robot, load_world


def test_loader_creates_world_and_robot_with_restricted_default_api():
    world = load_world("basic")
    robot = load_robot("standard", world, position=(1, 1))

    robot.step()
    robot.turn_left()
    robot.turn_right()

    with pytest.raises(AttributeError):
        robot.position

    assert all(isinstance(actor, Actor) for actor in world.actors)


def test_world_config_can_expose_position():
    world = load_world("with_position")
    robot = load_robot("standard", world, position=(2, 3))

    assert robot.position == (2, 3)


def test_custom_world_config_controls_leaf_abilities():
    config = WorldConfig(
        name="leaf-world",
        robot_abilities=frozenset({"on_leaf", "remove_leaf"}),
    )
    world = Loader.load_world(config)
    robot = Loader.load_robot(RobotConfig(name="green", costume=(40, 160, 80, 255)), world, position=(1, 1))
    Leaf((1, 1), world=world)

    assert robot.on_leaf()
    assert robot.remove_leaf()
    assert not robot.on_leaf()


def test_loader_places_configured_world_objects():
    world = load_world(
        WorldConfig(
            name="configured-objects",
            objects=(
                ObjectConfig("tree", (1, 1)),
                ObjectConfig("mushroom", (2, 1)),
                ObjectConfig("leaf", (3, 1)),
            ),
        )
    )

    assert world.is_blocked((1, 1))
    assert world.is_blocked((2, 1))
    assert not world.is_blocked((3, 1))


def test_unknown_configs_raise_clear_errors():
    with pytest.raises(ValueError, match="Unknown RobotWorld config"):
        load_world("missing")

    with pytest.raises(ValueError, match="Unknown Robot config"):
        load_robot("missing")
