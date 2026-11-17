"""Public sensor/containment API on a real world, without mocks.

Every documented argument shape is called once. These calls broke unnoticed
(``detect(Class)``, ``World.contains_position``, string directions) because the
older tests either mocked the collaborator or only used one argument shape.
"""
import pytest

from miniworlds import Actor, TiledWorld, World
from miniworlds.base.app import App


class Wall(Actor):
    pass


class Coin(Actor):
    pass


@pytest.fixture
def scene():
    App.reset(unittest=True, file=__file__)
    world = World(200, 200)
    player = Actor((100, 100), world=world)
    wall = Wall((115, 100), world=world)
    coin = Coin((100, 100), world=world)
    for actor in (player, wall, coin):
        actor.size = (20, 20)
    yield world, player, wall, coin
    App.reset(unittest=True, file=__file__)


@pytest.mark.unit
class TestDetectArgumentShapes:
    def test_detect_by_class_instance_name_and_keyword(self, scene):
        _, player, wall, coin = scene
        assert player.detect(Coin) is coin
        assert player.detect(coin) is coin
        assert player.detect("coin") is coin
        assert player.detect(filter=Coin) is coin
        assert player.detect(Wall) is wall
        assert player.detect() is not None

    def test_detect_class_without_collision_returns_none(self, scene):
        _, player, wall, coin = scene
        coin.remove()
        wall.remove()
        assert player.detect(Wall) is None
        assert player.detect(Coin) is None

    def test_detect_with_distance(self, scene):
        _, player, wall, _ = scene
        assert player.detect(Wall, 20, 90) is wall
        assert player.detect(Wall, 20, "right") is wall
        assert player.detect(Wall, 20, "left") is None

    def test_detect_all_shapes(self, scene):
        _, player, wall, coin = scene
        assert player.detect_all(Coin) == [coin]
        assert player.detect_all("coin") == [coin]
        assert player.detect_all(coin) == [coin]
        assert wall in player.detect_all()
        assert player.detect_all(Wall, direction=90, distance=20) == [wall]
        assert player.detect_all(Wall, direction="right", distance=20) == [wall]
        assert player.detect_all(Wall, direction="left", distance=20) == []

    @pytest.mark.parametrize("direction", [90, "right", "RIGHT"])
    def test_detect_actor_at_and_actors_at_accept_direction_names(self, scene, direction):
        _, player, wall, _ = scene
        assert player.detect_actor_at(direction, 20, Wall) is wall
        assert player.detect_actors_at(direction, 20, Wall) == [wall]
        assert player.detect_actor_at(direction, 20, Coin) is None

    def test_detect_color_at_accepts_direction_names(self, scene):
        world, player, _, _ = scene
        world.add_background((10, 20, 30))
        by_degrees = player.detect_color_at(90, 5)
        assert player.detect_color_at("right", 5) == by_degrees

    def test_last_position_is_the_previous_position(self, scene):
        _, player, _, _ = scene
        player.position = (50, 60)
        assert player.last_position == (100, 100)


@pytest.mark.unit
class TestWorldContainment:
    def test_contains_position(self, scene):
        world, *_ = scene
        assert world.contains_position((0, 0))
        assert world.contains((199, 199))
        assert not world.contains_position((200, 0))
        assert not world.contains_position((0, -1))

    def test_contains_rect_and_rect_any(self, scene):
        world, *_ = scene
        assert world.contains_rect((0, 0, 200, 200))
        assert not world.contains_rect((150, 150, 100, 100))
        assert world.contains_rect_any((150, 150, 100, 100))
        assert not world.contains_rect_any((200, 200, 10, 10))
        # a rectangle larger than the world still overlaps it
        assert world.contains_rect_any((-50, -50, 400, 400))

    def test_tiled_world_uses_tile_coordinates(self):
        App.reset(unittest=True, file=__file__)
        world = TiledWorld(10, 5)
        assert world.contains_position((9, 4))
        assert not world.contains_position((10, 4))
        assert world.borders((0, 0)) == ["left", "top"]
        assert world.borders((9, 4)) == ["bottom", "right"]
        assert world.borders((3, 2)) == []
        App.reset(unittest=True, file=__file__)


@pytest.mark.unit
class TestWorldBackground:
    def test_has_background_and_remove_without_argument(self, scene):
        world, *_ = scene
        world.add_background((1, 2, 3))
        world.add_background((4, 5, 6))
        assert world.has_background
        world.remove_background()  # removes the last one
        assert world.has_background
        world.remove_background(0)  # must not raise
