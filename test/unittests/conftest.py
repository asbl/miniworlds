import pytest

from test.unittests.support.builders import (
    helper_make_collision_world,
    helper_make_event_handler_world,
    helper_make_event_registry,
    helper_make_managed_world,
    helper_make_mouse_world,
    helper_make_worlds_manager_app,
)


@pytest.fixture
def collision_world_builder():
    return helper_make_collision_world


@pytest.fixture
def event_handler_world_builder():
    return helper_make_event_handler_world


@pytest.fixture
def event_registry_builder():
    return helper_make_event_registry


@pytest.fixture
def managed_world_builder():
    return helper_make_managed_world


@pytest.fixture
def mouse_world_builder():
    return helper_make_mouse_world


@pytest.fixture
def worlds_manager_app_builder():
    return helper_make_worlds_manager_app
