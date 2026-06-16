import ast
from pathlib import Path


SOURCE_ROOT = Path(__file__).parents[3] / "source"


def _runtime_imports(module_path: str) -> set[str]:
    source_path = SOURCE_ROOT / module_path
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    runtime_imports: set[str] = set()

    for node in tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            continue
        if isinstance(node, ast.Import):
            runtime_imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            runtime_imports.add(node.module)

    return runtime_imports


def test_position_manager_keeps_actor_and_world_as_type_only_imports():
    imports = _runtime_imports("miniworlds/worlds/manager/position_manager.py")

    assert "miniworlds.actors.actor" not in imports
    assert "miniworlds.worlds.world" not in imports


def test_world_connector_keeps_actor_and_world_as_type_only_imports():
    imports = _runtime_imports("miniworlds/worlds/manager/world_connector.py")

    assert "miniworlds.actors.actor" not in imports
    assert "miniworlds.worlds.world" not in imports


def test_event_focus_annotations_do_not_import_actor_at_runtime():
    imports = _runtime_imports("miniworlds/worlds/manager/event_manager.py")
    handler_imports = _runtime_imports("miniworlds/worlds/manager/event_handler.py")

    assert "miniworlds.actors.actor" not in imports
    assert "miniworlds.actors.actor" not in handler_imports


def test_event_registry_does_not_import_actor_or_world_roots_at_runtime():
    imports = _runtime_imports("miniworlds/worlds/manager/event_registry.py")

    assert "miniworlds.actors.actor" not in imports
    assert "miniworlds.worlds.world" not in imports


def test_world_initialization_keeps_actor_as_type_only_import():
    imports = _runtime_imports("miniworlds/worlds/world_initialization_facade.py")

    assert "miniworlds.actors.actor" not in imports
