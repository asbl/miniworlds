import pytest

from test.unittests.support.builders import (
    make_collision_world,
    make_event_handler_world,
    make_event_registry,
    make_managed_world,
    make_mouse_world,
    make_worlds_manager_app,
)


@pytest.fixture
def collision_world_builder():
    return make_collision_world


@pytest.fixture
def event_handler_world_builder():
    return make_event_handler_world


@pytest.fixture
def event_registry_builder():
    return make_event_registry


@pytest.fixture
def managed_world_builder():
    return make_managed_world


@pytest.fixture
def mouse_world_builder():
    return make_mouse_world


@pytest.fixture
def worlds_manager_app_builder():
    return make_worlds_manager_app