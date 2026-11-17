"""Run the ``::`` code examples from public docstrings against a real world.

Docstring examples are fragments (``actor.detect(Wall)``) that rely on names
defined elsewhere. They are executed with a small prelude: the receiver
(``world``/``actor``/...) is a real instance of the class that owns the
docstring and capitalised unknown names become empty ``Actor`` subclasses.

Why this exists: ``actor.detect(Wall)`` and ``world.contains_position(...)``
were broken for months although the docs showed them, because the tests only
exercised mocks and other argument shapes.
"""
from __future__ import annotations

import ast
import inspect
import re
import textwrap
import warnings

import pygame
import pytest

import miniworlds
from miniworlds import Actor, World
from miniworlds.base.app import App
from test.docs.generate_doc_example_tests import UndefinedNameVisitor

# Examples that need context this harness does not model (a prepared costume, a
# tile-valid position, a mouse position, a Vector receiver, ...). They are
# skipped, not failed. A skipped example can still be broken: when the prelude
# learns to model its context, delete the entry. Examples that really fail go
# to the engine/docstring fix, never to this list.
NEEDS_CONTEXT: dict[str, str] = {
    "Actor.animate_costume#1": "needs a prepared costume (run_costume)",
    "Actor.next_costume#1": "needs an actor with several costumes",
    "Appearance.after_animation#1": "receiver must be a Costume",
    "Appearance.set_image#1": "receiver must be a Background with images",
    "Console.newline#1": "receiver must be a Console",
    "Costume.info_overlay#1": "receiver must be a Costume",
    "HexWorld.find_nearest#1": "robot must stand on a hex tile",
    "HexWorld.get_reachable_tiles#1": "robot must stand on a hex tile",
    "HexWorld.get_actors_from_pixel#1": "needs a mouse position",
    "HexWorld.get_corner_from_pixel#1": "needs a mouse position",
    "HexWorld.get_edge_from_pixel#1": "needs a mouse position",
    "TextBox.create_line_actors#1": "receiver must be a TextBox",
    "Text.text#1": "needs a player object with lives",
    "Text.value#1": "needs a player object with score",
    "TileBase.data#1": "needs a TiledWorld around the tile",
    "TiledWorld.draw_on_image#1": "needs a pygame surface",
    "TiledWorld.get_corner#1": "actor must stand on a tile corner",
    "TiledWorld.get_edge#1": "actor must stand on a tile edge",
    "TiledWorld.get_tile#1": "actor must stand on a tile",
    "Vector.limit#1": "receiver must be a Vector",
    "Vector.rotate#1": "receiver must be a Vector",
    "World.direction_to#1": "needs a mouse position",
    "World.remove_background#1": "needs a world that already has a background",
}

ASSET_RE = re.compile(r"""["']([\w/.-]+\.(?:png|jpg|jpeg|gif|bmp|wav|mp3|ogg))["']""")


def _code_blocks(doc: str) -> list[str]:
    lines = doc.expandtabs().split("\n")
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].rstrip().endswith("::"):
            base = len(lines[i]) - len(lines[i].lstrip())
            j = i + 1
            buffer: list[str] = []
            while j < len(lines) and (
                not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > base
            ):
                buffer.append(lines[j])
                j += 1
            block = textwrap.dedent("\n".join(buffer)).strip("\n")
            if block.strip():
                blocks.append(block)
            i = j
        else:
            i += 1
    return blocks


def _collect() -> list[tuple[str, type, str]]:
    found: list[tuple[str, type, str]] = []
    seen: set[type] = set()
    for name in sorted(dir(miniworlds)):
        cls = getattr(miniworlds, name)
        if not (inspect.isclass(cls) and cls.__module__.startswith("miniworlds")):
            continue
        if cls in seen:
            continue
        seen.add(cls)
        for member_name, member in vars(cls).items():
            function = member.fget if isinstance(member, property) else member
            doc = getattr(function, "__doc__", None)
            if member_name.startswith("_") or not doc:
                continue
            for index, block in enumerate(_code_blocks(doc), 1):
                found.append((f"{cls.__name__}.{member_name}#{index}", cls, block))
    return found


EXAMPLES = _collect()


def test_docstring_examples_are_collected():
    """Guard: a broken collector must not turn the suite into a silent no-op."""
    assert len(EXAMPLES) >= 150
    labels = {label for label, _, _ in EXAMPLES}
    assert "Actor.detect#1" in labels
    assert "World.contains_position#1" in labels
    assert not set(NEEDS_CONTEXT) - labels, "stale NEEDS_CONTEXT entries"


def _instantiate(cls: type, world):
    """Best-effort instance of ``cls`` for use as receiver."""
    attempts = (
        lambda: cls((100, 100), world=world),
        lambda: cls((100, 100)),
        lambda: cls(),
    )
    for attempt in attempts:
        try:
            return attempt()
        except Exception:
            continue
    return None


def _make_world(owner: type):
    if inspect.isclass(owner) and issubclass(owner, World):
        for args in ((8, 8), (200, 200), ()):
            try:
                return owner(*args)
            except Exception:
                continue
    return World(200, 200)


def _prepare_assets(code: str, directory) -> None:
    pygame.init()
    for path in ASSET_RE.findall(code):
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.rsplit(".", 1)[-1] in ("png", "jpg", "jpeg", "gif", "bmp"):
            pygame.image.save(pygame.Surface((32, 32)), str(target))
        else:
            target.write_bytes(b"")


@pytest.mark.unit
@pytest.mark.parametrize(
    "label, owner, code", EXAMPLES, ids=[label for label, _, _ in EXAMPLES]
)
def test_docstring_example_runs(label, owner, code, tmp_path, monkeypatch):
    if label in NEEDS_CONTEXT:
        pytest.skip(NEEDS_CONTEXT[label])
    try:
        tree = ast.parse(code)
    except SyntaxError:
        pytest.skip("pseudo code, not valid Python")
    undefined = UndefinedNameVisitor()
    undefined.visit(tree)

    monkeypatch.chdir(tmp_path)
    _prepare_assets(code, tmp_path)
    monkeypatch.setattr(World, "run", lambda self, *a, **k: None)
    App.reset(unittest=True, file=__file__)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        world = _make_world(owner)
        namespace = {n: getattr(miniworlds, n) for n in dir(miniworlds) if not n.startswith("_")}
        namespace["__name__"] = "__docstring__"
        receiver = None if issubclass(owner, World) else _instantiate(owner, world)
        for name in sorted(undefined.undefined):
            if name in namespace:
                continue
            if name[0].isupper():
                namespace[name] = type(name, (Actor,), {})
            elif "world" in name.lower():
                namespace[name] = world
            elif receiver is not None:
                namespace[name] = receiver
            else:
                namespace[name] = _instantiate(Actor, world)
        try:
            exec(compile(code, label, "exec"), namespace)
        except Exception as error:
            raise AssertionError(
                f"Docstring example {label} fails: {type(error).__name__}: {error}\n\n{code}"
            ) from error
    App.reset(unittest=True, file=__file__)
