"""Engine-independent tests of teaching content and project/media safety."""

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "miniworlds_plugin_core",
    ROOT / "libraries/thonny-miniworlds/thonnycontrib/miniworlds/core.py",
)
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)
pytestmark = pytest.mark.unit


@pytest.mark.parametrize("mode", core.MODES)
@pytest.mark.parametrize("kind", ["Pixelwelt", "Kachelwelt"])
@pytest.mark.parametrize("example", ["Grundgerüst", "Bewegung", "Tastatur", "Maus"])
def test_generated_projects(mode, kind, example):
    code = core.project_code(mode, kind, example)
    ast.parse(code)
    assert core.check_code(code, mode=mode) == []
    assert ("@player.register" in code) == (mode == "E2" and example != "Grundgerüst")
    assert ("class Player" in code) == (mode == "Q1")


def test_project_creation_never_overwrites(tmp_path):
    main = core.create_project(tmp_path, "game", "# student work")
    assert main.read_text() == "# student work"
    assert (main.parent / "images").is_dir()
    assert (main.parent / "sounds").is_dir()
    with pytest.raises(FileExistsError):
        core.create_project(tmp_path, "game", "replacement")
    with pytest.raises(ValueError):
        core.create_project(tmp_path, "../escape", "")


def test_media_collision_and_paths(tmp_path):
    project = tmp_path / "game"
    project.mkdir()
    image = tmp_path / "actor.png"
    image.write_bytes(b"original")
    assert core.import_media(image, project) == "images/actor.png"
    image.write_bytes(b"new")
    assert core.import_media(image, project) == "images/actor_1.png"
    assert (project / "images/actor.png").read_bytes() == b"original"
    assert (
        core.import_media(project / "images/actor.png", project) == "images/actor.png"
    )
    sound = tmp_path / "click.wav"
    sound.write_bytes(b"sound")
    assert core.import_media(sound, project) == "sounds/click.wav"
    with pytest.raises(ValueError):
        core.import_media(tmp_path / "script.py", project)


def test_checks_explain_events_and_missing_media(tmp_path):
    code = """from miniworlds import *
world = World()
player = Actor()
@player.register
def on_key_down(self):
    pass

def act(self):
    pass
player.add_costume("images/missing.png")
world.add_background("red")
"""
    findings = core.check_code(code, tmp_path)
    assert [f.line for f in findings] == [1, 5, 8, 10]
    assert any("Ereignisparameter" in f.message for f in findings)
    assert any("registriert" in f.message for f in findings)
    assert any("missing.png" in f.message for f in findings)
    assert not any("red" in f.message for f in findings)


def test_checks_handle_syntax_and_unrelated_python():
    assert core.check_code("def broken(:")[0].line == 1
    assert core.check_code("print('hello')") == []


@pytest.mark.parametrize("event", core.EVENTS)
def test_event_signatures_match_modes(event):
    objects = ast.parse(core.event_code("E2", "player", event)).body[0]
    classes = (
        ast.parse("class Player:\n" + core.event_code("Q1", "Player", event))
        .body[0]
        .body[0]
    )
    assert len(objects.args.args) == 1 + len(core.EVENTS[event][0])
    assert len(objects.decorator_list) == 1
    assert not classes.decorator_list
    assert [a.arg for a in objects.args.args] == [a.arg for a in classes.args.args]


@pytest.mark.parametrize("mode", core.MODES)
@pytest.mark.parametrize("kind", ["Pixelwelt", "Kachelwelt"])
@pytest.mark.parametrize("example", ["Grundgerüst", "Bewegung", "Tastatur", "Maus"])
def test_projects_initialize_with_real_engine(mode, kind, example, monkeypatch):
    from miniworlds import App, World

    App.reset(unittest=True)
    monkeypatch.setattr(World, "run", lambda self: None)
    namespace = {}
    try:
        exec(core.project_code(mode, kind, example), namespace)  # noqa: S102 -- exercise trusted templates
        world = namespace["world"]
        player = namespace["player"] if mode == "E2" else world.player
        assert player.world is world
        if example == "Bewegung":
            player.act()
        elif example == "Tastatur":
            player.on_key_pressed_right()
        elif example == "Maus":
            player.on_mouse_left((3, 3))
            assert player.center == (3, 3)
    finally:
        App.reset(unittest=True)


def test_project_mode_is_local_and_preserves_other_settings(tmp_path):
    import json

    e2, q1 = tmp_path / "e2", tmp_path / "q1"
    e2.mkdir()
    q1.mkdir()
    (q1 / core.PROJECT_FILE).write_text('{"other": 42}')
    core.save_project_mode(e2, "E2")
    core.save_project_mode(q1, "Q1")
    nested = q1 / "actors"
    nested.mkdir()
    assert core.project_root(nested / "player.py") == q1
    assert core.project_mode(q1) == "Q1"
    assert core.project_mode(e2) == "E2"
    assert json.loads((q1 / core.PROJECT_FILE).read_text())["other"] == 42
    (q1 / core.PROJECT_FILE).write_text("{bad json")
    with pytest.raises(ValueError):
        core.save_project_mode(q1, "E2")
    assert (q1 / core.PROJECT_FILE).read_text() == "{bad json"


def test_recognition_resolves_aliases_and_inheritance_without_factories():
    code = """import miniworlds as mw
from miniworlds import Actor as Figure
class Base(Figure):
    pass
class Player(Base):
    pass
class Game(mw.World):
    pass
class Unrelated:
    pass
world = Game()
player: Player = Player()
thing = make_something()
"""
    assert {name: t.kind for name, t in core.targets_for(code, "Q1").items()} == {
        "Base": "Actor",
        "Player": "Actor",
        "Game": "World",
    }
    assert set(core.targets_for(code, "E2")) == {"world", "player"}
    assert "on_clicked_left" not in core.events_for("World")
    assert "on_clicked_left" in core.events_for("Actor")


@pytest.mark.parametrize("indent", ["    ", "  ", "\t"])
@pytest.mark.parametrize("ending", ["", "\n"])
def test_class_insertion_preserves_text_and_indentation(indent, ending):
    code = f"from miniworlds import Actor\n# Schülerkommentar äöü\nclass Player(Actor):\n{indent}# erhalten\n{indent}pass{ending}"
    edit = core.event_edit(code, "Q1", "Player", "on_key_down")
    updated = edit.apply(code)
    assert updated.startswith(code)
    assert f"{indent}def on_key_down(self, keys):\n{indent}{indent}pass" in updated
    node = next(
        n for n in ast.walk(ast.parse(updated)) if isinstance(n, ast.FunctionDef)
    )
    assert edit.line == node.lineno


def test_object_insertion_is_before_run_and_existing_event_navigates():
    code = core.project_code("E2")
    edit = core.event_edit(code, "E2", "player", "act")
    updated = edit.apply(code)
    assert updated.index("@player.register") < updated.index("world.run()")
    again = core.event_edit(updated, "E2", "player", "act")
    assert again.existing
    assert again.apply(updated) == updated
    with pytest.raises(ValueError, match="Actor"):
        core.event_edit(code, "E2", "world", "on_clicked_left")
    with pytest.raises(ValueError):
        core.event_edit(code, "E2", "unknown", "act")


def test_existing_class_event_and_unusual_class_are_safe():
    code = core.project_code("Q1", example="Bewegung")
    assert core.event_edit(code, "Q1", "Player", "act").existing
    with pytest.raises(ValueError, match="Zeilen"):
        core.event_edit(
            "from miniworlds import Actor\nclass Player(Actor): pass\n",
            "Q1",
            "Player",
            "act",
        )
    bad_order = (
        "from miniworlds import *\nworld = World()\nworld.run()\nplayer = Actor()\n"
    )
    with pytest.raises(ValueError, match="Reihenfolge"):
        core.event_edit(bad_order, "E2", "player", "act")


@pytest.mark.parametrize(
    "signature, expected",
    [("", "self, keys"), ("self", "self, keys"), ("keys", "self, keys")],
)
def test_signature_fix_is_previewable_and_preserves_body(signature, expected):
    code = f"from miniworlds import Actor\nclass Player(Actor):\n    def on_key_down({signature}):  # behalten\n        print('body')\n"
    finding = next(f for f in core.check_code(code) if f.severity == "Fehler")
    assert finding.explanation and finding.fix
    updated = finding.fix.apply(code)
    assert f"def on_key_down({expected}):  # behalten" in updated
    assert "print('body')" in updated


def test_no_speculative_fix_for_extra_parameters_or_unrelated_class():
    code = "from miniworlds import Actor\nclass Player(Actor):\n    def act(self, a, b):\n        pass\n"
    finding = next(f for f in core.check_code(code) if f.severity == "Fehler")
    assert finding.fix is None
    other = "from miniworlds import World\nclass Other:\n    def act(foo, bar):\n        pass\n"
    assert not any(f.severity == "Fehler" for f in core.check_code(other))


def test_context_understands_self_world_and_user_subclasses():
    code = """from miniworlds import Actor, World
class Player(Actor):
    def act(self):
        self.world.play_sound("sounds/click.wav")
        self.move(1)
world = World()
player = Player()
player.move(1)
"""
    assert core.contextual_topic(code, 4, 25) == ("play_sound", "World")
    assert core.contextual_topic(code, 5, 14) == ("move", "Actor")
    assert core.contextual_topic(code, 8, 9) == ("move", "Actor")
    assert core.contextual_topic(code, 7, 12) == ("Actor", "Actor")


def test_progressive_help_and_example_filters():
    explanation = core.learning_help("move", "E2", "Actor", 0)
    hint = core.learning_help("move", "E2", "Actor", 1)
    example = core.learning_help("move", "E2", "Actor", 2)
    assert "Parameter:" in explanation and "Rückgabe:" in explanation
    assert "Beispiel:" not in explanation and "Hinweis:" not in explanation
    assert "Hinweis:" in hint and "Beispiel:" not in hint
    assert "player.move(2)" in example
    assert "self.play_sound(" in core.learning_help("play_sound", "Q1", "World", 2)
    assert core.filter_examples("Eingabe", "Fortgeschritten") == ["Maus"]
    assert core.filter_examples("Bewegung", "Fortgeschritten") == []


@pytest.mark.parametrize("mode", core.MODES)
def test_teaching_templates_explain_selected_paradigm(mode):
    code = core.teaching_project_code(mode, example="Tastatur")
    assert "# Aufgabe:" in code and "# Beobachtung:" in code
    assert ("# Player erbt" in code) == (mode == "Q1")
    ast.parse(code)


def test_media_call_quotes_paths_and_rejects_code():
    assert (
        core.media_call('images/a"b.png', "Kostüm", "self")
        == 'self.add_costume("images/a\\"b.png")'
    )
    assert (
        core.media_call("sounds/click.wav", "Sound", "self.world")
        == 'self.world.play_sound("sounds/click.wav")'
    )
    with pytest.raises(ValueError):
        core.media_call("image.png", "Kostüm", "__import__('os').system('echo nope')")
