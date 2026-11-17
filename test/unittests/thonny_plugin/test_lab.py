"""Exercise the IDE adapter against miniworlds' public experiment API."""

import importlib
import sys
from types import ModuleType

import pytest

from test.unittests.thonny_plugin.test_learning_tools import ROOT

package = ModuleType("_miniworlds_lab_tests")
package.__path__ = [str(ROOT / "libraries/thonny-miniworlds/thonnycontrib/miniworlds")]
sys.modules[package.__name__] = package
model = importlib.import_module(package.__name__ + ".lab_model")
runtime = importlib.import_module(package.__name__ + ".lab_runtime")
pytestmark = pytest.mark.unit

SOURCE = """from miniworlds import World, Actor
class Player(Actor):
    def advance(self, steps):
        self.x += steps
    def compare(self, other):
        return self is other
    def broken(self):
        self.x = 99
        raise ValueError("example")
world = World(200, 200)
player = Player((10, 10))
alias = player
world.run()
"""


@pytest.fixture
def lab(tmp_path):
    from miniworlds import App

    original = sys.modules["__main__"]
    filename = tmp_path / "main.py"
    filename.write_text(SOURCE)
    instance = None
    try:
        instance = runtime.Laboratory(SOURCE, filename, "v1")
        yield instance
    finally:
        if instance:
            instance.close(quit_display=False)
        sys.modules["__main__"] = original
        App.reset(unittest=True)


def player_row(lab):
    return next(r for r in lab.snapshot()["objects"] if "player" in r["aliases"])


def test_object_identity_methods_and_paused_state(lab):
    row = player_row(lab)
    assert "alias" in row["aliases"]
    assert any(m["name"] == "advance" and not m["inherited"] for m in row["methods"])
    assert any(m["name"] == "move" and m["inherited"] for m in row["methods"])
    frame = lab.worlds()[0].frame
    result = lab.command(
        {
            "action": "invoke",
            "handle": row["handle"],
            "method": "advance",
            "arguments": "20",
            "prediction": "x becomes 30",
        }
    )
    assert lab.namespace["player"].x == 30
    assert lab.worlds()[0].frame == frame and lab.worlds()[0].is_paused
    assert result["history"][-1]["prediction"] == "x becomes 30"
    result = lab.command(
        {
            "action": "invoke",
            "handle": row["handle"],
            "method": "compare",
            "arguments": "alias",
        }
    )
    assert result["history"][-1]["result"] == "True"


def test_card_previews_are_bounded_pngs_and_follow_costume_changes(lab):
    import base64
    import io

    from PIL import Image

    player = lab.namespace["player"]
    player.add_costume((255, 0, 0))
    lab.refresh()
    first = player_row(lab)["thumbnail"]
    assert first
    image = Image.open(io.BytesIO(base64.b64decode(first)))
    assert image.format == "PNG" and max(image.size) <= 48
    player.add_costume((0, 0, 255))
    player.switch_costume(1)
    lab.refresh()
    assert player_row(lab)["thumbnail"] != first
    assert all(
        row["thumbnail"] is None
        for row in lab.snapshot()["objects"]
        if row["type"] == "World"
    )


def test_source_versions_and_generation_invalidation(lab):
    row = player_row(lab)
    lab.command({"action": "revision", "version": "v2"})
    assert player_row(lab)["is_stale"]
    with pytest.raises(ValueError, match="neu laden"):
        lab.command(
            {
                "action": "invoke",
                "handle": row["handle"],
                "method": "advance",
                "arguments": "10",
            }
        )
    lab.command({"action": "revision", "version": "v1"})
    assert not player_row(lab)["is_stale"]
    session = lab.objects[row["handle"]][1]
    lab.close(quit_display=False)
    with pytest.raises(RuntimeError):
        session.resolve(row["handle"])


def test_constructor_and_error_preserve_changes(lab):
    lab.command(
        {
            "action": "create",
            "class": "Player",
            "name": "player2",
            "arguments": "(40, 50)",
        }
    )
    assert lab.namespace["player2"] is not lab.namespace["player"]
    row = player_row(lab)
    with pytest.raises(ValueError, match="example"):
        lab.command(
            {
                "action": "invoke",
                "handle": row["handle"],
                "method": "broken",
                "arguments": "",
            }
        )
    assert lab.namespace["player"].x == 99
    assert lab.worlds()[0].is_paused


def test_literal_parameters_and_reference_arguments():
    obj = object()
    args, kwargs = model.arguments("(1, 2), player, speed=3", {"player": obj})
    assert args == [(1, 2), obj] and kwargs == {"speed": 3}
    with pytest.raises(ValueError):
        model.arguments('__import__("os")', {})
    with pytest.raises(ValueError):
        model.arguments("*items", {})


def test_static_diagram_revision_and_replay(tmp_path):
    source = tmp_path / "main.py"
    source.write_text(SOURCE)
    helper = tmp_path / "helper.py"
    helper.write_text("value=1")
    old = model.revision(tmp_path, source, SOURCE)
    helper.write_text("value=2")
    assert model.revision(tmp_path, source, SOURCE) != old
    classes = model.classes_in(SOURCE)
    assert classes[0]["bases"] == ["Actor"] and classes[0]["name"] == "Player"
    exported = model.export_calls(SOURCE, ["player.advance(20)"])
    assert exported.index("player.advance(20)") < exported.index("world.run()")


def test_nested_reference_arguments_and_unsaved_helper_revision(tmp_path):
    obj = object()
    args, kwargs = model.arguments(
        '[player, {"other": player}], pair=(player, 2)', {"player": obj}
    )
    assert args == [[obj, {"other": obj}]] and kwargs["pair"] == (obj, 2)
    main = tmp_path / "main.py"
    helper = tmp_path / "helper.py"
    main.write_text("import helper")
    helper.write_text("x=1")
    saved = model.revision(tmp_path, main, main.read_text())
    assert saved != model.revision(
        tmp_path, main, main.read_text(), {str(helper): "x=2"}
    )


def test_failed_constructor_disables_replay_after_partial_changes(lab):
    exec(  # noqa: S102 -- controlled constructor failure fixture
        """class Broken(Actor):
    def __init__(self, position=(60, 60)):
        super().__init__(position)
        player.x = 70
        raise ValueError("constructor failed")
""",
        lab.namespace,
    )
    with pytest.raises(ValueError, match="constructor failed"):
        lab.command({"action": "create", "class": "Broken", "name": "broken"})
    assert lab.namespace["player"].x == 70
    assert lab.worlds()[0].is_paused
    assert not lab.snapshot()["replay_complete"]


def test_parameter_schema_and_form_arguments_support_defaults_and_references():
    def method(distance: int = 1, direction=None, label: str = "Spieler", other=None):
        pass

    schema = model.parameter_schema(method)
    refs = {"other_player": object()}
    values = {
        "distance": ("20", "value"),
        "direction": ("right", "value"),
        "label": ("Hallo Welt", "value"),
        "other": ("other_player", "object"),
    }
    code = model.form_arguments(schema, values, refs)
    args, kwargs = model.arguments(code, refs)
    assert args == [] and kwargs == {
        "distance": 20,
        "direction": "right",
        "label": "Hallo Welt",
        "other": refs["other_player"],
    }
    with pytest.raises(ValueError, match="Zahl"):
        model.form_arguments(schema, {"distance": ("Hallo", "value")}, refs)
    from miniworlds import Actor, World

    assert any(p["name"] == "position" for p in model.parameter_schema(Actor))
    assert any(p["name"] == "x" for p in model.parameter_schema(World))


def test_form_positional_only_optional_gaps_and_required_values():
    def method(a=1, b=2, /, *, required):
        pass

    schema = model.parameter_schema(method)
    code = model.form_arguments(
        schema, {"b": ("3", "value"), "required": ("True", "value")}, {}
    )
    assert code == "1, 3, required=True"
    with pytest.raises(ValueError, match="required"):
        model.form_arguments(schema, {}, {})
