"""Index of the public miniworlds API for editor completion and hints.

``build_index`` lists, for every public ``Actor`` and ``World`` class, the
public members it defines itself (methods and properties with a short
signature and the first docstring line) and its public base class. A member
that a class inherits is found by following ``base``; nothing is duplicated.
"""
from __future__ import annotations

import functools
import inspect
from typing import Any, Optional

MAX_DOC = 140


def _first_line(doc: Optional[str]) -> str:
    # cleandoc, not getdoc: getdoc(<str>) would return the docstring of ``str``.
    text = inspect.cleandoc(doc) if isinstance(doc, str) else ""
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


def _own_classes(cls: type) -> list[type]:
    """``cls`` plus the non-exported miniworlds bases it inherits from.

    Engine classes get much of their API from internal base classes
    (``ActorBase``, ``WorldBase``, ...). Pupils see them as part of ``Actor`` and
    ``World``, so their members are listed with the nearest public class.
    """
    import miniworlds

    found = [cls]
    for ancestor in cls.__mro__[1:]:
        if ancestor is object:
            break
        if getattr(miniworlds, ancestor.__name__, None) is ancestor:
            break  # next public class: it lists its own members
        if ancestor.__module__.startswith("miniworlds"):
            found.append(ancestor)
    return found


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
        seen: set[str] = set()
        for source in _own_classes(cls):
            for member_name, member in sorted(vars(source).items()):
                if member_name.startswith("_") or member_name in seen:
                    continue
                if isinstance(member, (property, functools.cached_property)):
                    seen.add(member_name)
                    getter = member.fget if isinstance(member, property) else member.func
                    members.append(
                        {"name": member_name, "kind": "property", "doc": _first_line(getter.__doc__ if getter else None)}
                    )
                elif inspect.isfunction(member):
                    seen.add(member_name)
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
            "_cls": cls,
        }
    # Names that exist on the class but are not part of the curated list
    # (pygame sprite methods, plain class attributes, ...): never suggested,
    # but known, so hints do not call them typos.
    for name, entry in classes.items():
        chain_names: set[str] = set()
        current: Optional[str] = name
        while current:
            chain_names |= {m["name"] for m in classes[current]["members"]}
            current = classes[current]["base"]
        entry["hidden"] = sorted(
            n for n in dir(entry.pop("_cls")) if not n.startswith("_") and n not in chain_names
        )
    return {"classes": classes}
