"""Offline learning content and conservative checks; no GUI or engine imports."""

import ast
import keyword
import shutil
from dataclasses import dataclass
from pathlib import Path

MODES = {
    "E2": "E2 · Programmieren mit Objekten",
    "Q1": "Q1 · Programmieren mit Klassen",
}
EVENTS = {
    "on_setup": ((), "Einmal beim Einrichten."),
    "act": ((), "In jedem Frame."),
    "on_key_down": (
        ("keys",),
        "Einmal beim Drücken einer Taste; keys enthält Tastennamen.",
    ),
    "on_key_pressed": (("keys",), "In jedem Frame bei gehaltener Taste."),
    "on_key_up": (("keys",), "Beim Loslassen einer Taste."),
    "on_key_down_space": ((), "Einmal beim Drücken der Leertaste."),
    "on_key_pressed_right": ((), "In jedem Frame bei gehaltener rechter Pfeiltaste."),
    "on_mouse_left": (
        ("position",),
        "Linker Mausklick; position enthält die Koordinaten.",
    ),
    "on_clicked_left": (("position",), "Linker Klick auf einen Actor (nur Actor)."),
    "on_detecting_actor": (
        ("other",),
        "Kollision mit einem anderen Actor (nur Actor).",
    ),
}
ACTOR_ONLY = {"on_clicked_left", "on_detecting_actor"}
TOPICS = {
    "World": (
        "Eine Welt enthält die Actors. Größen werden in Pixeln angegeben.",
        "world = World(640, 480)",
        "class MyWorld(World):\n    def on_setup(self):\n        self.add_background((255, 255, 255))\n\nworld = MyWorld(640, 480)",
    ),
    "TiledWorld": (
        "Eine Kachelwelt wird in Spalten und Zeilen angegeben, nicht in Pixeln.",
        "world = TiledWorld(20, 15)",
        "class MyWorld(TiledWorld):\n    def on_setup(self):\n        self.tile_size = 32\n\nworld = MyWorld(20, 15)",
    ),
    "Actor": (
        "Ein Actor ist eine Figur in der Welt. Die Position ist ein Paar (x, y).",
        "player = Actor((100, 100))",
        'class Player(Actor):\n    def on_setup(self):\n        self.add_costume("images/player.png")\n\nplayer = Player((100, 100))',
    ),
    "move": (
        "Bewegt die Figur in ihre aktuelle Richtung.",
        "player.move(2)",
        "self.move(2)",
    ),
    "add_costume": (
        "Fügt einer Figur ein Kostüm hinzu. Nutze einen Pfad relativ zur Programmdatei.",
        'player.add_costume("images/player.png")',
        'self.add_costume("images/player.png")',
    ),
    "add_background": (
        "Legt einen Hintergrund als Farbe oder Bild fest.",
        'world.add_background("images/background.png")',
        'self.add_background("images/background.png")',
    ),
    "play_sound": (
        "Spielt eine Sounddatei ab.",
        'world.play_sound("sounds/click.wav")',
        'self.world.play_sound("sounds/click.wav")',
    ),
    "run": (
        "Startet die Ereignisschleife. Weitere Einrichtung gehört vor diesen Aufruf.",
        "world.run()",
        "world.run()",
    ),
    "register": (
        "E2: Der Dekorator bindet eine Funktion an ein Objekt. Q1: Ereignisse werden als Methoden in der Klasse definiert.",
        "@player.register\ndef act(self):\n    self.move(1)",
        "class Player(Actor):\n    def act(self):\n        self.move(1)",
    ),
}


def event_code(mode, target, event, body="pass"):
    if mode not in MODES or event not in EVENTS:
        raise ValueError("Unbekannter Modus oder unbekanntes Ereignis")
    if not target.isidentifier() or keyword.iskeyword(target):
        raise ValueError("Bitte einen gültigen Objektnamen wählen.")
    params = ", ".join(("self",) + EVENTS[event][0])
    code = (
        f"def {event}({params}):\n"
        + "\n".join("    " + line for line in body.splitlines())
        + "\n"
    )
    if mode == "E2":
        return f"@{target}.register\n" + code
    return "\n".join("    " + line if line else "" for line in code.split("\n"))


def help_text(topic, mode):
    if topic in EVENTS:
        return EVENTS[topic][1] + "\n\n" + event_code(mode, "player", topic)
    text, objects, classes = TOPICS.get(topic, TOPICS["World"])
    return text + "\n\n" + (objects if mode == "E2" else classes)


def project_code(mode, kind="Pixelwelt", example="Grundgerüst"):
    world_type = "TiledWorld" if kind == "Kachelwelt" else "World"
    size = "20, 15" if kind == "Kachelwelt" else "640, 480"
    position = "2, 2" if kind == "Kachelwelt" else "100, 100"
    behavior = {
        "Bewegung": ("act", "self.move(1)"),
        "Tastatur": ("on_key_pressed_right", "self.x += 1"),
        "Maus": ("on_mouse_left", "self.center = position"),
    }
    if mode == "E2":
        code = f"from miniworlds import World, TiledWorld, Actor\n\nworld = {world_type}({size})\nworld.add_background((240, 240, 240))\nplayer = Actor(({position}))\nplayer.add_costume((50, 120, 220))\n"
        if example in behavior:
            event, body = behavior[example]
            code += "\n" + event_code(mode, "player", event, body)
    elif mode == "Q1":
        code = "from miniworlds import World, TiledWorld, Actor\n\n\nclass Player(Actor):\n    def on_setup(self):\n        self.add_costume((50, 120, 220))\n"
        if example in behavior:
            event, body = behavior[example]
            code += "\n" + event_code(mode, "player", event, body)
        code += f"\n\nclass MyWorld({world_type}):\n    def on_setup(self):\n        self.add_background((240, 240, 240))\n        self.player = Player(({position}))\n\n\nworld = MyWorld({size})\n"
    else:
        raise ValueError("Unbekannter Modus")
    return code + "\nworld.run()\n"


def create_project(parent, name, code):
    if (
        not name
        or name in {".", ".."}
        or Path(name).name != name
        or "/" in name
        or "\\" in name
    ):
        raise ValueError("Bitte einen einfachen Ordnernamen angeben.")
    path = Path(parent) / name
    path.mkdir()  # Never overwrite an existing project.
    (path / "images").mkdir()
    (path / "sounds").mkdir()
    (path / "main.py").write_text(code, encoding="utf-8")
    return path / "main.py"


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
SOUND_EXTENSIONS = {".wav", ".ogg", ".mp3"}


def import_media(source, project):
    source = Path(source)
    suffix = source.suffix.lower()
    if suffix not in IMAGE_EXTENSIONS | SOUND_EXTENSIONS:
        raise ValueError("Nicht unterstütztes Bild- oder Soundformat.")
    folder = Path(project) / ("images" if suffix in IMAGE_EXTENSIONS else "sounds")
    folder.mkdir(exist_ok=True)
    target = folder / source.name
    if target.exists() and source.resolve() == target.resolve():
        return target.relative_to(project).as_posix()
    i = 1
    while target.exists():
        target = folder / f"{source.stem}_{i}{source.suffix}"
        i += 1
    shutil.copy2(source, target)
    return target.relative_to(project).as_posix()


@dataclass(frozen=True)
class Finding:
    line: int
    message: str
    severity: str = "Hinweis"
    explanation: str = ""
    fix: "CodeEdit | None" = None


def check_code(code, project=None, mode="E2"):
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return [
            Finding(
                error.lineno or 1,
                f"Python-Syntax: {error.msg}",
                "Fehler",
                "Python kann dieses Programm noch nicht lesen. Korrigiere zuerst die markierte Stelle.",
            )
        ]
    findings = []
    _, known_classes, known_objects = analyze(code)
    parents = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }
    relevant = any(
        isinstance(n, ast.ImportFrom)
        and n.module
        and n.module.startswith("miniworlds")
        or isinstance(n, ast.Import)
        and any(a.name.startswith("miniworlds") for a in n.names)
        for n in ast.walk(tree)
    )
    if not relevant:
        return findings
    run = False
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in EVENTS
        ):
            parent = parents.get(node)
            registered = any(
                isinstance(d, ast.Attribute)
                and d.attr == "register"
                or isinstance(d, ast.Call)
                and isinstance(d.func, ast.Attribute)
                and d.func.attr == "register"
                for d in node.decorator_list
            )
            is_method = (
                isinstance(parent, ast.ClassDef) and parent.name in known_classes
            )
            expected = 1 + len(EVENTS[node.name][0])
            args = node.args.posonlyargs + node.args.args
            if (registered or is_method) and (
                len(args) != expected or not args or args[0].arg != "self"
            ):
                fix = signature_fix(code, node)
                findings.append(
                    Finding(
                        node.lineno,
                        f"{node.name}: Erwartet self und {expected - 1} Ereignisparameter.",
                        "Fehler",
                        "miniworlds ruft diese Methode mit der festgelegten Ereignissignatur auf. "
                        "Bei einer Änderung von Parametern müssen Verwendungen im Methodenrumpf geprüft werden.",
                        fix,
                    )
                )
            if parent is tree and not registered:
                findings.append(
                    Finding(
                        node.lineno,
                        "Ereignisfunktion ohne @objekt.register: Prüfe, ob sie an anderer Stelle registriert wird.",
                        explanation="Eine frei stehende Funktion wird nicht automatisch zum Ereignis. In Q1 gehört sie als Methode in die Klasse. Indirekte Registrierung kann diese Prüfung nicht erkennen.",
                    )
                )
            if mode == "Q1" and registered:
                findings.append(
                    Finding(
                        node.lineno,
                        "Q1: Dieses Ereignis verwendet einen Dekorator. Als Klassenmethode ist er nicht nötig.",
                    )
                )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "run":
                run = True
            if (
                project
                and node.func.attr in {"add_costume", "add_background", "play_sound"}
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                value = node.args[0].value
                # Only unambiguous file references, not named colors or dynamic expressions.
                if (
                    Path(value).suffix.lower() in IMAGE_EXTENSIONS | SOUND_EXTENSIONS
                    and not (Path(project) / value).is_file()
                ):
                    findings.append(
                        Finding(
                            node.lineno,
                            f"Datei nicht im Projekt gefunden: {value}. Prüfe auch den Suchpfad der Welt.",
                            explanation="Importiere die Datei über Bilder & Sounds oder prüfe Groß-/Kleinschreibung. Dynamische Suchpfade können von dieser Prüfung nicht erfasst werden.",
                        )
                    )
    if not run:
        worlds = [t for t in known_objects.values() if t.kind == "World"]
        fix = None
        if len(worlds) == 1:
            fix = CodeEdit(
                len(code),
                len(code),
                "\n" + worlds[0].name + ".run()\n",
                len(code.splitlines()) + 1,
            )
        findings.append(
            Finding(
                1,
                "Kein .run()-Aufruf gefunden. Ein einfaches Startprogramm endet mit world.run(); bei mehreren Dateien kann der Aufruf anderswo stehen.",
                explanation="Nur im Startprogramm ergänzen. Bibliotheksmodule brauchen keinen eigenen run-Aufruf.",
                fix=fix,
            )
        )
    return sorted(findings, key=lambda f: f.line)


# Project metadata is deliberately small and independent of Thonny's settings.
PROJECT_FILE = ".miniworlds.json"


def project_root(filename):
    if not filename:
        return None
    folder = Path(filename).absolute().parent
    for candidate in (folder, *folder.parents):
        if (candidate / PROJECT_FILE).is_file():
            return candidate
    return folder


def project_mode(project, default="E2"):
    import json

    path = Path(project) / PROJECT_FILE
    if not path.exists():
        return default
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("mode") not in MODES:
        raise ValueError(f"Ungültiger Unterrichtsmodus in {path}")
    return data["mode"]


def save_project_mode(project, mode):
    import json

    if mode not in MODES:
        raise ValueError("Unbekannter Unterrichtsmodus")
    path = Path(project) / PROJECT_FILE
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(data, dict):
        raise ValueError("Die Projektdatei muss ein JSON-Objekt enthalten.")  # noqa: TRY004 -- invalid file content
    data["mode"] = mode
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


@dataclass(frozen=True)
class Target:
    name: str
    kind: str  # Actor or World
    line: int


def _dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else ""
    return ""


def analyze(code):
    """Resolve imported miniworlds types, aliases and local inheritance only.

    Unknown factories are left unknown instead of guessing that every call
    constructs an Actor. No student code is imported or executed.
    """
    tree = ast.parse(code)
    types = {}
    modules = set()
    exports = {
        "Actor": "Actor",
        "World": "World",
        "TiledWorld": "World",
        "HexWorld": "World",
        "Circle": "Actor",
        "Rectangle": "Actor",
        "Text": "Actor",
        "Number": "Actor",
        "Ellipse": "Actor",
        "Line": "Actor",
        "Point": "Actor",
        "Polygon": "Actor",
        "Triangle": "Actor",
        "Arc": "Actor",
    }
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "miniworlds":
            for alias in node.names:
                if alias.name == "*":
                    types.update(exports)
                elif alias.name in exports:
                    types[alias.asname or alias.name] = exports[alias.name]
        elif isinstance(node, ast.Import):
            modules.update(
                a.asname or a.name for a in node.names if a.name == "miniworlds"
            )

    def kind(node):
        name = _dotted(node)
        if name in types:
            return types[name]
        prefix, _, member = name.rpartition(".")
        if prefix in modules:
            return exports.get(member)
        return None

    classes = {}
    pending = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    for _ in range(len(pending) + 1):
        for node in pending:
            resolved = next((kind(base) for base in node.bases if kind(base)), None)
            if resolved:
                classes[node.name] = Target(node.name, resolved, node.lineno)
                types[node.name] = resolved
    objects = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            value, targets = node.value, node.targets
        elif isinstance(node, ast.AnnAssign):
            value, targets = node.value, [node.target]
        else:
            continue
        resolved = kind(value.func) if isinstance(value, ast.Call) else None
        for target in targets:
            if isinstance(target, ast.Name):
                if resolved:
                    objects[target.id] = Target(target.id, resolved, node.lineno)
                else:
                    objects.pop(target.id, None)
    return tree, classes, objects


def targets_for(code, mode):
    _, classes, objects = analyze(code)
    return classes if mode == "Q1" else objects


def events_for(kind):
    return [name for name in EVENTS if kind == "Actor" or name not in ACTOR_ONLY]


@dataclass(frozen=True)
class CodeEdit:
    start: int
    end: int
    replacement: str
    line: int
    existing: bool = False

    def apply(self, code):
        result = code[: self.start] + self.replacement + code[self.end :]
        ast.parse(result)
        return result


def event_edit(code, mode, target, event):
    tree, classes, objects = analyze(code)
    targets = classes if mode == "Q1" else objects
    if target not in targets:
        raise ValueError(
            "Das Ziel ist nicht eindeutig als miniworlds-Actor oder -World erkennbar. Bitte Importe und Vererbung prüfen."
        )
    if event not in events_for(targets[target].kind):
        raise ValueError("Dieses Ereignis gehört zu einem Actor.")
    lines = code.splitlines(keepends=True)
    if mode == "Q1":
        cls = next(
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == target
        )
        existing = next(
            (
                n
                for n in cls.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name == event
            ),
            None,
        )
        if existing:
            return CodeEdit(0, 0, "", existing.lineno, True)
        if cls.body[0].lineno == cls.lineno:
            raise ValueError(
                "Bitte den Klassenrumpf zuerst auf eigene, eingerückte Zeilen verteilen."
            )
        first_line = lines[cls.body[0].lineno - 1]
        indent = first_line[: len(first_line) - len(first_line.lstrip())]
        unit = "\t" if "\t" in indent else " " * len(indent)
        snippet = event_code("Q1", target, event)
        snippet = (
            "\n".join(
                indent + line[4:].replace("    ", unit, 1) if line else ""
                for line in snippet.splitlines()
            )
            + "\n"
        )
        offset = sum(len(line) for line in lines[: cls.end_lineno])
        prefix = "\n" if offset and code[offset - 1] == "\n" else "\n\n"
        edit = CodeEdit(
            offset,
            offset,
            prefix + snippet,
            code[:offset].count("\n") + prefix.count("\n") + 1,
            False,
        )
    else:
        for node in tree.body:
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == event
                and any(_dotted(d) == f"{target}.register" for d in node.decorator_list)
            ):
                return CodeEdit(0, 0, "", node.lineno, True)
        run = next(
            (
                n
                for n in tree.body
                if isinstance(n, ast.Expr)
                and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Attribute)
                and n.value.func.attr == "run"
            ),
            None,
        )
        if run and run.lineno <= targets[target].line:
            raise ValueError(
                "Das Zielobjekt wird erst nach .run() erzeugt. Bitte zuerst die Reihenfolge korrigieren."
            )
        offset = (
            sum(len(line) for line in lines[: run.lineno - 1]) if run else len(code)
        )
        prefix = "" if not offset or code[offset - 1] == "\n" else "\n"
        snippet = prefix + "\n" + event_code(mode, target, event) + "\n"
        edit = CodeEdit(
            offset, offset, snippet, (run.lineno if run else len(lines) + 1) + 2
        )
    edit.apply(code)
    return edit


@dataclass(frozen=True)
class Example:
    name: str
    topic: str
    level: str
    behavior: str
    task: str
    hint: str


EXAMPLES = {
    "Grundgerüst": Example(
        "Grundgerüst",
        "Einstieg",
        "Einstieg",
        "Eine blaue Figur erscheint auf hellem Hintergrund.",
        "Verändere Position und Farbe der Figur.",
        "Die Position besteht aus x und y; Farben aus Rot, Grün und Blau.",
    ),
    "Bewegung": Example(
        "Bewegung",
        "Bewegung",
        "Einstieg",
        "Die Figur bewegt sich in jedem Frame in ihre Richtung.",
        "Verdopple die Geschwindigkeit. Was passiert bei einem negativen Wert?",
        "Suche den Aufruf move im Ereignis act.",
    ),
    "Tastatur": Example(
        "Tastatur",
        "Eingabe",
        "Einstieg",
        "Die Figur bewegt sich nach rechts, solange die rechte Pfeiltaste gehalten wird.",
        "Ergänze Bewegung nach links.",
        "Verwende on_key_pressed_left und verringere x.",
    ),
    "Maus": Example(
        "Maus",
        "Eingabe",
        "Fortgeschritten",
        "Bei einem linken Mausklick springt die Figur zur Klickposition.",
        "Lass die Figur nur dann springen, wenn sie selbst angeklickt wird.",
        "Vergleiche on_mouse_left mit on_clicked_left.",
    ),
}


def filter_examples(topic="Alle", level="Alle"):
    return [
        e.name
        for e in EXAMPLES.values()
        if (topic == "Alle" or e.topic == topic)
        and (level == "Alle" or e.level == level)
    ]


HELP_DETAILS = {
    "move": (
        "distance: Anzahl Schritte (Zahl); bei 0 wird die Geschwindigkeit speed verwendet. Optional direction.",
        "Der Actor selbst (Methodenverkettung möglich).",
        "Bewegung folgt direction; sie ist nicht automatisch nach rechts gerichtet.",
    ),
    "add_costume": (
        "source: Bildpfad oder Farbe als RGB/RGBA-Tupel.",
        "Das hinzugefügte Costume.",
        "Dateiname, Groß-/Kleinschreibung und Projektordner prüfen.",
    ),
    "add_background": (
        "source: Bildpfad oder Farbe als RGB/RGBA-Tupel.",
        "Der hinzugefügte Background.",
        "Diese Methode gehört zur World, nicht zum Actor.",
    ),
    "play_sound": (
        "path: Soundpfad; volume: 0 bis 100 (Standard 100).",
        "Kein Rückgabewert (None).",
        "Die Datei muss existieren; das Audioformat muss unterstützt werden.",
    ),
    "run": (
        "Optional fullscreen und fit_desktop als bool.",
        "Kein Rückgabewert (None).",
        "Die Einrichtung steht vor run; der Aufruf startet die Ereignisschleife.",
    ),
    "World": (
        "width und height: positive Pixelmaße.",
        "Eine neue World-Instanz.",
        "Die Welt vor ihren Actors erzeugen.",
    ),
    "TiledWorld": (
        "columns und rows: Anzahl Kacheln.",
        "Eine neue TiledWorld-Instanz.",
        "Keine Pixelmaße als Kachelanzahl verwenden.",
    ),
    "Actor": (
        "position: Koordinatenpaar (x, y).",
        "Eine neue Actor-Instanz.",
        "Ein Actor braucht eine bereits erzeugte Welt.",
    ),
    "register": (
        "Eine Ereignisfunktion; der erste Parameter heißt self.",
        "Die registrierte Methode.",
        "In Q1 werden Ereignisse als Methoden überschrieben; dort entfällt der Dekorator.",
    ),
}


def learning_help(topic, mode, kind=None, stage=0):
    """Explanation, hint and example are progressively revealed."""
    if topic in EVENTS:
        parameters, description = EVENTS[topic]
        text = (
            description
            + "\n\nParameter: "
            + ", ".join(("self",) + parameters)
            + ".\nRückgabe: None."
        )
        if kind == "World" and topic in ACTOR_ONLY:
            text += "\nDieses Ereignis gehört zu einem Actor, nicht zu einer World."
        hint = "self bezeichnet " + (
            "das Objekt, an dem die Funktion registriert ist."
            if mode == "E2"
            else "die aktuelle Instanz der Klasse. Die Methode überschreibt das Ereignis der Basisklasse."
        )
        example = event_code(mode, "player" if kind != "World" else "world", topic)
    else:
        description, objects, classes = TOPICS.get(topic, TOPICS["World"])
        parameters, result, hint = HELP_DETAILS.get(topic, HELP_DETAILS["World"])
        text = description + f"\n\nParameter: {parameters}\nRückgabe: {result}"
        example = objects if mode == "E2" else classes
        if topic == "play_sound" and mode == "Q1" and kind == "World":
            example = 'self.play_sound("sounds/click.wav")'
        if topic == "add_background" and mode == "Q1" and kind == "Actor":
            example = 'self.world.add_background("images/background.png")'
        owners = {
            "move": "Actor",
            "add_costume": "Actor",
            "add_background": "World",
            "run": "World",
        }
        if kind and topic in owners and kind != owners[topic]:
            text += (
                f"\nDiese Methode gehört zu {owners[topic]}; erkanntes Ziel: {kind}."
            )
    text = MODES[mode] + (f" · {kind}" if kind else "") + "\n\n" + text
    if stage >= 1:
        text += "\n\nHinweis: " + hint
    if stage >= 2:
        text += "\n\nBeispiel:\n" + example
    return text


def contextual_topic(code, line, column):
    """Return topic and receiver kind at a cursor without running code."""
    import re

    lines = code.splitlines()
    text = lines[line - 1] if 0 < line <= len(lines) else ""
    match = next(
        (m for m in re.finditer(r"\w+", text) if m.start() <= column <= m.end()), None
    )
    if match is None:
        return "", None
    word = match.group()
    tree, classes, objects = analyze(code)
    before = text[: match.start()]
    receiver = re.search(r"([\w.]+)\.$", before)
    kind = None
    if receiver:
        name = receiver.group(1)
        if name in objects:
            kind = objects[name].kind
        elif name in classes:
            kind = classes[name].kind
        elif name in {"self", "self.world"}:
            cls = next(
                (
                    n
                    for n in tree.body
                    if isinstance(n, ast.ClassDef) and n.lineno <= line <= n.end_lineno
                ),
                None,
            )
            if cls and cls.name in classes:
                kind = "World" if name == "self.world" else classes[cls.name].kind
    if word in classes:
        return classes[word].kind, classes[word].kind
    if word in objects:
        return objects[word].kind, objects[word].kind
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "miniworlds":
            for alias in node.names:
                if (alias.asname or alias.name) == word and alias.name in TOPICS:
                    word = alias.name
    return word, kind


def media_call(relative, purpose, target):
    import json

    if purpose not in {"Kostüm", "Hintergrund", "Sound"}:
        raise ValueError("Unbekannter Medienaufruf")
    # Accept only attribute/name expressions, never arbitrary code.
    expression = ast.parse(target, mode="eval").body
    if not _dotted(expression) or any(
        keyword.iskeyword(p) for p in _dotted(expression).split(".")
    ):
        raise ValueError("Bitte ein Objekt oder self.world angeben.")
    method = {
        "Kostüm": "add_costume",
        "Hintergrund": "add_background",
        "Sound": "play_sound",
    }[purpose]
    return f"{target}.{method}({json.dumps(relative, ensure_ascii=False)})"


def signature_fix(code, node):
    """Offer a signature change only when it can preserve existing names."""
    if (
        node.args.vararg
        or node.args.kwarg
        or node.args.kwonlyargs
        or node.args.defaults
        or node.args.posonlyargs
    ):
        return None
    names = [arg.arg for arg in node.args.args]
    expected = ["self", *EVENTS[node.name][0]]
    if "self" in names and (not names or names[0] != "self"):
        return None
    if not names or names[0] != "self":
        names.insert(0, "self")
    if len(names) > len(expected):
        return None
    while len(names) < len(expected):
        candidate = expected[len(names)]
        if candidate in names:
            return None
        names.append(candidate)
    import re

    lines = code.splitlines(keepends=True)
    start = sum(len(line) for line in lines[: node.lineno - 1])
    line = lines[node.lineno - 1]
    # Multiline/annotated definitions remain explanatory-only.
    match = re.match(r"(\s*(?:async\s+)?def\s+\w+\s*)\([^\n:]*\)(\s*):", line)
    if not match:
        return None
    replacement = match.group(1) + "(" + ", ".join(names) + ")" + match.group(2) + ":"
    return CodeEdit(start, start + match.end(), replacement, node.lineno)


def teaching_project_code(mode, kind="Pixelwelt", example="Grundgerüst"):
    item = EXAMPLES[example]
    introduction = (
        f"# {MODES[mode]}\n# Beobachtung: {item.behavior}\n# Aufgabe: {item.task}\n"
    )
    if mode == "E2":
        introduction += "# Ein Objekt besitzt Zustand (z. B. position) und Methoden (z. B. move).\n# @objekt.register verbindet die Ereignisfunktion mit diesem Objekt.\n"
    else:
        introduction += "# Player erbt von Actor. self bezeichnet die aktuelle Instanz.\n# Ereignismethoden überschreiben das Verhalten der Basisklasse.\n"
    return introduction + "\n" + project_code(mode, kind, example)
