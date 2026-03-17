from unittest.mock import Mock, patch

from miniworlds.worlds.manager.mouse_manager import MouseManager


def test_get_position_returns_coordinates_for_active_world(mouse_world_builder):
    world = mouse_world_builder()
    manager = MouseManager(world)

    with patch("pygame.mouse.get_pos", return_value=(12, 34)):
        position = manager.get_position()

    assert position == (12, 34)
    world.app.worlds_manager.get_world_by_pixel.assert_called_once_with(12, 34)


def test_get_position_returns_none_for_other_world(mouse_world_builder):
    world = mouse_world_builder()
    world.app.worlds_manager.get_world_by_pixel.return_value = object()
    manager = MouseManager(world)

    with patch("pygame.mouse.get_pos", return_value=(7, 9)):
        position = manager.get_position()

    assert position is None


def test_update_positions_preserves_previous_mouse_position(mouse_world_builder):
    world = mouse_world_builder()
    manager = MouseManager(world)

    with patch.object(manager, "get_position", side_effect=[(1, 2), (3, 4)]):
        manager._update_positions()
        manager._update_positions()

    assert manager.last_position == (1, 2)
    assert manager.get_last_position() == (1, 2)


def test_x_and_y_return_zero_when_mouse_is_not_over_world(mouse_world_builder):
    world = mouse_world_builder()
    manager = MouseManager(world)

    with patch.object(manager, "get_position", return_value=None):
        assert manager.x() == 0
        assert manager.y() == 0


def test_x_and_y_return_coordinates_when_mouse_is_over_world(mouse_world_builder):
    world = mouse_world_builder()
    manager = MouseManager(world)

    with patch.object(manager, "get_position", return_value=(40, 50)):
        assert manager.x() == 40
        assert manager.y() == 50


def test_left_and_right_read_mouse_buttons(mouse_world_builder):
    world = mouse_world_builder()
    manager = MouseManager(world)

    with patch("pygame.mouse.get_pressed", return_value=(1, 0, 1)):
        assert manager.left() == 1
        assert manager.right() == 1
        assert manager.mouse_left_is_clicked() == 1
        assert manager.mouse_right_is_clicked() == 1


def test_is_mouse_pressed_and_side_specific_helpers_delegate_to_aliases(
    mouse_world_builder,
):
    world = mouse_world_builder()
    manager = MouseManager(world)

    with patch.object(manager, "mouse_left_is_clicked", return_value=False):
        with patch.object(manager, "mouse_right_is_clicked", return_value=True):
            assert manager.is_mouse_pressed() is True
            assert manager.is_mouse_left_pressed() is False
            assert manager.is_mouse_right_pressed() is True