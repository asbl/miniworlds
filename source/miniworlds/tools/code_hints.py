"""Beginner-friendly hints for pupil code, from source only (nothing runs).

``check(files)`` finds the mistakes beginners make most often and that Python
only reports late or cryptically:

* a name that is defined nowhere (typo, or ``move(2)`` instead of ``self.move(2)``),
* ``self.mov(2)``: a member that does not exist but is close to one that does,
* a method without ``self`` (``def act():``),
* a program that never calls ``world.run()``.

The checks are deliberately conservative: a hint is only given when it is
very likely right, never for names that might come from code we cannot see.
"""
from __future__ import annotations

import ast
import builtins
import difflib
import re
from typing import Any, Optional

from miniworlds.tools import class_model
from miniworlds.tools.api_index import build_index

CUTOFF_NAME = 0.75
CUTOFF_MEMBER = 0.72
OBJECT_MEMBERS = set(dir(object))


def _column(line: str, byte_offset: int) -> int:
    """UTF-16 column (what editors like CodeMirror use) of an ``ast`` UTF-8 byte offset."""
    prefix = line.encode("utf-8")[:byte_offset].decode("utf-8", errors="ignore")
    return len(prefix.encode("utf-16-le")) // 2


def _hint(path, node, message, severity="warning", code="", replacement=None, lines=None):
    col = node.col_offset
    end = getattr(node, "end_col_offset", None) or node.col_offset + 1
    if lines is not None and node.lineno <= len(lines):
        text = lines[node.lineno - 1]
        col, end = _column(text, col), _column(text, end)
    return {
        "file": path,
        "line": node.lineno,
        "col": col,
        "end_col": end,
        "severity": severity,
        "code": code,
        "message": message,
        "replacement": replacement,
    }


def _bound_names(tree: ast.AST, out: set[str]) -> bool:
    """Collect every name bound anywhere; return True if a star import hides names."""
    star = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            out.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
            if not isinstance(node, ast.ClassDef):
                a = node.args
                for arg in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]:
                    if arg is not None:
                        out.add(arg.arg)
        elif isinstance(node, ast.Lambda):
            a = node.args
            for arg in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]:
                if arg is not None:
                    out.add(arg.arg)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    star = True
                else:
                    out.add(alias.asname or alias.name)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            out.add(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            out.update(node.names)
        elif isinstance(node, ast.MatchAs) and node.name:
            out.add(node.name)
        elif isinstance(node, ast.MatchStar) and node.name:
            out.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            out.add(node.rest)
    return star


def _members_of(
    name: str, user: dict[str, dict], api: dict[str, Any], files_attrs: dict[str, set[str]], seen=None
) -> Optional[set[str]]:
    """All member names of class ``name``; ``None`` if any base is unknown."""
    seen = seen or set()
    if name in seen:
        return None
    seen = seen | {name}
    if name in user:
        info = user[name]
        names = {m["name"] for m in info["methods"]} | {a["name"] for a in info["attributes"]}
        names |= files_attrs.get(name, set())
        for base in info["bases"] or ["object"]:
            if base == "object":
                continue
            inherited = _members_of(base, user, api, files_attrs, seen)
            if inherited is None:
                return None
            names |= inherited
        return names
    if name in api:
        entry = api[name]
        names = {m["name"] for m in entry["members"]} | set(entry.get("hidden", ()))
        if entry["base"]:
            inherited = _members_of(entry["base"], user, api, files_attrs, seen)
            if inherited is None:
                return None
            names |= inherited
        return names
    return None


def _self_attributes(node: ast.ClassDef) -> set[str]:
    """Names assigned as ``self.x`` anywhere in the class, including nested code."""
    found: set[str] = set()
    for item in ast.walk(node):
        if (
            isinstance(item, ast.Attribute)
            and isinstance(item.value, ast.Name)
            and item.value.id == "self"
            and isinstance(item.ctx, (ast.Store, ast.Del))
        ):
            found.add(item.attr)
    return found


def check(files: dict[str, str], index: Optional[dict] = None) -> list[dict[str, Any]]:
    """Return hints sorted by file and line (see module docstring)."""
    import miniworlds

    api = (index or build_index())["classes"]
    trees: dict[str, ast.Module] = {}
    for path in sorted(files):
        if path.endswith(".py") and isinstance(files[path], str):
            try:
                trees[path] = ast.parse(files[path], filename=path)
            except SyntaxError:
                continue  # the syntax error itself is reported elsewhere

    model = class_model.analyze({p: files[p] for p in trees})
    user = {c["name"]: c for c in model["classes"]}
    hints: list[dict] = []

    bound: set[str] = set(dir(builtins)) | {
        "__name__", "__file__", "__doc__", "__class__", "__builtins__", "__spec__", "__loader__", "__package__",
    }
    star = False
    miniworlds_star = False
    for tree in trees.values():
        star |= _bound_names(tree, bound)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "miniworlds" and any(a.name == "*" for a in node.names):
                miniworlds_star = True
    if miniworlds_star:
        bound |= {n for n in dir(miniworlds) if not n.startswith("_")}
    star_unknown = star and not miniworlds_star

    # Extension packages (physics, robot, ...) add members to engine classes.
    extended = any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and any(
            name.startswith("miniworlds_")
            for name in (
                [node.module or ""] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names]
            )
        )
        for tree in trees.values()
        for node in ast.walk(tree)
    )

    class_attrs: dict[str, set[str]] = {}
    for tree in trees.values():
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_attrs[node.name] = _self_attributes(node)

    for path, tree in trees.items():
        lines = re.split(r"\r\n|\r|\n", files[path])
        # --- names defined nowhere -------------------------------------
        if not star_unknown:
            enclosing = _enclosing_classes(tree)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in bound:
                    cls_name = enclosing.get(id(node))
                    if cls_name:
                        members = _members_of(cls_name, user, api, class_attrs)
                        if members and node.id in members:
                            hints.append(
                                _hint(path, node, f"„{node.id}“ gehört zum Objekt: schreibe self.{node.id}.", "error", "missing-self", f"self.{node.id}", lines=lines)
                            )
                            continue
                    close = difflib.get_close_matches(node.id, sorted(bound), n=1, cutoff=CUTOFF_NAME)
                    text = f"Der Name „{node.id}“ ist nirgends definiert."
                    if close:
                        text += f" Meintest du „{close[0]}“?"
                    hints.append(_hint(path, node, text, "error", "undefined-name", close[0] if close else None, lines=lines))

        # --- method without self ----------------------------------------
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                decorators = {d.id for d in item.decorator_list if isinstance(d, ast.Name)}
                if decorators & {"staticmethod", "classmethod"}:
                    continue
                first = (item.args.posonlyargs + item.args.args)[:1]
                if not first or first[0].arg not in ("self", "cls"):
                    hints.append(
                        _hint(path, item, f"Die Methode „{item.name}“ braucht „self“ als ersten Parameter: def {item.name}(self, …).", "error", "missing-self-param", lines=lines)
                    )

            # --- self.<typo> ---------------------------------------------
            members = None if extended else _members_of(node.name, user, api, class_attrs)
            if members is None:
                continue
            members = members | _descendant_members(node.name, user, class_attrs)
            known = sorted(members | OBJECT_MEMBERS)
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for sub in _walk_same_self(item):
                    if (
                        isinstance(sub, ast.Attribute)
                        and isinstance(sub.value, ast.Name)
                        and sub.value.id == "self"
                        and isinstance(sub.ctx, ast.Load)
                        and sub.attr not in members
                        and sub.attr not in OBJECT_MEMBERS
                    ):
                        close = difflib.get_close_matches(sub.attr, known, n=1, cutoff=CUTOFF_MEMBER)
                        if close:
                            hints.append(
                                _hint(path, sub, f"„self.{sub.attr}“ gibt es nicht. Meintest du „self.{close[0]}“?", "warning", "unknown-member", f"self.{close[0]}", lines=lines)
                            )

        # --- program never starts the world --------------------------------
        if path == "main.py":
            calls_run = any(
                isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run"
                for n in ast.walk(tree)
            )
            if not calls_run and tree.body:
                last = tree.body[-1]
                hints.append(
                    _hint(path, last, "Die Welt wird nie gestartet: am Ende fehlt z. B. welt.run().", "warning", "no-run", lines=lines)
                )

    return sorted(hints, key=lambda h: (h["file"], h["line"], h["col"]))


def _walk_same_self(function: ast.AST):
    """Walk a method body, skipping nested functions that bind their own ``self``.

    ``@world.register`` handlers written inside a method take ``self`` too, but it
    is the registered object, not the class being checked.
    """
    stack = list(ast.iter_child_nodes(function))
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            args = node.args
            if any(a.arg == "self" for a in args.posonlyargs + args.args + args.kwonlyargs):
                continue
        yield node
        stack.extend(ast.iter_child_nodes(node))


def _descendant_members(name: str, user: dict[str, dict], files_attrs: dict[str, set[str]]) -> set[str]:
    """Members that subclasses of ``name`` add.

    A base class may call hooks only its subclasses define (template method),
    so those names are legitimate on ``self`` there.
    """
    def lineage(cls_name: str, seen: frozenset = frozenset()) -> set[str]:
        if cls_name in seen or cls_name not in user:
            return set()
        out = {cls_name}
        for base in user[cls_name]["bases"]:
            out |= lineage(base, seen | {cls_name})
        return out

    names: set[str] = set()
    for other, info in user.items():
        if other != name and name in lineage(other):
            names |= {m["name"] for m in info["methods"]} | {a["name"] for a in info["attributes"]}
            names |= files_attrs.get(other, set())
    return names


def _enclosing_classes(tree: ast.Module) -> dict[int, str]:
    """Map ``id(name node)`` to the class it sits in (only inside methods)."""
    mapping: dict[int, str] = {}
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        for item in cls.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for node in ast.walk(item):
                    if isinstance(node, ast.Name):
                        mapping[id(node)] = cls.name
    return mapping
