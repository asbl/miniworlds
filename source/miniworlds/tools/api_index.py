"""Index of the public miniworlds API for editor completion and hints.

``build_index`` lists, for every public ``Actor`` and ``World`` class, the
public members it defines itself (methods and properties with a short
signature and the first docstring line) and its public base class. A member
that a class inherits is found by following ``base``; nothing is duplicated.
"""
from __future__ import annotations

import inspect
from typing import Any, Optional

MAX_DOC = 140


def _first_line(doc: Optional[str]) -> str:
    text = inspect.getdoc(doc) if isinstance(doc, str) else doc
    if not text:
        return ""
    line = text.strip().split("\n\n")[0].replace("\n", " ").strip()
    return line if len(line) <= MAX_DOC else line[: MAX_DOC - 1] + "…"


def _signature(function: Any) -> str:
    try:
        parameters = list(inspect.signature(function).parameters.values())[1:]
    except (TypeError, ValueError):
        return "()"
    shown = []
    for parameter in parameters:
        if parameter.kind is parameter.VAR_POSITIONAL:
            shown.append("*" + parameter.name)
        elif parameter.kind is parameter.VAR_KEYWORD:
            shown.append("**" + parameter.name)
        elif parameter.default is parameter.empty:
            shown.append(parameter.name)
        else:
            shown.append(f"{parameter.name}={parameter.default!r}")
    return "(" + ", ".join(shown) + ")"


def _public_base(cls: type) -> Optional[str]:
    import miniworlds

    for ancestor in cls.__mro__[1:]:
        if getattr(miniworlds, ancestor.__name__, None) is ancestor:
            return ancestor.__name__
    return None


def build_index() -> dict[str, Any]:
    """Return ``{"classes": {name: {"base", "kind", "members": [...]}}}``."""
    import miniworlds
    from miniworlds.actors.actor import Actor
    from miniworlds.worlds.world import World

    classes: dict[str, Any] = {}
    for name in sorted(dir(miniworlds)):
        cls = getattr(miniworlds, name)
        if not (inspect.isclass(cls) and issubclass(cls, (Actor, World))):
            continue
        members = []
        for member_name, member in sorted(vars(cls).items()):
            if member_name.startswith("_"):
                continue
            if isinstance(member, property):
                members.append(
                    {"name": member_name, "kind": "property", "doc": _first_line(member.fget.__doc__ if member.fget else None)}
                )
            elif inspect.isfunction(member):
                members.append(
                    {
                        "name": member_name,
                        "kind": "method",
                        "signature": _signature(member),
                        "doc": _first_line(member.__doc__),
                    }
                )
        classes[name] = {
            "base": _public_base(cls),
            "kind": "actor" if issubclass(cls, Actor) else "world",
            "members": members,
        }
    return {"classes": classes}
