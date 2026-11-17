"""Static class model of a pupil project, for UML views in IDEs.

``analyze`` reads Python sources with ``ast`` only; nothing is imported or run,
so the model also exists while the program is broken or not started. It is the
data behind the Greenfoot-style class diagram: which classes exist, where in
the source they live (file and lines), their attributes and methods, and how
they inherit from each other and from miniworlds classes.
"""
from __future__ import annotations

import ast
import inspect
from typing import Any, Optional

# Methods the engine calls itself; shown as events in the diagram.
EVENT_METHODS = ("act",)


def _base_name(node: ast.expr) -> Optional[str]:
    """``Wurm`` -> ``Wurm``; ``mw.Circle`` -> ``Circle``; ``Generic[T]`` -> ``Generic``."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return None


def _visibility(name: str) -> str:
    return "-" if name.startswith("_") and not name.startswith("__") else "+"


def _params(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    args = function.args
    names = [a.arg for a in args.posonlyargs + args.args]
    if names and names[0] in ("self", "cls"):
        names = names[1:]
    names += [a.arg for a in args.kwonlyargs]
    return names


def _self_attributes(function: ast.FunctionDef | ast.AsyncFunctionDef):
    """Yield ``(name, line)`` for every ``self.<name> = ...`` in a method."""
    owner = function.args.args[0].arg if function.args.args else "self"
    for node in ast.walk(function):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        for target in targets:
            for part in ast.walk(target):
                if (
                    isinstance(part, ast.Attribute)
                    and isinstance(part.value, ast.Name)
                    and part.value.id == owner
                    and isinstance(part.ctx, ast.Store)
                ):
                    yield part.attr, part.lineno


def _describe_class(path: str, node: ast.ClassDef) -> dict[str, Any]:
    methods: list[dict[str, Any]] = []
    attributes: dict[str, dict[str, Any]] = {}
    method_names: set[str] = set()
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_names.add(item.name)
            if item.name.startswith("__") and item.name != "__init__":
                continue  # other dunder methods only add noise to the diagram
            methods.append(
                {
                    "name": item.name,
                    "line": item.lineno,
                    "params": _params(item),
                    "visibility": _visibility(item.name),
                    "kind": "event"
                    if item.name in EVENT_METHODS or item.name.startswith("on_")
                    else "method",
                }
            )
        elif isinstance(item, (ast.Assign, ast.AnnAssign)):
            targets = item.targets if isinstance(item, ast.Assign) else [item.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    attributes.setdefault(
                        target.id,
                        {"name": target.id, "line": item.lineno, "static": True},
                    )
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for name, line in _self_attributes(item):
                attributes.setdefault(name, {"name": name, "line": line, "static": False})
    for attribute in attributes.values():
        attribute["visibility"] = _visibility(attribute["name"])
    return {
        "name": node.name,
        "file": path,
        "line": node.lineno,
        "end_line": node.end_lineno or node.lineno,
        "bases": [name for name in map(_base_name, node.bases) if name],
        "bases_text": [ast.unparse(base) for base in node.bases],
        "methods": methods,
        "attributes": [a for n, a in attributes.items() if n not in method_names],
    }


def _library_class(name: str):
    import miniworlds

    candidate = getattr(miniworlds, name, None)
    return candidate if inspect.isclass(candidate) else None


def _library_chain(cls: type) -> list[str]:
    """Public miniworlds classes from ``cls`` up to the root (names only)."""
    import miniworlds

    chain = []
    for ancestor in cls.__mro__:
        if ancestor is object:
            continue
        if getattr(miniworlds, ancestor.__name__, None) is ancestor:
            chain.append(ancestor.__name__)
    return chain


def _kind_of_library(cls: type) -> str:
    from miniworlds.actors.actor import Actor
    from miniworlds.worlds.world import World

    if issubclass(cls, Actor):
        return "actor"
    if issubclass(cls, World):
        return "world"
    return "other"


def analyze(files: dict[str, str]) -> dict[str, Any]:
    """Return ``{"classes": [...], "libraries": [...], "errors": [...]}``.

    ``classes`` are the top-level classes of the project, ordered by file
    (``main.py`` first) and line. ``kind`` is ``"actor"``, ``"world"`` or
    ``"other"`` and follows the inheritance chain, also across files.
    ``libraries`` lists the miniworlds classes the project inherits from,
    including their own public ancestors, so a diagram can draw the whole chain.
    ``errors`` names files that could not be parsed; their classes are missing.
    """
    classes: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for path in sorted(files, key=lambda p: (p != "main.py", p)):
        if not path.endswith(".py") or not isinstance(files[path], str):
            continue
        try:
            tree = ast.parse(files[path], filename=path)
        except SyntaxError as error:
            errors.append({"file": path, "line": error.lineno or 1, "message": error.msg})
            continue
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(_describe_class(path, node))

    by_name: dict[str, dict[str, Any]] = {}
    for info in classes:
        by_name.setdefault(info["name"], info)

    libraries: dict[str, dict[str, Any]] = {}
    for info in classes:
        for base in info["bases"]:
            library = None if base in by_name else _library_class(base)
            if library is None:
                continue
            chain = _library_chain(library)
            for index, name in enumerate(chain):
                libraries.setdefault(
                    name,
                    {
                        "name": name,
                        "base": chain[index + 1] if index + 1 < len(chain) else None,
                        "kind": _kind_of_library(_library_class(name)),
                    },
                )

    def resolve_kind(info: dict[str, Any], seen: frozenset[str]) -> str:
        for base in info["bases"]:
            user = by_name.get(base)
            if user is not None:
                kind = (
                    resolve_kind(user, seen | {info["name"]})
                    if user["name"] not in seen
                    else "other"
                )
            else:
                library = _library_class(base)
                kind = "other" if library is None else _kind_of_library(library)
            if kind != "other":
                return kind
        return "other"

    for info in classes:
        info["kind"] = resolve_kind(info, frozenset())
        info["origin"] = "user"
    return {
        "classes": classes,
        "libraries": sorted(libraries.values(), key=lambda lib: lib["name"]),
        "errors": errors,
    }
